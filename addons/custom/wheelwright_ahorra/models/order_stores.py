from collections import OrderedDict

from markupsafe import Markup, escape

from odoo import api, fields, models
from odoo.tools.misc import format_amount


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    wah_store_name = fields.Char(string='Comercio', readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            line.wah_store_name = line.product_id.wah_store_name or False
        return lines

    def write(self, values):
        result = super().write(values)
        if 'product_id' in values:
            for line in self.filtered(lambda item: item.order_id.state in ('draft', 'sent')):
                line.wah_store_name = line.product_id.wah_store_name or False
        return result


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    wah_store_breakdown = fields.Html(
        string='Preparación por comercio', compute='_compute_wah_store_breakdown', sanitize=True,
    )

    @api.depends('order_line.name', 'order_line.wah_store_name', 'order_line.product_uom_qty',
                 'order_line.product_uom_id', 'order_line.price_total', 'order_line.display_type',
                 'order_line.is_delivery', 'currency_id')
    def _compute_wah_store_breakdown(self):
        for order in self:
            groups = OrderedDict()
            for line in order.order_line:
                if line.display_type or line.is_delivery or not line.product_id:
                    continue
                label = line.wah_store_name or 'Comercio sin asignar'
                groups.setdefault(label, []).append(line)
            blocks = []
            for label, lines in groups.items():
                rows = [Markup('<li><strong>%s %s</strong> · %s</li>') % (
                    escape(f'{line.product_uom_qty:g}'), escape(line.product_uom_id.name),
                    escape(line.name),
                ) for line in lines]
                amount = sum(line.price_total for line in lines)
                blocks.append(Markup('<section><h4>%s</h4><ul>%s</ul><p>Subtotal de productos con impuestos: <strong>%s</strong></p></section>') % (
                    escape(label), Markup('').join(rows),
                    escape(format_amount(order.env, amount, order.currency_id)),
                ))
            order.wah_store_breakdown = Markup('').join(blocks) if blocks else False
