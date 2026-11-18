"""Acciones limitadas al local propio o al recorrido asignado al repartidor."""
from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


class Courier(models.Model):
    _inherit = 'wah.courier'

    user_id = fields.Many2one('res.users', string='Cuenta para Mi reparto', ondelete='restrict',
                             groups='product.group_product_manager', domain=[('active', '=', True)])
    _one_account = models.Constraint('UNIQUE(user_id)', 'Esta cuenta ya está vinculada a otro repartidor.')


class Preparation(models.Model):
    _inherit = 'wah.preparation'

    pickup_requested_at = fields.Datetime(string='Retiro solicitado', readonly=True, copy=False)
    pickup_requested_by = fields.Many2one('res.users', string='Retiro solicitado por', readonly=True, copy=False)

    def _wah_lock_merchant_pickup(self):
        self.ensure_one()
        self.check_access('write')
        if self.merchant_id.owner_id.id != self.env.uid:
            raise AccessError('Solo el dueño puede gestionar el retiro de su local.')
        order = self.sudo().order_id
        order._wah_lock_dispatch()
        self.env.cr.execute('SELECT id FROM wah_preparation WHERE id=%s FOR UPDATE', (self.id,))
        self.invalidate_recordset()
        return order

    def action_request_pickup(self):
        order = self._wah_lock_merchant_pickup()
        if self.state != 'ready':
            raise ValidationError('Primero marcá los productos como listos para retirar.')
        if not self.pickup_requested_at:
            self.sudo().write({'pickup_requested_at': fields.Datetime.now(), 'pickup_requested_by': self.env.uid})
            order._wah_dispatch_event('El comercio %s solicitó el retiro.' % self.store_name)
        return True

    def action_merchant_handoff(self):
        order = self._wah_lock_merchant_pickup()
        if self.state == 'collected':
            return True
        if order.wah_route_state != 'assigned' or not order.wah_courier_id.active:
            raise ValidationError('El pedido debe tener un repartidor activo asignado.')
        if not self.pickup_requested_at:
            raise ValidationError('Solicitá el retiro antes de confirmar la entrega al repartidor.')
        self.sudo()._transition('collected', 'ready', 'collected_at', manager_only=True)
        order._wah_dispatch_event('El comercio %s confirmó la entrega a %s.' % (self.store_name, order.wah_courier_id.name))
        return True


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    wah_courier_accepted_at = fields.Datetime(string='Recorrido aceptado', readonly=True, copy=False,
                                             groups='product.group_product_manager')

    def write(self, values):
        if not self.env.su and 'wah_courier_accepted_at' in values:
            raise AccessError('La aceptación se registra desde Mi reparto.')
        if 'wah_courier_id' in values and any(o.sudo().wah_courier_id.id != values['wah_courier_id'] for o in self):
            values = dict(values, wah_courier_accepted_at=False)
        return super().write(values)

    def _wah_lock_courier_portal(self, website, lock=True):
        self.ensure_one()
        # No se conceden permisos generales de venta al repartidor.
        # La elevación se limita a este pedido después de comprobar la cuenta.
        order = self.sudo()
        if lock:
            self.env.cr.execute('SELECT id FROM sale_order WHERE id=%s FOR UPDATE', (self.id,))
        order.invalidate_recordset()
        courier = order.wah_courier_id
        if lock and courier:
            self.env.cr.execute('SELECT id FROM wah_courier WHERE id=%s FOR SHARE', (courier.id,))
            courier.invalidate_recordset()
        if (not self.env.user.active or not courier or not courier.active or courier.user_id.id != self.env.uid
                or order.website_id != website or order.company_id != website.company_id):
            raise AccessError('Este recorrido no está asignado a tu cuenta.')
        if order.state != 'sale' or order.wah_route_state == 'cancelled':
            raise ValidationError('El pedido no está confirmado o fue cancelado.')
        return order

    def _wah_courier_action(self, website, action, preparation_id=None, method=None, received=0, reference=''):
        order = self._wah_lock_courier_portal(website)
        if action == 'accept':
            if (order.wah_route_state not in ('assigned', 'on_way', 'delivered')
                    or (order.wah_route_state == 'delivered' and order.wah_collection_state != 'pending')):
                raise ValidationError('Solo podés aceptar un recorrido asignado que todavía tenga tareas pendientes.')
            if not order.wah_courier_accepted_at:
                order.write({'wah_courier_accepted_at': fields.Datetime.now()})
                order._wah_dispatch_event('El repartidor %s aceptó el recorrido.' % order.wah_courier_id.name)
            return True
        if not order.wah_courier_accepted_at:
            raise ValidationError('Aceptá el recorrido antes de registrar movimientos.')
        if action == 'pickup':
            if order.wah_route_state != 'assigned':
                raise ValidationError('El pedido ya salió a reparto o está cerrado.')
            prep = order.wah_preparation_ids.filtered(lambda p: p.id == preparation_id)
            if not prep:
                raise AccessError('La preparación no pertenece a este recorrido.')
            if prep.state != 'collected':
                prep._transition('collected', 'ready', 'collected_at', manager_only=True)
                order._wah_dispatch_event('El repartidor registró el retiro en %s.' % prep.store_name)
            return True
        if action == 'depart':
            return order.action_wah_dispatch()
        if action == 'deliver':
            return order.action_wah_deliver()
        if action == 'collect':
            return order._wah_register_collection(method, order.amount_total, received, reference)
        raise ValidationError('Elegí una acción válida del recorrido.')

    def _wah_courier_summary(self, website, detail=False):
        order = self._wah_lock_courier_portal(website, lock=False)
        result = {'id': order.id, 'name': order.name, 'route_state': order.wah_route_state,
                  'route_label': dict(order._fields['wah_route_state'].selection)[order.wah_route_state],
                  'accepted': bool(order.wah_courier_accepted_at), 'delivery_label': order.wah_delivery_label,
                  'amount': order.amount_total, 'currency': order.currency_id,
                  'collection_state': order.wah_collection_state}
        if detail:
            partner = order.partner_shipping_id
            result.update(customer=partner.name, address=partner._display_address(), phone=partner.phone,
                          notes=order.wah_delivery_notes, cash_tendered=order.wah_cash_tendered,
                          pickups=[{'id': p.id, 'store': p.store_name, 'state': p.state,
                                    'state_label': dict(p._fields['state'].selection)[p.state],
                                    'address': p.merchant_id.street, 'phone': p.merchant_id.phone,
                                    'requested': bool(p.pickup_requested_at), 'note': p.merchant_note,
                                    'items': [{'name': l.name, 'quantity': l.quantity, 'uom': l.uom_name} for l in p.line_ids]}
                                   for p in order.wah_preparation_ids])
            receipt = order.wah_collection_ids.filtered(lambda c: c.state == 'posted')[:1]
            result['receipt'] = {'name': receipt.name, 'amount': receipt.amount, 'change': receipt.change_amount} if receipt else False
        return result
