from odoo import http


class WheelwrightController(http.Controller):

    @http.route('/ahorra', type='http', auth='public', website=True)
    def home(self, **kw):
        # La portada principal es /. Se conserva /ahorra como alias.
        return http.request.redirect('/')
