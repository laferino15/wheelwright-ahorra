from odoo import http
from odoo.http import request


class Offers(http.Controller):
    @http.route('/ofertas', type='http', auth='public', website=True, sitemap=True)
    def offers(self, **kwargs):
        return request.render('wheelwright_ahorra.offers_page', {
            'offer_cards': request.website._wah_offer_cards(),
        })
