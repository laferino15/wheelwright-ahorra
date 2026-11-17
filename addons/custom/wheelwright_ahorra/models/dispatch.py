"""Reparto consolidado y registro operativo de cobros, sin asientos contables."""
import math

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError

from .merchant import is_manager

ROUTE_STATES = [('pending', 'Pendiente de reparto'), ('assigned', 'Repartidor asignado'),
                ('on_way', 'En camino'), ('delivered', 'Entregado'), ('cancelled', 'Cancelado')]


class Courier(models.Model):
    _name = 'wah.courier'
    _description = 'Repartidor de wheel-ahorra'
    _order = 'name'

    name = fields.Char(string='Nombre', required=True)
    phone = fields.Char(string='Teléfono', required=True)
    active = fields.Boolean(default=True)

    @api.constrains('name', 'phone')
    def _check_details(self):
        if any(not (courier.name or '').strip() or not (courier.phone or '').strip() for courier in self):
            raise ValidationError('Completá el nombre y el teléfono del repartidor.')


class RouteEvent(models.Model):
    _name = 'wah.route.event'
    _description = 'Historial de reparto y cobro'
    _order = 'occurred_at desc, id desc'

    order_id = fields.Many2one('sale.order', required=True, ondelete='restrict', readonly=True)
    occurred_at = fields.Datetime(string='Fecha y hora', required=True, readonly=True)
    actor_id = fields.Many2one('res.users', string='Registrado por', required=True, readonly=True, ondelete='restrict')
    description = fields.Char(string='Movimiento', required=True, readonly=True)

    @api.model_create_multi
    def create(self, values):
        if not self.env.su:
            raise AccessError('El historial se genera desde las acciones del pedido.')
        return super().create(values)

    def write(self, values):
        raise AccessError('Los movimientos del historial no se pueden modificar.')

    def unlink(self):
        if not self.env.su:
            raise AccessError('Los movimientos del historial no se pueden eliminar.')
        return super().unlink()


class Collection(models.Model):
    _name = 'wah.collection'
    _description = 'Registro operativo de cobro'
    _order = 'collected_at desc, id desc'

    name = fields.Char(string='Número de registro', required=True, readonly=True)
    order_id = fields.Many2one('sale.order', string='Pedido', required=True, readonly=True, ondelete='restrict')
    currency_id = fields.Many2one('res.currency', required=True, readonly=True)
    amount = fields.Monetary(string='Importe cobrado', required=True, readonly=True)
    method = fields.Selection([('cash', 'Efectivo'), ('transfer', 'Transferencia verificada')], string='Medio de cobro', required=True, readonly=True)
    received_amount = fields.Monetary(string='Efectivo recibido', readonly=True)
    change_amount = fields.Monetary(string='Vuelto entregado', readonly=True)
    reference = fields.Char(string='Referencia / comprobante', readonly=True)
    courier_id = fields.Many2one('wah.courier', string='Repartidor', readonly=True, ondelete='restrict')
    collected_at = fields.Datetime(string='Registrado el', required=True, readonly=True)
    actor_id = fields.Many2one('res.users', string='Registrado por', required=True, readonly=True, ondelete='restrict')
    state = fields.Selection([('posted', 'Registrado'), ('void', 'Anulado')], default='posted', required=True, readonly=True)
    void_reason = fields.Text(string='Motivo de anulación', readonly=True)
    voided_at = fields.Datetime(string='Anulado el', readonly=True)
    voided_by = fields.Many2one('res.users', string='Anulado por', readonly=True, ondelete='restrict')

    @api.model_create_multi
    def create(self, values):
        if not self.env.su:
            raise AccessError('Registrá el cobro desde el pedido de reparto.')
        return super().create(values)

    def write(self, values):
        if not self.env.su or set(values) - {'state', 'void_reason', 'voided_at', 'voided_by'}:
            raise AccessError('El registro es inalterable. Para corregirlo, anulalo con un motivo.')
        return super().write(values)

    def unlink(self):
        if not self.env.su:
            raise AccessError('Los cobros se anulan; no se eliminan.')
        return super().unlink()

    def action_void_wizard(self):
        self.ensure_one()
        self.order_id._wah_lock_dispatch()
        return {'type': 'ir.actions.act_window', 'name': 'Anular registro de cobro', 'res_model': 'wah.collection.void',
                'view_mode': 'form', 'target': 'new', 'context': {'default_collection_id': self.id}}

    def _void(self, reason):
        self.ensure_one()
        self.order_id._wah_lock_dispatch()
        self.invalidate_recordset(['state'])
        if self.state != 'posted':
            raise ValidationError('Este registro ya fue anulado.')
        if not isinstance(reason, str) or not 3 <= len(reason.strip()) <= 1000:
            raise ValidationError('Indicá un motivo de anulación de entre 3 y 1000 caracteres.')
        self.sudo().write({'state': 'void', 'void_reason': reason.strip(), 'voided_at': fields.Datetime.now(), 'voided_by': self.env.uid})
        self.order_id._wah_dispatch_event('Cobro %s anulado. Motivo: %s' % (self.name, reason.strip()))


