import hashlib
from collections import OrderedDict

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError

from .merchant import is_manager


PREPARATION_STATES = [
    ('received', 'Recibido'), ('preparing', 'En preparación'), ('ready', 'Listo para retirar'),
    ('collected', 'Retirado por el repartidor'), ('delivered', 'Entregado'), ('cancelled', 'Cancelado'),
]


class Preparation(models.Model):
    _name = 'wah.preparation'
    _description = 'Preparación de pedido por comercio'
    _order = 'placed_at desc, id desc'

    name = fields.Char(string='Preparación', required=True, readonly=True)
    reference = fields.Char(string='Pedido', required=True, readonly=True)
    order_id = fields.Many2one('sale.order', string='Pedido completo', required=True,
                               readonly=True, groups='product.group_product_manager', ondelete='restrict')
    merchant_id = fields.Many2one('wah.merchant', string='Comercio registrado', readonly=True, ondelete='restrict')
    store_name = fields.Char(string='Local', required=True, readonly=True)
    store_key = fields.Char(required=True, readonly=True, groups='product.group_product_manager')
    website_id = fields.Many2one('website', readonly=True, required=True)
    placed_at = fields.Datetime(string='Fecha del pedido', readonly=True, required=True)
    currency_id = fields.Many2one('res.currency', readonly=True, required=True)
    state = fields.Selection(PREPARATION_STATES, default='received', required=True, readonly=True)
    line_ids = fields.One2many('wah.preparation.line', 'preparation_id', string='Productos', readonly=True)
    amount_total = fields.Monetary(string='Subtotal de este local', compute='_compute_amount')
    merchant_note = fields.Text(string='Observación del comercio', readonly=True)
    started_at = fields.Datetime(string='Inicio de preparación', readonly=True)
    ready_at = fields.Datetime(string='Listo para retirar', readonly=True)
    collected_at = fields.Datetime(string='Retirado', readonly=True)
    delivered_at = fields.Datetime(string='Entregado', readonly=True)
    _one_per_store = models.Constraint('UNIQUE(order_id, store_key)', 'Ya existe una preparación para este local en el pedido.')

    @api.depends('line_ids.amount_total')
    def _compute_amount(self):
        for preparation in self:
            preparation.amount_total = sum(preparation.line_ids.mapped('amount_total'))

    def write(self, vals):
        if not self.env.su:
            raise AccessError('Usá los botones de preparación para actualizar el pedido.')
        return super().write(vals)

    def _transition(self, target, source, timestamp, manager_only=False):
        self.check_access('write')
        manager = is_manager(self.env)
        if manager_only and not manager:
            raise AccessError('El retiro y la entrega los registra la administración.')
        if not manager and any(record.merchant_id.owner_id.id != self.env.uid for record in self):
            raise AccessError('Solo podés actualizar las preparaciones de tu comercio.')
        if not self:
            return True
        self.env.cr.execute('SELECT id FROM wah_preparation WHERE id IN %s FOR UPDATE', (tuple(self.ids),))
        self.invalidate_recordset(['state'])
        for preparation in self:
            if preparation.sudo().order_id.state != 'sale':
                raise ValidationError('El pedido no está confirmado o fue cancelado.')
            if preparation.state == target:
                continue
            if preparation.state != source:
                raise ValidationError('Este pedido cambió de estado. Actualizá la pantalla y revisalo.')
            preparation.sudo().write({'state': target, timestamp: fields.Datetime.now()})
        return True

    def action_start(self):
        return self._transition('preparing', 'received', 'started_at')

    def action_ready(self):
        return self._transition('ready', 'preparing', 'ready_at')

    def action_collect(self):
        return self._transition('collected', 'ready', 'collected_at', manager_only=True)

    def action_deliver(self):
        return self._transition('delivered', 'collected', 'delivered_at', manager_only=True)

    def action_save_note(self, note):
        self.check_access('write')
        if not is_manager(self.env) and any(record.merchant_id.owner_id.id != self.env.uid for record in self):
            raise AccessError('La preparación no pertenece a tu comercio.')
        if not isinstance(note, str) or len(note) > 1000:
            raise ValidationError('La observación puede tener hasta 1000 caracteres.')
        if any(record.state in ('cancelled', 'delivered') for record in self):
            raise ValidationError('El pedido ya está cerrado.')
        return self.sudo().write({'merchant_note': note.strip()})


