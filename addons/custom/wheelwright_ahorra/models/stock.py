"""Disponibilidad para ventas web por presentación; independiente del depósito físico."""
import math
from collections import defaultdict

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.tools.float_utils import float_compare, float_round

from .merchant import MerchantProduct


class MerchantStock(models.Model):
    _inherit = 'wah.merchant.product'

    stock_tracking = fields.Boolean(string='Controlar stock para la tienda', default=False)
    stock_quantity = fields.Float(string='Cantidad disponible para vender', digits='Product Unit of Measure', default=0)
    _editable = MerchantProduct._editable | {'stock_tracking', 'stock_quantity'}
    _catalog_stock_unique = models.Constraint('UNIQUE(product_tmpl_id)', 'Un producto del catálogo solo puede estar asociado a una propuesta de comercio.')

    @api.constrains('stock_quantity')
    def _check_stock_quantity(self):
        for item in self:
            if not math.isfinite(item.stock_quantity) or item.stock_quantity < 0:
                raise ValidationError('La cantidad disponible debe ser un número mayor o igual a cero.')

    def _lock_stock(self):
        if self:
            self.env.cr.execute('SELECT id FROM wah_merchant_product WHERE id IN %s ORDER BY id FOR UPDATE', (tuple(sorted(self.ids)),))
            self.invalidate_recordset(['stock_tracking', 'stock_quantity', 'available', 'state', 'product_tmpl_id'])

    def write(self, vals):
        if {'stock_quantity', 'stock_tracking', 'available'} & vals.keys():
            self._check_owner()
            self._lock_stock()
        return super().write(vals)

    def action_update_stock(self, tracking, quantity, available):
        self.ensure_one()
        self._check_owner()
        if self.merchant_id.state != 'approved':
            raise ValidationError('El comercio debe estar aprobado para actualizar su disponibilidad.')
        if type(tracking) is not bool or type(available) is not bool:
            raise ValidationError('Revisá las opciones de disponibilidad.')
        try:
            quantity = float(quantity)
        except (TypeError, ValueError):
            raise ValidationError('Ingresá una cantidad válida.')
        if not math.isfinite(quantity) or quantity < 0:
            raise ValidationError('La cantidad disponible debe ser un número mayor o igual a cero.')
        self._lock_stock()
        self.sudo().write({'stock_tracking': tracking, 'stock_quantity': quantity, 'available': available})
        if self.state == 'approved' and self.sudo().product_tmpl_id:
            self.sudo().product_tmpl_id.write({'is_published': available})
        return True


class CatalogStock(models.Model):
    _inherit = 'product.template'

    wah_sold_out = fields.Boolean(string='Agotado en el comercio', compute='_compute_wah_sold_out', compute_sudo=True)

    def _compute_wah_sold_out(self):
        offers = self.env['wah.merchant.product'].sudo().search([('product_tmpl_id', 'in', self.ids)])
        mapping = {offer.product_tmpl_id.id: offer for offer in offers}
        for product in self:
            offer = mapping.get(product.id)
            product.wah_sold_out = bool(offer and (not offer.available or (offer.stock_tracking and offer.stock_quantity <= 0)))


class StockOrderLine(models.Model):
    _inherit = 'sale.order.line'

    wah_stock_offer_id = fields.Many2one('wah.merchant.product', readonly=True, copy=False, ondelete='restrict', groups='product.group_product_manager')
    wah_stock_reserved = fields.Float(readonly=True, copy=False, digits='Product Unit of Measure', groups='product.group_product_manager')

    def write(self, values):
        if {'wah_stock_offer_id', 'wah_stock_reserved'} & values.keys() and not self.env.su:
            raise AccessError('Las reservas de stock las administra el sistema al confirmar el pedido.')
        return super().write(values)