class DispatchOrder(models.Model):
    _inherit = 'sale.order'

    wah_courier_id = fields.Many2one('wah.courier', string='Repartidor asignado', copy=False, ondelete='restrict', groups='product.group_product_manager')
    wah_route_state = fields.Selection(ROUTE_STATES, string='Estado de reparto', default='pending', readonly=True, copy=False, index=True)
    wah_departed_at = fields.Datetime(string='Salida a reparto', readonly=True, copy=False, groups='product.group_product_manager')
    wah_delivered_at = fields.Datetime(string='Entrega registrada', readonly=True, copy=False)
    wah_dropoff_details = fields.Text(string='Destino al salir a reparto', readonly=True, copy=False, groups='product.group_product_manager')
    wah_route_event_ids = fields.One2many('wah.route.event', 'order_id', string='Historial', readonly=True, groups='product.group_product_manager')
    wah_collection_ids = fields.One2many('wah.collection', 'order_id', string='Cobros registrados', readonly=True, groups='product.group_product_manager')
    wah_collection_state = fields.Selection([('pending', 'Pendiente de cobro'), ('collected', 'Cobro registrado'), ('not_required', 'Sin importe a cobrar')],
        string='Cobro del reparto', compute='_compute_wah_collection', compute_sudo=True, store=True)
    wah_collection_amount = fields.Monetary(string='Cobro registrado', compute='_compute_wah_collection', compute_sudo=True, store=True, groups='product.group_product_manager')
    wah_preparation_state = fields.Selection(selection_add=[('on_way', 'En camino')])

    @api.depends('amount_total', 'currency_id', 'state', 'wah_collection_ids.state', 'wah_collection_ids.amount')
    def _compute_wah_collection(self):
        for order in self:
            total = sum(order.wah_collection_ids.filtered(lambda receipt: receipt.state == 'posted').mapped('amount'))
            order.wah_collection_amount = total
            order.wah_collection_state = 'not_required' if order.state == 'cancel' or order.currency_id.is_zero(order.amount_total) else ('collected' if total and not order.currency_id.compare_amounts(total, order.amount_total) else 'pending')

    @api.depends('wah_preparation_ids.state', 'wah_route_state')
    def _compute_wah_preparation_state(self):
        super()._compute_wah_preparation_state()
        for order in self:
            if order.wah_route_state == 'on_way':
                order.wah_preparation_state = 'on_way'

    def write(self, values):
        protected = {'wah_route_state', 'wah_departed_at', 'wah_delivered_at', 'wah_dropoff_details'}
        if not self.env.su and protected & values.keys():
            raise AccessError('Usá las acciones del panel de reparto para cambiar el estado.')
        if 'wah_courier_id' in values:
            self._wah_lock_dispatch(require_sale=False)
            if any(order.wah_route_state in ('on_way', 'delivered', 'cancelled') for order in self):
                raise ValidationError('No se puede cambiar el repartidor después de salir a reparto.')
            if not values['wah_courier_id'] and any(order.wah_route_state == 'assigned' for order in self):
                raise ValidationError('Elegí otro repartidor antes de guardar.')
        if {'wah_delivery_date', 'wah_delivery_window', 'wah_delivery_notes', 'partner_shipping_id', 'pricelist_id', 'fiscal_position_id', 'carrier_id'} & values.keys():
            if any(order.wah_route_state in ('on_way', 'delivered') for order in self):
                raise ValidationError('El pedido ya salió a reparto. No se pueden cambiar destino, horario ni condiciones comerciales.')
        previous = {order.id: order.wah_courier_id.id for order in self.sudo()} if 'wah_courier_id' in values else {}
        result = super().write(values)
        for order in self:
            if order.id in previous and previous[order.id] != order.sudo().wah_courier_id.id and order.wah_route_state == 'assigned':
                order._wah_dispatch_event('Repartidor cambiado a %s.' % order.sudo().wah_courier_id.name)
        return result

    def _wah_lock_dispatch(self, require_sale=True):
        if not is_manager(self.env):
            raise AccessError('El reparto y los cobros los gestiona la administración.')
        self.check_access('write')
        if self:
            self.env.cr.execute('SELECT id FROM sale_order WHERE id IN %s ORDER BY id FOR UPDATE', (tuple(sorted(self.ids)),))
            self.invalidate_recordset(['state', 'wah_route_state', 'wah_courier_id', 'wah_collection_ids'])
        if require_sale and any(not order.website_id or order.state != 'sale' for order in self):
            raise ValidationError('El pedido debe estar confirmado y pertenecer a la tienda.')

    def _wah_dispatch_event(self, text):
        self.ensure_one()
        self.env['wah.route.event'].sudo().create({'order_id': self.id, 'occurred_at': fields.Datetime.now(), 'actor_id': self.env.uid, 'description': text})

    def action_wah_assign(self):
        self._wah_lock_dispatch()
        for order in self:
            if order.wah_route_state not in ('pending', 'assigned'):
                raise ValidationError('El pedido ya salió a reparto o está cerrado.')
            if not order.wah_courier_id or not order.wah_courier_id.active:
                raise ValidationError('Asigná un repartidor activo.')
            if not order.wah_preparation_ids:
                raise ValidationError('Primero generá las preparaciones del pedido.')
            if order.wah_route_state == 'pending':
                order.sudo().write({'wah_route_state': 'assigned'})
                order._wah_dispatch_event('Pedido asignado a %s.' % order.wah_courier_id.name)
        return True

    def action_wah_open_dispatch(self):
        self.ensure_one()
        self._wah_lock_dispatch(require_sale=False)
        return {'type': 'ir.actions.act_window', 'name': 'Reparto y cobros', 'res_model': 'sale.order',
                'res_id': self.id, 'views': [(self.env.ref('wheelwright_ahorra.dispatch_form').id, 'form')], 'target': 'current'}

    def action_wah_dispatch(self):
        self._wah_lock_dispatch()
        for order in self:
            if order.wah_route_state == 'on_way':
                continue
            if order.wah_route_state != 'assigned' or not order.wah_courier_id.active:
                raise ValidationError('Asigná un repartidor activo antes de salir.')
            preparations = order.wah_preparation_ids
            preparations.invalidate_recordset(['state'])
            if not preparations or any(prep.state != 'collected' for prep in preparations):
                raise ValidationError('Falta registrar el retiro de uno o más locales.')
            partner = order.partner_shipping_id
            details = '\n'.join(filter(None, [partner.name, partner.phone, partner._display_address(), order.wah_delivery_notes]))
            order.sudo().write({'wah_route_state': 'on_way', 'wah_departed_at': fields.Datetime.now(), 'wah_dropoff_details': details})
            order._wah_dispatch_event('Salida a reparto con %s. Todos los locales retirados.' % order.wah_courier_id.name)
        return True

    def action_wah_deliver(self):
        self._wah_lock_dispatch()
        with self.env.cr.savepoint():
            for order in self:
                if order.wah_route_state == 'delivered':
                    continue
                if order.wah_route_state != 'on_way':
                    raise ValidationError('Primero registrá la salida a reparto.')
                preparations = order.wah_preparation_ids
                preparations._transition('delivered', 'collected', 'delivered_at', manager_only=True)
                order.sudo().write({'wah_route_state': 'delivered', 'wah_delivered_at': fields.Datetime.now()})
                order._wah_dispatch_event('Entrega registrada. El cobro se registra por separado.')
        return True

    def action_wah_collection_wizard(self):
        self.ensure_one()
        self._wah_lock_dispatch()
        if self.wah_route_state != 'delivered':
            raise ValidationError('Registrá la entrega antes de cargar el cobro.')
        if self.wah_collection_state != 'pending':
            raise ValidationError('Este pedido no tiene un cobro pendiente.')
        return {'type': 'ir.actions.act_window', 'name': 'Registrar cobro del reparto', 'res_model': 'wah.collection.register',
                'view_mode': 'form', 'target': 'new', 'context': {'default_order_id': self.id}}

    def _wah_register_collection(self, method, amount, received, reference):
        self.ensure_one()
        self._wah_lock_dispatch()
        if self.wah_route_state != 'delivered':
            raise ValidationError('El cobro del reparto requiere una entrega registrada.')
        existing = self.env['wah.collection'].sudo().search([('order_id', '=', self.id), ('state', '=', 'posted')], limit=1)
        if existing:
            raise ValidationError('El pedido ya tiene un cobro registrado: %s.' % existing.name)
        if method not in ('cash', 'transfer') or not isinstance(reference, str) or len(reference) > 200:
            raise ValidationError('Revisá el medio de cobro y la referencia.')
        if not all(math.isfinite(value) for value in (amount, received)) or amount <= 0 or self.currency_id.compare_amounts(amount, self.amount_total):
            raise ValidationError('El importe debe coincidir con el total completo del pedido.')
        amount = self.currency_id.round(amount)
        received = self.currency_id.round(received)
        if self.sudo().amount_paid:
            raise ValidationError('El pedido ya registra un pago en Odoo. Revisalo antes de cargar otro cobro.')
        if self.sudo().transaction_ids.filtered(lambda tx: tx.state in ('draft', 'pending', 'authorized') and not (tx.provider_code == 'custom' and tx.provider_id.custom_mode == 'cash_on_delivery')):
            raise ValidationError('Hay un pago electrónico en proceso. Verificalo antes de cargar un cobro de reparto.')
        if method == 'cash' and self.currency_id.compare_amounts(received, amount) < 0:
            raise ValidationError('El efectivo recibido debe alcanzar el total.')
        if method == 'transfer' and not reference.strip():
            raise ValidationError('Ingresá la referencia de la transferencia que verificaste.')
        receipt = self.env['wah.collection'].sudo().create({
            'name': self.env['ir.sequence'].sudo().next_by_code('wah.collection'), 'order_id': self.id,
            'currency_id': self.currency_id.id, 'amount': amount, 'method': method,
            'received_amount': received if method == 'cash' else 0,
            'change_amount': self.currency_id.round(received - amount) if method == 'cash' else 0,
            'reference': reference.strip(), 'courier_id': self.wah_courier_id.id,
            'collected_at': fields.Datetime.now(), 'actor_id': self.env.uid,
        })
        self._wah_dispatch_event('Cobro %s registrado por %s: %s %s.' % (receipt.name, dict(receipt._fields['method'].selection)[method], amount, self.currency_id.name))
        return receipt

    def _action_cancel(self):
        self.check_access('write')
        if self:
            self.env.cr.execute('SELECT id FROM sale_order WHERE id IN %s ORDER BY id FOR UPDATE', (tuple(sorted(self.ids)),))
            self.invalidate_recordset(['wah_route_state'])
            self.sudo().wah_preparation_ids.invalidate_recordset(['state'])
        for order in self.sudo():
            if order.wah_route_state in ('on_way', 'delivered') or any(prep.state in ('collected', 'delivered') for prep in order.wah_preparation_ids):
                raise ValidationError('El pedido ya fue retirado. Revisá la devolución de la mercadería antes de cancelar.')
            if order.wah_collection_ids.filtered(lambda receipt: receipt.state == 'posted'):
                raise ValidationError('El pedido tiene un cobro registrado. Revisá su devolución antes de cancelar.')
        result = super()._action_cancel()
        for order in self.filtered('website_id'):
            if order.wah_route_state != 'cancelled':
                order.sudo().write({'wah_route_state': 'cancelled'})
                order._wah_dispatch_event('Pedido cancelado antes del retiro.')
        return result

    def _check_cart_is_ready_to_be_paid(self):
        if any(order.sudo().wah_collection_state == 'collected' for order in self):
            raise ValidationError('El pedido ya tiene un cobro de reparto registrado.')
        return super()._check_cart_is_ready_to_be_paid()


