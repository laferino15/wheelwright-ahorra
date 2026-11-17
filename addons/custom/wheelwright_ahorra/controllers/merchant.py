import base64

from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError, UserError
from odoo.tools.image import image_data_uri
from odoo.addons.portal.controllers.portal import pager as portal_pager


class MerchantPortal(http.Controller):
    def _preparation(self, preparation_id):
        preparation = request.env['wah.preparation'].search([
            ('id', '=', preparation_id), ('merchant_id.owner_id', '=', request.env.uid),
            ('website_id', '=', request.website.id)], limit=1)
        if not preparation:
            raise NotFound()
        return preparation

    @http.route('/mi-comercio/pedidos', type='http', auth='user', website=True, methods=['GET'])
    def preparations(self, status='open', page=1, **kw):
        store = self._store()
        if not store:
            return request.redirect('/mi-comercio/registro')
        status = status if status in ('open', 'closed', 'all') else 'open'
        try:
            page = max(1, int(page))
        except (ValueError, TypeError):
            page = 1
        domain = [('merchant_id', '=', store.id), ('website_id', '=', request.website.id)]
        if status == 'open':
            domain.append(('state', 'not in', ['delivered', 'cancelled']))
        elif status == 'closed':
            domain.append(('state', 'in', ['delivered', 'cancelled']))
        model = request.env['wah.preparation']
        pager = portal_pager('/mi-comercio/pedidos', total=model.search_count(domain), page=page,
                             step=20, url_args={'status': status})
        return request.render('wheelwright_ahorra.merchant_preparations', {
            'store': store, 'preparations': model.search(domain, limit=20, offset=pager['offset']),
            'pager': pager, 'status': status, 'page_name': 'merchant_preparations',
        })

    @http.route('/mi-comercio/pedidos/<int:preparation_id>', type='http', auth='user', website=True, methods=['GET'])
    def preparation(self, preparation_id, **kw):
        preparation = self._preparation(preparation_id)
        return request.render('wheelwright_ahorra.merchant_preparation_detail', {
            'preparation': preparation, 'page_name': 'merchant_preparations',
            'updated': kw.get('updated') == '1', 'error': False,
        })

    @http.route('/mi-comercio/pedidos/<int:preparation_id>/actualizar', type='http', auth='user',
                website=True, methods=['POST'])
    def update_preparation(self, preparation_id, **post):
        preparation = self._preparation(preparation_id)
        try:
            with request.env.cr.savepoint():
                action = post.get('action')
                if action == 'start':
                    preparation.action_start()
                elif action == 'ready':
                    preparation.action_ready()
                elif action == 'note':
                    preparation.action_save_note(post.get('merchant_note') or '')
                else:
                    raise ValidationError('Elegí una acción válida para tu preparación.')
            return request.redirect('/mi-comercio/pedidos/%s?updated=1' % preparation.id)
        except (UserError, AccessError) as error:
            return request.render('wheelwright_ahorra.merchant_preparation_detail', {
                'preparation': preparation, 'page_name': 'merchant_preparations',
                'updated': False, 'error': str(error),
            })

    def _store(self):
        return request.env['wah.merchant'].search([
            ('owner_id', '=', request.env.uid), ('website_id', '=', request.website.id)], limit=1)

    def _categories(self):
        # Solo nombres de categorías del sitio; no se elevan escrituras del dueño.
        return request.env['product.public.category'].sudo().search([
            ('parent_id', '=', False), ('website_id', 'in', [False, request.website.id])], order='sequence, name')

    def _upload(self, name):
        file = request.httprequest.files.get(name)
        if not file or not file.filename:
            return None
        content = file.read(5 * 1024 * 1024 + 1)
        if len(content) > 5 * 1024 * 1024:
            raise ValidationError('La imagen puede tener hasta 5 MB.')
        if file.mimetype not in ('image/jpeg', 'image/png', 'image/webp'):
            raise ValidationError('Usá una imagen JPG, PNG o WebP.')
        return base64.b64encode(content)

    def _category(self, value):
        try:
            category_id = int(value)
        except (TypeError, ValueError):
            raise ValidationError('Elegí una categoría.')
        if category_id not in self._categories().ids:
            raise ValidationError('La categoría no corresponde a este sitio.')
        return category_id

    def _render_store(self, store=False, error=False, values=None):
        return request.render('wheelwright_ahorra.merchant_register', {
            'store': store, 'categories': self._categories(), 'error': error,
            'values': values or {}, 'page_name': 'merchant',
            'logo_src': image_data_uri(store.logo) if store and store.logo else False,
        })

    def _product(self, product_id):
        product = request.env['wah.merchant.product'].search([
            ('id', '=', product_id), ('merchant_id.owner_id', '=', request.env.uid),
            ('merchant_id.website_id', '=', request.website.id)], limit=1)
        if not product:
            raise NotFound()
        return product

    @http.route('/vender', type='http', auth='public', website=True, methods=['GET'])
    def sell(self):
        return request.render('wheelwright_ahorra.merchant_landing')

    @http.route('/mi-comercio', type='http', auth='user', website=True, methods=['GET'])
    def home(self, **kw):
        store = self._store()
        if not store:
            return request.redirect('/mi-comercio/registro')
        products = request.env['wah.merchant.product'].search([('merchant_id', '=', store.id)])
        return request.render('wheelwright_ahorra.merchant_dashboard', {
            'store': store, 'products': products, 'page_name': 'merchant',
            'notice': {'saved': 'Los cambios se guardaron. Revisá el producto y envialo a revisión.',
                       'stock': 'Se actualizaron el stock y la disponibilidad del producto.',
                       'submitted': 'El producto fue enviado a revisión.'}.get(kw.get('notice')),
        })

    @http.route('/mi-comercio/registro', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def register(self, **post):
        store = self._store()
        if request.httprequest.method == 'POST':
            try:
                vals = {key: (post.get(key) or '').strip() for key in ['name', 'street', 'phone', 'hours', 'description']}
                if any(len(value) > (2000 if key == 'description' else 200) for key, value in vals.items()):
                    raise ValidationError('Revisá la longitud de los datos del local.')
                vals['category_id'] = self._category(post.get('category_id'))
                logo = self._upload('logo')
                if logo:
                    vals['logo'] = logo
                with request.env.cr.savepoint():
                    if store:
                        store.write(vals)
                    else:
                        request.env['wah.merchant'].create(vals)
                return request.redirect('/mi-comercio')
            except (UserError, AccessError) as error:
                return self._render_store(store, str(error), post)
        return self._render_store(store)

    def _render_product(self, store, product=False, error=False, values=None):
        return request.render('wheelwright_ahorra.merchant_product_form', {
            'store': store, 'product': product, 'error': error, 'values': values or {},
            'categories': self._categories(), 'page_name': 'merchant',
            'image_src': image_data_uri(product.image) if product and product.image else False,
        })

    @http.route(['/mi-comercio/productos/nuevo', '/mi-comercio/productos/<int:product_id>'],
                type='http', auth='user', website=True, methods=['GET', 'POST'])
    def product(self, product_id=None, **post):
        product = self._product(product_id) if product_id else False
        store = self._store()
        if not store or store.state != 'approved':
            return request.redirect('/mi-comercio')
        if request.httprequest.method == 'POST':
            original_product = product
            try:
                vals = {key: (post.get(key) or '').strip() for key in ['name', 'presentation', 'description']}
                if len(vals['name']) > 200 or len(vals['presentation']) > 200 or len(vals['description']) > 4000:
                    raise ValidationError('Revisá la longitud del nombre o la descripción.')
                try:
                    vals['price'] = float((post.get('price') or '').replace(',', '.'))
                except ValueError:
                    raise ValidationError('Ingresá un precio válido.')
                vals['category_id'] = self._category(post.get('category_id'))
                vals['available'] = post.get('available') == '1'
                vals['stock_tracking'] = post.get('stock_tracking') == '1'
                try:
                    vals['stock_quantity'] = float((post.get('stock_quantity') or '0').replace(',', '.'))
                except ValueError:
                    raise ValidationError('Ingresá una cantidad disponible válida.')
                image = self._upload('image')
                if image:
                    vals['image'] = image
                with request.env.cr.savepoint():
                    if product:
                        product.write(vals)
                    else:
                        vals['merchant_id'] = store.id
                        product = request.env['wah.merchant.product'].create(vals)
                    if post.get('intent') == 'submit':
                        product.action_submit()
                notice = 'submitted' if post.get('intent') == 'submit' else 'saved'
                return request.redirect('/mi-comercio?notice=' + notice)
            except (UserError, AccessError) as error:
                return self._render_product(store, original_product, str(error), post)
        return self._render_product(store, product)

    @http.route('/mi-comercio/productos/<int:product_id>/enviar', type='http', auth='user',
                website=True, methods=['POST'])
    def submit(self, product_id):
        product = self._product(product_id)
        try:
            with request.env.cr.savepoint():
                product.action_submit()
            return request.redirect('/mi-comercio?notice=submitted')
        except (UserError, AccessError) as error:
            return self._render_product(self._store(), product, str(error))

    @http.route('/mi-comercio/productos/<int:product_id>/stock', type='http', auth='user',
                website=True, methods=['GET', 'POST'])
    def stock(self, product_id, **post):
        product = self._product(product_id)
        error = False
        if request.httprequest.method == 'POST':
            try:
                with request.env.cr.savepoint():
                    product.action_update_stock(post.get('stock_tracking') == '1',
                                                (post.get('stock_quantity') or '0').replace(',', '.'),
                                                post.get('available') == '1')
                return request.redirect('/mi-comercio?notice=stock')
            except (UserError, AccessError) as exc:
                error = str(exc)
        return request.render('wheelwright_ahorra.merchant_stock_form', {
            'product': product, 'store': self._store(), 'error': error,
            'values': post if error else {}, 'page_name': 'merchant',
        })
