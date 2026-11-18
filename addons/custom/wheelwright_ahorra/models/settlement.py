"""Liquidaciones operativas por local; no realizan transferencias bancarias."""
import math

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError

from .merchant import is_manager


class Merchant(models.Model):
    _inherit = 'wah.merchant'

    commission_rate = fields.Float(string='Comisión de la plataforma (%)', default=0,
                                   digits=(6, 4), groups='product.group_product_manager')

    @api.constrains('commission_rate')
    def _check_commission_rate(self):
        for merchant in self:
            if not math.isfinite(merchant.commission_rate) or not 0 <= merchant.commission_rate <= 100:
                raise ValidationError('La comisión debe estar entre 0 y 100 %.')


class SettlementLine(models.Model):
    _name = 'wah.settlement.line'
    _description = 'Pedido incluido en una liquidación'
    _order = 'id'

    settlement_id = fields.Many2one('wah.settlement', required=True, readonly=True, ondelete='cascade')
    preparation_id = fields.Many2one('wah.preparation', string='Preparación', required=True, readonly=True, ondelete='restrict')
    reserved_preparation_id = fields.Many2one('wah.preparation', readonly=True, ondelete='restrict')
    order_id = fields.Many2one('sale.order', string='Pedido', required=True, readonly=True, ondelete='restrict')
    currency_id = fields.Many2one(related='settlement_id.currency_id')
    gross_amount = fields.Monetary(string='Productos con impuestos', readonly=True)
    commission_rate = fields.Float(string='Comisión (%)', digits=(6, 4), readonly=True)
    commission_amount = fields.Monetary(string='Comisión', readonly=True)
    net_amount = fields.Monetary(string='A pagar al local', readonly=True)
    _one_reserved_preparation = models.Constraint(
        'UNIQUE(reserved_preparation_id)', 'Este pedido del local ya está incluido en otra liquidación.')

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            raise AccessError('El detalle se genera desde la liquidación.')
        return super().create(vals_list)

    def write(self, values):
        if not self.env.su or set(values) - {'reserved_preparation_id'}:
            raise AccessError('El detalle de la liquidación es inalterable.')
        return super().write(values)

    def unlink(self):
        raise AccessError('Las liquidaciones se anulan conservando su detalle.')


