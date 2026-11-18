import math

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


def is_manager(env):
    return env.su or env.user.has_group('product.group_product_manager')


class Merchant(models.Model):
    _name = 'wah.merchant'
    _description = 'Comercio de wheel-ahorra'
    _order = 'create_date desc, id desc'

    name = fields.Char(string='Nombre del local', required=True)
    owner_id = fields.Many2one('res.users', string='Dueño', required=True, default=lambda self: self.env.user, ondelete='restrict')
    website_id = fields.Many2one('website', required=True, default=lambda self: self.env['website'].get_current_website(), ondelete='restrict')
    category_id = fields.Many2one('product.public.category', string='Rubro', required=True, ondelete='restrict')
    street = fields.Char(string='Dirección del local', required=True)
    phone = fields.Char(string='Teléfono / WhatsApp', required=True)
    hours = fields.Char(string='Horarios de atención')
    description = fields.Text(string='Descripción del local')
    logo = fields.Image(string='Logo', max_width=1024, max_height=1024)
    state = fields.Selection([('pending', 'Pendiente de aprobación'), ('approved', 'Aprobado'), ('rejected', 'Revisar solicitud')], default='pending', required=True, readonly=True)
    review_notes = fields.Text(string='Observaciones de la administración', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Comercio en catálogo', groups='product.group_product_manager', readonly=True, ondelete='restrict')
    product_ids = fields.One2many('wah.merchant.product', 'merchant_id', string='Productos')
    _owner_website_unique = models.Constraint('UNIQUE(owner_id, website_id)', 'Esta cuenta ya tiene un local registrado en este sitio.')

    _editable = {'name', 'category_id', 'street', 'phone', 'hours', 'description', 'logo'}

    @api.model_create_multi
    def create(self, vals_list):
        if not is_manager(self.env):
            for vals in vals_list:
                if set(vals) - self._editable:
                    raise AccessError('Solo podés registrar tu propio comercio.')
                vals.update(owner_id=self.env.uid, state='pending', website_id=self.env['website'].get_current_website().id)
        return super().create(vals_list)

    def write(self, vals):
        self.check_access('write')
        if not is_manager(self.env):
            if set(vals) - self._editable:
                raise AccessError('No podés cambiar el dueño ni aprobar tu comercio.')
            vals = dict(vals, state='pending', review_notes=False)
        return super().write(vals)

    @api.constrains('name', 'street', 'phone', 'category_id', 'website_id')
    def _validate_details(self):
        for store in self:
            if not all((value or '').strip() for value in [store.name, store.street, store.phone]):
                raise ValidationError('Completá nombre, dirección y teléfono del local.')
            if store.category_id.website_id and store.category_id.website_id != store.website_id:
                raise ValidationError('El rubro no pertenece a este sitio.')

    def action_approve(self):
        if not is_manager(self.env):
            raise AccessError('La aprobación corresponde a la administración.')
        self.check_access('write')
        for store in self:
            values = {'name': store.name, 'is_company': True, 'street': store.street,
                      'phone': store.phone, 'city': 'Wheelwright', 'country_id': self.env.ref('base.ar').id}
            if store.logo:
                values['image_1920'] = store.logo
            partner = store.partner_id.sudo()
            if partner:
                partner.write(values)
            else:
                partner = self.env['res.partner'].sudo().create(values)
            super(Merchant, store).write({'partner_id': partner.id, 'state': 'approved', 'review_notes': False})
        return True

    def action_reject(self):
        if not is_manager(self.env):
            raise AccessError('La revisión corresponde a la administración.')
        self.check_access('write')
        products = self.env['wah.merchant.product'].sudo().search([('merchant_id', 'in', self.ids)])
        products.mapped('product_tmpl_id').write({'is_published': False})
        products.write({'state': 'rejected', 'review_notes': 'El local requiere revisión. Revisá la información antes de reenviar tus productos.'})
        return super().write({'state': 'rejected'})


class MerchantProduct(models.Model):
    _name = 'wah.merchant.product'
    _description = 'Producto presentado por un comercio'
    _order = 'write_date desc, id desc'

    merchant_id = fields.Many2one('wah.merchant', required=True, string='Comercio', ondelete='restrict')
    name = fields.Char(string='Producto', required=True)
    category_id = fields.Many2one('product.public.category', string='Categoría', required=True, ondelete='restrict')
    presentation = fields.Char(string='Presentación / unidad de venta', required=True)
    description = fields.Text(string='Descripción')
    price = fields.Monetary(string='Precio final al cliente', currency_field='currency_id', required=True)
    currency_id = fields.Many2one(related='merchant_id.website_id.currency_id', readonly=True)
    image = fields.Image(string='Imagen', max_width=1920, max_height=1920)
    available = fields.Boolean(string='Disponible para vender', default=True)
    state = fields.Selection([('draft', 'Borrador'), ('pending', 'En revisión'), ('approved', 'Aprobado'), ('rejected', 'Requiere cambios')], default='draft', required=True, readonly=True)
    review_notes = fields.Text(string='Observaciones de la administración', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', string='Producto publicado', groups='product.group_product_manager', readonly=True, ondelete='restrict')
    _editable = {'name', 'category_id', 'presentation', 'description', 'price', 'image', 'available'}

    def _check_owner(self):
        self.check_access('write')
        if not is_manager(self.env) and any(p.merchant_id.owner_id.id != self.env.uid for p in self):
            raise AccessError('Solo podés administrar los productos de tu local.')

    @api.model_create_multi
    def create(self, vals_list):
        if not is_manager(self.env):
            for vals in vals_list:
                if set(vals) - (self._editable | {'merchant_id'}):
                    raise AccessError('No podés publicar ni aprobar productos directamente.')
                store = self.env['wah.merchant'].browse(vals.get('merchant_id')).exists()
                store.check_access('read')
                if not store or store.owner_id.id != self.env.uid:
                    raise AccessError('El producto debe pertenecer a tu local.')
                if store.state != 'approved':
                    raise ValidationError('Tu comercio debe estar aprobado para cargar productos.')
                vals['state'] = 'draft'
        return super().create(vals_list)

    def write(self, vals):
        self._check_owner()
        if not is_manager(self.env):
            if set(vals) - self._editable:
                raise AccessError('No podés cambiar el comercio ni aprobar productos.')
            # Una edición vuelve a revisión y retira la versión publicada.
            self.sudo().mapped('product_tmpl_id').write({'is_published': False})
            vals = dict(vals, state='draft', review_notes=False)
        return super().write(vals)

    @api.constrains('price', 'name', 'presentation', 'category_id', 'merchant_id')
    def _validate_product(self):
        for product in self:
            if not math.isfinite(product.price) or product.price <= 0:
                raise ValidationError('El precio debe ser un número mayor que cero.')
            if not (product.name or '').strip() or not (product.presentation or '').strip():
                raise ValidationError('Completá el nombre y la presentación del producto.')
            if product.category_id.website_id and product.category_id.website_id != product.merchant_id.website_id:
                raise ValidationError('La categoría no corresponde al sitio de tu local.')

    def action_submit(self):
        self._check_owner()
        for product in self:
            if product.state not in ('draft', 'rejected'):
                raise ValidationError('Solo se pueden enviar borradores o productos que requieren cambios.')
            if product.merchant_id.state != 'approved':
                raise ValidationError('El comercio todavía no está aprobado.')
            if not product.image:
                raise ValidationError('Agregá una imagen antes de enviar el producto a revisión.')
        return super().write({'state': 'pending', 'review_notes': False})

    def action_approve(self):
        if not is_manager(self.env):
            raise AccessError('La publicación corresponde a la administración.')
        self.check_access('write')
        for item in self:
            if item.state != 'pending' or item.merchant_id.state != 'approved' or not item.image:
                raise ValidationError('Revisá que el local esté aprobado y el producto tenga imagen y esté en revisión.')
            # El formulario expresa el precio FINAL. Convertirlo a precio base
            # usando los impuestos configurados, sin sumar IVA otra vez.
            product = item.product_tmpl_id.sudo()
            if not product:
                product = self.env['product.template'].sudo().create({'name': item.name, 'type': 'consu', 'sale_ok': True, 'purchase_ok': False, 'is_published': False})
            taxes = product.taxes_id.filtered(lambda tax: tax.company_id == item.merchant_id.website_id.company_id)
            price = item.price
            if taxes:
                unrounded = taxes.with_context(round=False)
                def gross(value):
                    return unrounded.compute_all(value, currency=item.currency_id, quantity=1,
                                                 product=product.product_variant_id)['total_included']
                fixed, one = gross(0), gross(1)
                factor = one - fixed
                if factor <= 0:
                    raise ValidationError('Revisá los impuestos del producto antes de publicarlo.')
                price = (item.price - fixed) / factor
                if price <= 0 or item.currency_id.compare_amounts(gross(price), item.price):
                    raise ValidationError('No se pudo conservar el precio final con los impuestos configurados.')
            product.write({'name': f'{item.name} — {item.presentation}', 'list_price': price, 'description_sale': item.description or item.presentation,
                           'description_ecommerce': False, 'image_1920': item.image,
                           'public_categ_ids': [(6, 0, item.category_id.ids)],
                           'wah_store_id': item.merchant_id.partner_id.id, 'wah_catalog_sample': False,
                           'website_id': item.merchant_id.website_id.id, 'is_published': item.available})
            super(MerchantProduct, item).write({'state': 'approved', 'product_tmpl_id': product.id, 'review_notes': False})
        return True

    def action_reject(self):
        if not is_manager(self.env):
            raise AccessError('La revisión corresponde a la administración.')
        self.check_access('write')
        self.mapped('product_tmpl_id').sudo().write({'is_published': False})
        return super().write({'state': 'rejected'})
