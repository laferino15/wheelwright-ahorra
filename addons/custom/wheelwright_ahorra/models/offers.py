"""Promociones visibles respaldadas por reglas nativas de precios."""
import math

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError
from .merchant import is_manager


class Offer(models.Model):
    _name = 'wah.offer'
    _description = 'Oferta de wheel-ahorra'
    _order = 'sequence, id desc'

    name = fields.Char(related='product_id.name')
    sequence = fields.Integer(string='Orden', default=10)
    product_id = fields.Many2one('product.template', string='Producto', required=True, ondelete='restrict')
    website_id = fields.Many2one('website', string='Sitio', required=True, default=lambda self: self.env['website'].get_current_website())
    company_id = fields.Many2one(related='website_id.company_id', store=True)
    pricelist_id = fields.Many2one('product.pricelist', string='Lista de precios', required=True,
        default=lambda self: self.env['website'].get_current_website().pricelist_ids[:1])
    discount = fields.Float(string='Descuento (%)', required=True, digits=(6, 2))
    date_start = fields.Datetime(string='Vigente desde', required=True, default=fields.Datetime.now)
    date_end = fields.Datetime(string='Vigente hasta')
    state = fields.Selection([('draft', 'Borrador'), ('published', 'Publicada'), ('paused', 'Pausada')], default='draft', required=True, readonly=True, copy=False)
    rule_id = fields.Many2one('product.pricelist.item', string='Regla de precio', readonly=True, copy=False, ondelete='set null')

    def init(self):
        self.env.cr.execute("CREATE UNIQUE INDEX IF NOT EXISTS wah_offer_one_published ON wah_offer (product_id, pricelist_id) WHERE state = 'published'")

    @api.constrains('discount', 'date_start', 'date_end', 'pricelist_id', 'website_id', 'product_id')
    def _check_offer(self):
        for offer in self:
            if not math.isfinite(offer.discount) or not 0 < offer.discount < 100:
                raise ValidationError('Ingresá un descuento mayor que 0 y menor que 100 %.')
            if offer.date_end and offer.date_end <= offer.date_start:
                raise ValidationError('El fin de la oferta debe ser posterior al inicio.')
            if offer.pricelist_id not in offer.website_id.pricelist_ids:
                raise ValidationError('La lista de precios debe estar disponible en este sitio.')
            if offer.product_id.website_id and offer.product_id.website_id != offer.website_id:
                raise ValidationError('El producto pertenece a otro sitio.')
            if offer.product_id.company_id and offer.product_id.company_id != offer.company_id:
                raise ValidationError('El producto pertenece a otra compañía.')

    @api.model_create_multi
    def create(self, values):
        if not is_manager(self.env):
            raise AccessError('Las promociones las administra wheel-ahorra.')
        if any(v.get('state', 'draft') != 'draft' or v.get('rule_id') for v in values):
            raise AccessError('Creá un borrador y usá Publicar oferta.')
        return super().create(values)

    def write(self, values):
        if not self.env.su:
            self._lock()
            if {'rule_id', 'state'} & values.keys():
                raise AccessError('Usá los botones Publicar y Pausar.')
            if any(o.state == 'published' for o in self) and set(values) - {'sequence'}:
                raise ValidationError('Pausá la oferta antes de cambiar sus condiciones.')
        return super().write(values)

    def unlink(self):
        self._lock()
        if any(o.state == 'published' for o in self):
            raise ValidationError('Pausá la oferta antes de eliminarla.')
        return super().unlink()

    def _lock(self):
        if not is_manager(self.env):
            raise AccessError('Las promociones las administra wheel-ahorra.')
        self.check_access('write')
        if self:
            self.env.cr.execute('SELECT id FROM wah_offer WHERE id IN %s ORDER BY id FOR UPDATE', (tuple(sorted(self.ids)),))
            self.invalidate_recordset()

    def action_publish(self):
        self._lock()
        if not self.env['res.groups']._is_feature_enabled('product.group_product_pricelist'):
            raise ValidationError('Activá las listas de precios en Odoo antes de publicar promociones.')
        for offer in self:
            if offer.state == 'published':
                continue
            if not offer.product_id.is_published or not offer.product_id.sale_ok:
                raise ValidationError('Publicá primero el producto en la tienda.')
            if offer.product_id.product_variant_count != 1:
                raise ValidationError('Esta versión de ofertas requiere productos con una sola variante.')
            if offer.date_end and offer.date_end <= fields.Datetime.now():
                raise ValidationError('La fecha de fin ya pasó.')
            self.env.cr.execute('SELECT id FROM product_template WHERE id = %s FOR UPDATE', (offer.product_id.id,))
            others = self.sudo().search([('id', '!=', offer.id), ('product_id', '=', offer.product_id.id),
                ('pricelist_id', '=', offer.pricelist_id.id), ('state', '=', 'published')])
            if others:
                raise ValidationError('Ya existe una oferta publicada para este producto y lista. Pausala antes de publicar otra.')
            rule = self.env['product.pricelist.item'].create({
                'pricelist_id': offer.pricelist_id.id, 'applied_on': '1_product',
                'product_tmpl_id': offer.product_id.id, 'min_quantity': 1,
                'compute_price': 'percentage', 'base': 'list_price', 'percent_price': offer.discount,
                'date_start': offer.date_start, 'date_end': offer.date_end})
            offer.sudo().write({'rule_id': rule.id, 'state': 'published'})
        return True

    def action_pause(self):
        self._lock()
        for offer in self:
            offer.rule_id.unlink()
            offer.sudo().write({'rule_id': False, 'state': 'paused'})
        return True


class Website(models.Model):
    _inherit = 'website'

    def _wah_offer_cards(self, limit=None):
        self.ensure_one()
        from odoo.http import request
        now = fields.Datetime.now()
        offers = self.env['wah.offer'].sudo().search([
            ('website_id', '=', self.id), ('pricelist_id', '=', request.pricelist.id),
            ('state', '=', 'published'), ('date_start', '<=', now),
            '|', ('date_end', '=', False), ('date_end', '>=', now)])
        products = self.env['product.template'].search(self.sale_product_domain() + [('id', 'in', offers.product_id.ids), ('is_published', '=', True)])
        prices = products._get_sales_prices(self)
        rules = request.pricelist._compute_price_rule(products, 1.0, date=now)
        cards = []
        for offer in offers:
            product = products.filtered(lambda p: p.id == offer.product_id.id)
            if not product or product.wah_sold_out or rules[product.id][1] != offer.rule_id.id:
                continue
            values = prices[product.id]
            previous, current = values.get('base_price', 0), values['price_reduce']
            if previous <= current or current < 0:
                continue
            discount = 100 * (previous - current) / previous
            cards.append({'product': product, 'previous': previous, 'current': current,
                          'discount_label': '%s%%' % ('%.2f' % discount).rstrip('0').rstrip('.'),
                          'saving': previous - current})
            if limit and len(cards) >= limit:
                break
        return cards


class WebsitePage(models.Model):
    _inherit = 'website.page'

    @api.model
    def _allow_to_use_cache(self, request):
        # La portada contiene precios por visitante y ofertas con vencimiento.
        # El caché completo de páginas públicas no distingue esas condiciones.
        if request.httprequest.path == '/':
            return False
        return super()._allow_to_use_cache(request)