class StockOrder(models.Model):
    _inherit = 'sale.order'

    def _wah_stock_requirements(self):
        lines = self.sudo().filtered('website_id').order_line.filtered(lambda line: line.product_id and not line.display_type and not line.is_delivery)
        offers = self.env['wah.merchant.product'].sudo().search([('product_tmpl_id', 'in', lines.product_id.product_tmpl_id.ids)])
        mapping = {offer.product_tmpl_id.id: offer for offer in offers}
        return lines, offers, mapping

    def _wah_validate_stock(self, reserve=False):
        lines, offers, mapping = self._wah_stock_requirements()
        offers._lock_stock()
        needed = defaultdict(float)
        reservations = []
        for line in lines:
            offer = mapping.get(line.product_id.product_tmpl_id.id)
            if not offer or line.wah_stock_reserved:
                continue
            if line.product_uom_qty <= 0:
                raise ValidationError('Los productos del pedido deben tener una cantidad mayor que cero.')
            if offer.state != 'approved' or offer.merchant_id.state != 'approved' or not offer.available:
                raise ValidationError('El producto %s ya no está disponible. Revisá tu carrito.' % line.product_id.display_name)
            if offer.merchant_id.website_id != line.order_id.website_id or (line.wah_merchant_id and offer.merchant_id != line.wah_merchant_id):
                raise ValidationError('Cambió el comercio de un producto. Quitalo del carrito y volvé a agregarlo.')
            if offer.stock_tracking:
                quantity = line.product_uom_id._compute_quantity(line.product_uom_qty, line.product_id.uom_id, round=False)
                needed[offer.id] += quantity
                reservations.append((line, offer, quantity))
        for offer in offers:
            if float_compare(needed[offer.id], offer.stock_quantity, precision_digits=6) > 0:
                raise ValidationError('No queda stock suficiente de %s. Disponible: %s. Actualizá tu carrito.' % (offer.name, offer.stock_quantity))
        if reserve:
            for offer in offers:
                if needed[offer.id]:
                    offer.write({'stock_quantity': max(0, offer.stock_quantity - needed[offer.id])})
            for line, offer, quantity in reservations:
                line.sudo().write({'wah_stock_offer_id': offer.id, 'wah_stock_reserved': quantity})

    def action_confirm(self):
        self.check_access('write')
        with self.env.cr.savepoint():
            if self:
                self.env.cr.execute('SELECT id FROM sale_order WHERE id IN %s ORDER BY id FOR UPDATE', (tuple(sorted(self.ids)),))
                self.invalidate_recordset(['state'])
            self.filtered(lambda order: order.website_id and order.state in ('draft', 'sent'))._wah_validate_stock(reserve=True)
            return super().action_confirm()

    def _action_cancel(self):
        self.check_access('write')
        with self.env.cr.savepoint():
            if self:
                self.env.cr.execute('SELECT id FROM sale_order WHERE id IN %s ORDER BY id FOR UPDATE', (tuple(sorted(self.ids)),))
            all_lines = self.sudo().order_line
            all_lines.invalidate_recordset(['wah_stock_reserved', 'wah_stock_offer_id'])
            lines = all_lines.filtered(lambda line: line.wah_stock_reserved > 0)
            offers = lines.wah_stock_offer_id
            offers._lock_stock()
            delivered = {(prep.order_id.id, prep.merchant_id.id) for prep in self.sudo().wah_preparation_ids if prep.state == 'delivered'}
            result = super()._action_cancel()
            for line in lines:
                offer = line.wah_stock_offer_id
                # Lo ya entregado requiere un circuito de devolución, no una reposición automática.
                if (line.order_id.id, offer.merchant_id.id) not in delivered:
                    if offer.stock_tracking:
                        offer.write({'stock_quantity': offer.stock_quantity + line.wah_stock_reserved})
                    line.write({'wah_stock_reserved': 0, 'wah_stock_offer_id': False})
            return result

    def _verify_updated_quantity(self, order_line, product_id, new_qty, uom_id, **kwargs):
        quantity, warning = super()._verify_updated_quantity(order_line, product_id, new_qty, uom_id, **kwargs)
        if not self.website_id:
            return quantity, warning
        product = self.env['product.product'].sudo().browse(product_id)
        offer = self.env['wah.merchant.product'].sudo().search([('product_tmpl_id', '=', product.product_tmpl_id.id)], limit=1)
        if not offer:
            return quantity, warning
        if not offer.available or offer.state != 'approved' or offer.merchant_id.state != 'approved':
            return 0, 'Este producto ya no está disponible.'
        if not offer.stock_tracking:
            return quantity, warning
        other = self.sudo().order_line.filtered(lambda line: line != order_line and line.product_id.product_tmpl_id == product.product_tmpl_id)
        used = sum(line.product_uom_id._compute_quantity(line.product_uom_qty, product.uom_id, round=False) for line in other)
        uom = self.env['uom.uom'].browse(uom_id)
        maximum = product.uom_id._compute_quantity(max(0, offer.stock_quantity - used), uom, round=False)
        maximum = float_round(maximum, precision_rounding=uom.rounding, rounding_method='DOWN')
        if quantity > maximum:
            return maximum, 'Stock limitado: ajustamos la cantidad disponible de %s a %s.' % (offer.name, maximum)
        return quantity, warning

    def _check_cart_is_ready_to_be_paid(self):
        result = super()._check_cart_is_ready_to_be_paid()
        self._wah_validate_stock()
        return result
