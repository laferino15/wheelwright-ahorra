from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    wah_local_checkout = fields.Boolean(string='Compra local wheel-ahorra', default=False)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    wah_delivery_notes = fields.Text(string='Observaciones de entrega', copy=False)
    wah_cash_tendered = fields.Monetary(string='Efectivo para preparar cambio', copy=False)
    wah_invoice_requested = fields.Boolean(string='Solicita factura con datos específicos', copy=False)
