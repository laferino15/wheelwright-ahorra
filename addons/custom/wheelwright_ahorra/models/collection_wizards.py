from odoo import api, fields, models


class RegisterCollection(models.TransientModel):
    _name = 'wah.collection.register'
    _description = 'Registrar cobro del reparto'

    order_id = fields.Many2one('sale.order', string='Pedido', required=True, readonly=True)
    currency_id = fields.Many2one(related='order_id.currency_id', readonly=True)
    amount = fields.Monetary(string='Total a cobrar', required=True, readonly=True)
    method = fields.Selection([('cash', 'Efectivo'), ('transfer', 'Transferencia verificada')], string='Medio de cobro', default='cash', required=True)
    received_amount = fields.Monetary(string='Efectivo recibido')
    change_amount = fields.Monetary(string='Vuelto a entregar', compute='_compute_change')
    reference = fields.Char(string='Referencia / comprobante', size=200)

    @api.model
    def default_get(self, names):
        values = super().default_get(names)
        if values.get('order_id'):
            order = self.env['sale.order'].browse(values['order_id'])
            order._wah_lock_dispatch()
            values.update(amount=order.amount_total, received_amount=max(order.amount_total, order.wah_cash_tendered))
        return values

    @api.depends('received_amount', 'amount', 'method')
    def _compute_change(self):
        for wizard in self:
            wizard.change_amount = max(0, wizard.received_amount - wizard.amount) if wizard.method == 'cash' else 0

    def action_register(self):
        self.ensure_one()
        receipt = self.order_id._wah_register_collection(self.method, self.amount, self.received_amount, self.reference or '')
        return {'type': 'ir.actions.act_window', 'name': 'Cobro registrado', 'res_model': 'wah.collection', 'res_id': receipt.id, 'view_mode': 'form', 'target': 'current'}


class VoidCollection(models.TransientModel):
    _name = 'wah.collection.void'
    _description = 'Anular registro de cobro'

    collection_id = fields.Many2one('wah.collection', string='Registro', required=True, readonly=True)
    reason = fields.Text(string='Motivo de anulación', required=True)

    def action_void(self):
        self.ensure_one()
        self.collection_id._void(self.reason)
        return {'type': 'ir.actions.act_window_close'}
