from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, UserError, ValidationError
from werkzeug.exceptions import NotFound
from odoo.addons.portal.controllers.portal import pager as portal_pager
from .merchant import MerchantPortal
from odoo.addons.portal.controllers.portal import CustomerPortal


class MerchantPickup(MerchantPortal):
    def _pickup_info(self, prep):
        order = prep.sudo().order_id
        courier = order.wah_courier_id
        return {'courier': courier.name if courier and courier.active else False,
                'phone': courier.phone if courier and courier.active else False,
                'assigned': order.wah_route_state == 'assigned' and bool(courier and courier.active)}

    @http.route()
    def preparation(self, preparation_id, **kw):
        prep = self._preparation(preparation_id)
        return request.render('wheelwright_ahorra.merchant_preparation_detail', {
            'preparation': prep, 'page_name': 'merchant_preparations', 'pickup_info': self._pickup_info(prep),
            'updated': kw.get('updated') == '1', 'error': False})

    @http.route('/mi-comercio/pedidos/<int:preparation_id>/retiro', type='http', auth='user', website=True, methods=['POST'])
    def pickup(self, preparation_id, action=None, **post):
        prep = self._preparation(preparation_id)
        try:
            with request.env.cr.savepoint():
                if action == 'request':
                    prep.action_request_pickup()
                elif action == 'handoff':
                    prep.action_merchant_handoff()
                else:
                    raise ValidationError('Elegí una acción válida para el retiro.')
            return request.redirect('/mi-comercio/pedidos/%s?updated=1' % prep.id)
        except (UserError, AccessError) as error:
            return request.render('wheelwright_ahorra.merchant_preparation_detail', {
                'preparation': prep, 'page_name': 'merchant_preparations', 'pickup_info': self._pickup_info(prep),
                'updated': False, 'error': str(error)})

    @http.route()
    def update_preparation(self, preparation_id, **post):
        response = super().update_preparation(preparation_id, **post)
        if getattr(response, 'qcontext', None) is not None:
            prep = self._preparation(preparation_id)
            response.qcontext['pickup_info'] = self._pickup_info(prep)
        return response


class CourierAccountHome(CustomerPortal):
    @http.route()
    def home(self, **kw):
        if request.env['wah.courier'].sudo().search_count([
                ('user_id', '=', request.env.uid), ('active', '=', True)]):
            return request.redirect('/mi-reparto')
        if request.env['wah.merchant'].search_count([
                ('owner_id', '=', request.env.uid), ('website_id', '=', request.website.id)]):
            return request.redirect('/mi-comercio')
        return super().home(**kw)


class CourierPortal(http.Controller):
    def _order(self, order_id):
        order = request.env['sale.order'].sudo().search([
            ('id', '=', order_id), ('website_id', '=', request.website.id),
            ('company_id', '=', request.website.company_id.id), ('state', '=', 'sale'),
            ('wah_courier_id.user_id', '=', request.env.uid), ('wah_courier_id.active', '=', True),
            ('wah_route_state', '!=', 'cancelled')], limit=1)
        if not order:
            raise NotFound()
        return order

    @http.route('/mi-reparto', type='http', auth='user', website=True, methods=['GET'])
    def routes(self, status='open', page=1, **kw):
        status = status if status in ('open', 'closed', 'all') else 'open'
        try:
            page = max(1, int(page))
        except (TypeError, ValueError):
            page = 1
        domain = [('website_id', '=', request.website.id), ('company_id', '=', request.website.company_id.id),
                  ('state', '=', 'sale'), ('wah_courier_id.user_id', '=', request.env.uid),
                  ('wah_courier_id.active', '=', True), ('wah_route_state', 'in', ['assigned', 'on_way', 'delivered'])]
        courier = request.env['wah.courier'].sudo().search([
            ('user_id', '=', request.env.uid), ('active', '=', True)], limit=1)
        if not courier:
            raise NotFound()
        orders = request.env['sale.order'].sudo()
        metrics = {
            'assigned': orders.search_count(domain + [('wah_route_state', '=', 'assigned')]),
            'on_way': orders.search_count(domain + [('wah_route_state', '=', 'on_way')]),
            'pending': orders.search_count(domain + [('wah_route_state', '=', 'delivered'), ('wah_collection_state', '=', 'pending')]),
        }
        if status == 'open':
            domain += ['|', ('wah_route_state', '!=', 'delivered'), ('wah_collection_state', '=', 'pending')]
        elif status == 'closed':
            domain += [('wah_route_state', '=', 'delivered'), ('wah_collection_state', '!=', 'pending')]
        orders = request.env['sale.order'].sudo()
        pager = portal_pager('/mi-reparto', total=orders.search_count(domain), page=page, step=20, url_args={'status': status})
        records = orders.search(domain, order='wah_delivery_date, id', limit=20, offset=pager['offset'])
        return request.render('wheelwright_ahorra.courier_routes', {
            'routes': [o._wah_courier_summary(request.website) for o in records],
            'pager': pager, 'status': status, 'metrics': metrics, 'courier_name': courier.name, 'page_name': 'courier_routes'})

    @http.route('/mi-reparto/<int:order_id>', type='http', auth='user', website=True, methods=['GET'])
    def route(self, order_id, **kw):
        order = self._order(order_id)
        return request.render('wheelwright_ahorra.courier_route_detail', {
            'route': order._wah_courier_summary(request.website, detail=True), 'error': False,
            'updated': kw.get('updated') == '1', 'page_name': 'courier_routes'})

    @http.route('/mi-reparto/<int:order_id>/actualizar', type='http', auth='user', website=True, methods=['POST'])
    def update(self, order_id, action=None, **post):
        order = self._order(order_id)
        try:
            with request.env.cr.savepoint():
                try:
                    prep_id = int(post.get('preparation_id') or 0)
                    received = float(post.get('received_amount') or 0)
                except (TypeError, ValueError):
                    raise ValidationError('Revisá la preparación y el efectivo recibido.')
                order._wah_courier_action(request.website, action, preparation_id=prep_id,
                    method=post.get('method'), received=received, reference=post.get('reference') or '')
            return request.redirect('/mi-reparto/%s?updated=1' % order.id)
        except (UserError, AccessError) as error:
            return request.render('wheelwright_ahorra.courier_route_detail', {
                'route': order._wah_courier_summary(request.website, detail=True),
                'error': str(error), 'updated': False, 'page_name': 'courier_routes'})