class Settlement(models.Model):
    _name = 'wah.settlement'
    _description = 'Liquidación operativa a comercio'
    _order = 'id desc'

    name = fields.Char(string='Liquidación', default='Nueva', readonly=True, copy=False)
    merchant_id = fields.Many2one('wah.merchant', string='Comercio', required=True, ondelete='restrict')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company, readonly=True)
    currency_id = fields.Many2one('res.currency', required=True, default=lambda self: self.env.company.currency_id, readonly=True)
    date_from = fields.Date(string='Entrega desde', required=True, default=fields.Date.context_today)
    date_to = fields.Date(string='Entrega hasta', required=True, default=fields.Date.context_today)
    state = fields.Selection([('draft', 'Borrador'), ('confirmed', 'Confirmada'),
                              ('paid', 'Pagada'), ('cancelled', 'Anulada')], default='draft', readonly=True, copy=False)
    line_ids = fields.One2many('wah.settlement.line', 'settlement_id', string='Pedidos', readonly=True, copy=False)
    gross_amount = fields.Monetary(string='Total de productos', compute='_compute_amounts')
    commission_amount = fields.Monetary(string='Comisión de plataforma', compute='_compute_amounts')
    net_amount = fields.Monetary(string='Total a pagar al local', compute='_compute_amounts')
    confirmed_at = fields.Datetime(string='Confirmada el', readonly=True, copy=False)
    confirmed_by = fields.Many2one('res.users', string='Confirmada por', readonly=True, copy=False)
    payment_method = fields.Selection([('cash', 'Efectivo'), ('transfer', 'Transferencia verificada')], string='Medio de pago', copy=False)
    payment_reference = fields.Char(string='Referencia / recibo de pago', copy=False)
    paid_at = fields.Datetime(string='Pago registrado el', readonly=True, copy=False)
    paid_by = fields.Many2one('res.users', string='Pago registrado por', readonly=True, copy=False)
    cancel_reason = fields.Text(string='Motivo de anulación', copy=False)
    cancelled_at = fields.Datetime(string='Anulada el', readonly=True, copy=False)
    cancelled_by = fields.Many2one('res.users', string='Anulada por', readonly=True, copy=False)

    @api.depends('line_ids.gross_amount', 'line_ids.commission_amount', 'line_ids.net_amount')
    def _compute_amounts(self):
        for settlement in self:
            settlement.gross_amount = sum(settlement.line_ids.mapped('gross_amount'))
            settlement.commission_amount = sum(settlement.line_ids.mapped('commission_amount'))
            settlement.net_amount = sum(settlement.line_ids.mapped('net_amount'))

    @api.constrains('date_from', 'date_to', 'merchant_id', 'company_id')
    def _check_period(self):
        for settlement in self:
            if settlement.date_from > settlement.date_to:
                raise ValidationError('La fecha inicial no puede ser posterior a la final.')
            if settlement.merchant_id.website_id.company_id != settlement.company_id:
                raise ValidationError('El comercio pertenece a otra compañía.')

    @api.model_create_multi
    def create(self, vals_list):
        if not is_manager(self.env):
            raise AccessError('Las liquidaciones las gestiona la administración.')
        allowed = {'merchant_id', 'date_from', 'date_to'}
        for values in vals_list:
            if set(values) - allowed:
                raise AccessError('Creá un borrador eligiendo comercio y período.')
        return super().create(vals_list)

    def _lock(self):
        if not is_manager(self.env):
            raise AccessError('Las liquidaciones las gestiona la administración.')
        self.check_access('write')
        # El mismo orden de bloqueos que el cobro: pedidos, luego liquidaciones.
        orders = self.sudo().line_ids.order_id.sorted('id')
        orders._wah_lock_dispatch(require_sale=False)
        if self:
            self.env.cr.execute('SELECT id FROM wah_settlement WHERE id IN %s ORDER BY id FOR UPDATE', (tuple(sorted(self.ids)),))
            self.invalidate_recordset()

    def write(self, values):
        if self.env.su:
            return super().write(values)
        self._lock()
        for settlement in self:
            allowed = {'cancel_reason'} if settlement.state in ('draft', 'confirmed') else set()
            if settlement.state == 'draft' and not settlement.line_ids:
                allowed |= {'merchant_id', 'date_from', 'date_to'}
            if settlement.state == 'confirmed':
                allowed |= {'payment_method', 'payment_reference'}
            if set(values) - allowed:
                raise AccessError('Usá las acciones de la liquidación. El detalle generado no se modifica.')
        return super().write(values)

    def unlink(self):
        raise AccessError('Anulá la liquidación con un motivo para conservar el historial.')

    def copy(self, default=None):
        raise AccessError('Creá una nueva liquidación para otro período.')

    def _validate_orders(self):
        for line in self.sudo().line_ids:
            order = line.order_id
            order.invalidate_recordset(['state', 'wah_route_state', 'wah_collection_state'])
            if (order.state != 'sale' or order.wah_route_state != 'delivered'
                    or order.wah_collection_state != 'collected' or line.preparation_id.state != 'delivered'):
                raise ValidationError('Todos los pedidos deben estar entregados y completamente cobrados.')

    def action_generate(self):
        self.ensure_one()
        self._lock()
        if self.state != 'draft' or self.line_ids:
            raise ValidationError('El detalle ya se generó o la liquidación está cerrada.')
        # Serializa generaciones del mismo comercio, incluso desde dos borradores.
        self.env.cr.execute('SELECT id FROM wah_merchant WHERE id = %s FOR UPDATE', (self.merchant_id.id,))
        candidates = self.env['wah.preparation'].sudo().search([
            ('merchant_id', '=', self.merchant_id.id), ('state', '=', 'delivered'),
            ('order_id.company_id', '=', self.company_id.id),
            ('order_id.currency_id', '=', self.currency_id.id),
            ('order_id.wah_delivery_date', '>=', self.date_from),
            ('order_id.wah_delivery_date', '<=', self.date_to),
            ('order_id.state', '=', 'sale'), ('order_id.wah_route_state', '=', 'delivered'),
            ('order_id.wah_collection_state', '=', 'collected')], order='order_id, id')
        candidates.order_id._wah_lock_dispatch(require_sale=False)
        candidates.order_id.invalidate_recordset(['state', 'wah_route_state', 'wah_collection_state'])
        candidates.invalidate_recordset()
        reserved = self.env['wah.settlement.line'].sudo().search([
            ('reserved_preparation_id', 'in', candidates.ids)]).reserved_preparation_id
        candidates -= reserved
        candidates = candidates.filtered(lambda p: p.state == 'delivered' and p.order_id.state == 'sale'
            and p.order_id.wah_route_state == 'delivered' and p.order_id.wah_collection_state == 'collected')
        if not candidates:
            raise ValidationError('No hay pedidos entregados y cobrados pendientes para este comercio y período, en la moneda de la compañía.')
        self.merchant_id.invalidate_recordset(['commission_rate'])
        rate = self.merchant_id.commission_rate
        values = []
        for prep in candidates:
            gross = self.currency_id.round(prep.amount_total)
            if gross < 0:
                raise ValidationError('Las devoluciones requieren revisión antes de liquidar.')
            commission = self.currency_id.round(gross * rate / 100)
            values.append({'settlement_id': self.id, 'preparation_id': prep.id, 'reserved_preparation_id': prep.id,
                           'order_id': prep.order_id.id, 'gross_amount': gross, 'commission_rate': rate,
                           'commission_amount': commission, 'net_amount': self.currency_id.round(gross - commission)})
        self.env['wah.settlement.line'].sudo().create(values)
        self.sudo().write({'name': 'LIQ-%06d' % self.id})
        return True

    def action_confirm(self):
        self._lock()
        for settlement in self:
            if settlement.state != 'draft' or not settlement.line_ids:
                raise ValidationError('Generá y revisá el detalle antes de confirmar.')
            settlement._validate_orders()
            settlement.sudo().write({'state': 'confirmed', 'confirmed_at': fields.Datetime.now(), 'confirmed_by': self.env.uid})
        return True

    def action_pay(self):
        self._lock()
        for settlement in self:
            if settlement.state != 'confirmed':
                raise ValidationError('La liquidación debe estar confirmada y sin pagar.')
            settlement._validate_orders()
            if not settlement.payment_method or not (settlement.payment_reference or '').strip():
                raise ValidationError('Elegí el medio de pago y cargá la referencia o recibo del pago realizado.')
            settlement.sudo().write({'state': 'paid', 'paid_at': fields.Datetime.now(), 'paid_by': self.env.uid})
        return True

    def action_cancel(self):
        self._lock()
        for settlement in self:
            if settlement.state not in ('draft', 'confirmed'):
                raise ValidationError('Solo se pueden anular liquidaciones sin pagar.')
            if len((settlement.cancel_reason or '').strip()) < 3:
                raise ValidationError('Indicá un motivo de anulación de al menos 3 caracteres.')
            settlement.sudo().line_ids.write({'reserved_preparation_id': False})
            settlement.sudo().write({'state': 'cancelled', 'cancelled_at': fields.Datetime.now(), 'cancelled_by': self.env.uid})
        return True


class Collection(models.Model):
    _inherit = 'wah.collection'

    def _void(self, reason):
        self.ensure_one()
        self.order_id._wah_lock_dispatch()
        if self.env['wah.settlement.line'].sudo().search_count([
                ('order_id', '=', self.order_id.id), ('reserved_preparation_id', '!=', False)]):
            raise ValidationError('El cobro respalda una liquidación. Anulá primero las liquidaciones sin pagar; las pagadas requieren una devolución por separado.')
        return super()._void(reason)