class PreparationLine(models.Model):
    _name = 'wah.preparation.line'
    _description = 'Producto para preparar en un local'
    _order = 'id'

    preparation_id = fields.Many2one('wah.preparation', required=True, readonly=True, ondelete='cascade')
    name = fields.Char(string='Producto / presentación', required=True, readonly=True)
    quantity = fields.Float(string='Cantidad', digits='Product Unit of Measure', readonly=True)
    uom_name = fields.Char(string='Unidad', readonly=True)
    currency_id = fields.Many2one(related='preparation_id.currency_id', readonly=True)
    amount_total = fields.Monetary(string='Subtotal con impuestos', readonly=True)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    wah_merchant_id = fields.Many2one('wah.merchant', string='Comercio al comprar', readonly=True,
                                     copy=False, groups='product.group_product_manager', ondelete='restrict')
    wah_store_partner_id = fields.Many2one('res.partner', readonly=True, copy=False,
                                          groups='product.group_product_manager', ondelete='restrict')

    def _capture_wah_merchant(self):
        for line in self.sudo():
            partner = line.product_id.wah_store_id
            merchant = self.env['wah.merchant'].sudo().search([
                ('partner_id', '=', partner.id), ('website_id', '=', line.order_id.website_id.id)], limit=1) if partner else False
            line.write({'wah_store_partner_id': partner.id or False, 'wah_merchant_id': merchant.id if merchant else False})

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            order = self.env['sale.order'].browse(values.get('order_id')).sudo()
            if order.state == 'sale' and order.wah_preparation_ids and not values.get('is_delivery') and not values.get('display_type'):
                raise ValidationError('El pedido ya fue enviado a preparación. Cancelalo y creá otro para cambiar sus productos.')
        lines = super().create(vals_list)
        lines._capture_wah_merchant()
        return lines

    def _check_wah_changes(self):
        if any(line.order_id.state == 'sale' and line.order_id.sudo().wah_preparation_ids
               for line in self.filtered(lambda line: not line.is_delivery and not line.display_type)):
            raise ValidationError('El pedido ya fue enviado a preparación. Cancelalo y creá otro para cambiar sus productos.')

    def write(self, values):
        if {'product_id', 'product_uom_qty', 'product_uom_id', 'price_unit', 'discount', 'tax_ids', 'name'} & values.keys():
            self._check_wah_changes()
        result = super().write(values)
        if 'product_id' in values:
            self.filtered(lambda line: line.order_id.state in ('draft', 'sent'))._capture_wah_merchant()
        return result

    def unlink(self):
        self._check_wah_changes()
        return super().unlink()


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    wah_preparation_ids = fields.One2many('wah.preparation', 'order_id', string='Preparaciones',
                                         readonly=True, groups='product.group_product_manager')
    wah_preparation_state = fields.Selection(PREPARATION_STATES + [('not_sent', 'Pedido recibido')],
                                            string='Estado de preparación', compute='_compute_wah_preparation_state', compute_sudo=True)
    wah_unassigned_count = fields.Integer(string='Locales sin dueño asignado', compute='_compute_wah_unassigned', groups='product.group_product_manager')

    @api.depends('wah_preparation_ids.state')
    def _compute_wah_preparation_state(self):
        for order in self:
            states = order.wah_preparation_ids.mapped('state')
            active = [state for state in states if state != 'cancelled']
            if not states:
                value = 'not_sent'
            elif not active:
                value = 'cancelled'
            elif all(state == 'delivered' for state in active):
                value = 'delivered'
            elif all(state in ('collected', 'delivered') for state in active):
                value = 'collected'
            elif all(state in ('ready', 'collected', 'delivered') for state in active):
                value = 'ready'
            elif any(state != 'received' for state in active):
                value = 'preparing'
            else:
                value = 'received'
            order.wah_preparation_state = value

    @api.depends('wah_preparation_ids.merchant_id')
    def _compute_wah_unassigned(self):
        for order in self:
            order.wah_unassigned_count = len(order.wah_preparation_ids.filtered(lambda record: not record.merchant_id))

    def _ensure_wah_preparations(self):
        for order in self.sudo().filtered(lambda record: record.website_id and record.state == 'sale'):
            # Bloquea la orden para hacer idempotente la distribución simultánea.
            self.env.cr.execute('SELECT id FROM sale_order WHERE id=%s FOR UPDATE', (order.id,))
            order.invalidate_recordset(['wah_preparation_ids'])
            if order.wah_preparation_ids:
                continue
            groups = OrderedDict()
            for line in order.order_line.filtered(lambda record: not record.display_type and not record.is_delivery and record.product_id):
                if line.product_uom_qty <= 0:
                    continue
                partner = line.wah_store_partner_id
                merchant = line.wah_merchant_id
                label = line.wah_store_name or 'Comercio sin asignar'
                key = 'merchant-%s' % merchant.id if merchant else ('partner-%s' % partner.id if partner else 'unknown-' + hashlib.sha256(label.encode()).hexdigest()[:24])
                group = groups.setdefault(key, {'merchant': merchant, 'label': label, 'lines': []})
                group['lines'].append((0, 0, {'name': line.name, 'quantity': line.product_uom_qty,
                                             'uom_name': line.product_uom_id.name, 'amount_total': line.price_total}))
            for key, group in groups.items():
                self.env['wah.preparation'].sudo().create({
                    'name': '%s · %s' % (order.name, group['label']), 'reference': order.name,
                    'order_id': order.id, 'merchant_id': group['merchant'].id or False,
                    'store_name': group['label'], 'store_key': key, 'website_id': order.website_id.id,
                    'placed_at': order.date_order or fields.Datetime.now(), 'currency_id': order.currency_id.id,
                    'line_ids': group['lines'],
                })
        return True

    def action_confirm(self):
        result = super().action_confirm()
        self._ensure_wah_preparations()
        return result

    def _action_cancel(self):
        result = super()._action_cancel()
        preparations = self.env['wah.preparation'].sudo().search([
            ('order_id', 'in', self.ids), ('state', 'not in', ['delivered', 'cancelled'])])
        preparations.write({'state': 'cancelled'})
        return result

    def action_wah_generate_preparations(self):
        if not is_manager(self.env):
            raise AccessError('Esta operación corresponde a la administración.')
        self.check_access('write')
        return self._ensure_wah_preparations()