class DispatchPreparation(models.Model):
    _inherit = 'wah.preparation'

    def action_collect(self):
        orders = self.sudo().order_id.with_user(self.env.user)
        orders._wah_lock_dispatch()
        if any(order.wah_route_state != 'assigned' or not order.wah_courier_id.active for order in orders):
            raise ValidationError('Asigná un repartidor activo desde Reparto y cobros antes de retirar.')
        self.invalidate_recordset(['state'])
        first_pickups = self.filtered(lambda prep: prep.state != 'collected')
        result = super().action_collect()
        for prep in first_pickups:
            prep.sudo().order_id.with_user(self.env.user)._wah_dispatch_event('Retiro registrado en %s.' % prep.store_name)
        return result

    def action_deliver(self):
        raise ValidationError('Registrá la entrega completa desde wheel-ahorra → Reparto y cobros.')

    def action_open_dispatch(self):
        self.ensure_one()
        if not is_manager(self.env):
            raise AccessError('El panel de reparto corresponde a la administración.')
        return self.sudo().order_id.with_user(self.env.user).action_wah_open_dispatch()


class DispatchLine(models.Model):
    _inherit = 'sale.order.line'

    def _wah_check_dispatched_changes(self):
        self.check_access('write')
        orders = self.sudo().order_id
        if orders:
            self.env.cr.execute('SELECT id FROM sale_order WHERE id IN %s ORDER BY id FOR UPDATE', (tuple(sorted(orders.ids)),))
            orders.invalidate_recordset(['wah_route_state'])
        if any(line.order_id.sudo().wah_route_state in ('on_way', 'delivered') for line in self):
            raise ValidationError('No se pueden cambiar productos o importes de un pedido que ya salió a reparto.')

    def write(self, values):
        if {'product_id', 'product_uom_qty', 'product_uom_id', 'price_unit', 'discount', 'tax_ids', 'name'} & values.keys():
            self._wah_check_dispatched_changes()
        return super().write(values)

    def unlink(self):
        self.check_access('unlink')
        self._wah_check_dispatched_changes()
        return super().unlink()

    @api.model_create_multi
    def create(self, values_list):
        self.check_access('create')
        orders = self.env['sale.order'].sudo().browse(sorted({values['order_id'] for values in values_list if values.get('order_id')}))
        if orders:
            self.env.cr.execute('SELECT id FROM sale_order WHERE id IN %s ORDER BY id FOR UPDATE', (tuple(orders.ids),))
            orders.invalidate_recordset(['wah_route_state'])
        for values in values_list:
            order = self.env['sale.order'].sudo().browse(values.get('order_id'))
            if order.wah_route_state in ('on_way', 'delivered'):
                raise ValidationError('El pedido ya salió a reparto. No se pueden agregar líneas.')
        return super().create(values_list)


class DispatchTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.model_create_multi
    def create(self, values_list):
        transactions = super().create(values_list)
        orders = transactions.sudo().sale_order_ids
        if orders:
            self.env.cr.execute('SELECT id FROM sale_order WHERE id IN %s ORDER BY id FOR UPDATE', (tuple(sorted(orders.ids)),))
            if self.env['wah.collection'].sudo().search_count([('order_id', 'in', orders.ids), ('state', '=', 'posted')]):
                raise ValidationError('El pedido ya tiene un cobro de reparto registrado. No se puede iniciar otro pago.')
        return transactions
