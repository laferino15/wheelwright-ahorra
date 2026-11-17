from datetime import date

from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
from odoo.addons.website_sale.controllers.main import WebsiteSale

from ..models.delivery_windows import WINDOWS


class ScheduledCheckout(WebsiteSale):
    @http.route()
    def shop_payment(self, **post):
        order = request.cart
        if order and order.state in ('draft', 'sent'):
            if redirect := self._check_cart_and_addresses(order):
                return redirect
            if order._wah_requires_delivery_window() and not order._wah_has_valid_delivery_window():
                return request.redirect('/shop/entrega')
        return super().shop_payment(**post)

    @http.route('/shop/entrega', type='http', auth='public', website=True, sitemap=False, methods=['GET', 'POST'])
    def delivery_window(self, **post):
        order = request.cart
        if not order or not order.order_line or order.state not in ('draft', 'sent'):
            return request.redirect('/shop/cart')
        if redirect := self._check_cart_and_addresses(order):
            return redirect
        if not order._wah_requires_delivery_window():
            return request.redirect('/shop/payment')
        if request.httprequest.method == 'POST':
            request.env.cr.execute('SELECT id FROM sale_order WHERE id=%s FOR UPDATE', (order.id,))
            order.invalidate_recordset(['state', 'wah_delivery_date', 'wah_delivery_window'])
            if order.state not in ('draft', 'sent'):
                return request.redirect('/shop/cart')
        today = order._wah_local_now().date()
        error = False
        day = order.wah_delivery_date if order.wah_delivery_date and order.wah_delivery_date >= today else today
        raw_date = post.get('delivery_date')
        if raw_date:
            try:
                day = date.fromisoformat(raw_date)
                if raw_date != day.isoformat() or day < today:
                    raise ValueError()
            except (ValueError, TypeError):
                day = today
                error = 'Elegí una fecha válida a partir de hoy.'
        selected = post.get('delivery_window', order.wah_delivery_window or '')
        if request.httprequest.method == 'POST' and post.get('action') != 'refresh':
            if not raw_date:
                error = 'Elegí la fecha de entrega.'
            if not error and not order._wah_window_is_available(day, selected):
                error = 'Esa franja no está disponible. Elegí una que todavía no haya comenzado.'
            if not error:
                try:
                    with request.env.cr.savepoint():
                        # El carrito de la sesión es la única orden editable por esta ruta.
                        order.sudo().write({'wah_delivery_date': day, 'wah_delivery_window': selected})
                    return request.redirect('/shop/payment')
                except UserError as exc:
                    error = str(exc)
        windows = [(key, label, order._wah_window_is_available(day, key)) for key, label in WINDOWS]
        return request.render('wheelwright_ahorra.delivery_window_checkout', {
            'website_sale_order': order, 'day': day.isoformat(), 'today': today.isoformat(),
            'windows': windows, 'has_windows': any(item[2] for item in windows), 'day_label': day.strftime('%d/%m/%Y'),
            'selected': selected, 'error': error,
        })
