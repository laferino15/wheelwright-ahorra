from datetime import datetime, time

import pytz

from odoo import api, fields, models
from odoo.exceptions import ValidationError

WINDOWS = [('midday', '12:00 a 14:00'), ('afternoon', '17:00 a 20:00'), ('night', '22:00 a 00:00 (del día siguiente)')]
START_HOURS = {'midday': 12, 'afternoon': 17, 'night': 22}
LOCAL_TZ = pytz.timezone('America/Argentina/Buenos_Aires')


class DeliveryWebsite(models.Model):
    _inherit = 'website'

    wah_delivery_windows_enabled = fields.Boolean(string='Entrega con franjas wheel-ahorra', default=False)


class DeliveryOrder(models.Model):
    _inherit = 'sale.order'

    wah_delivery_date = fields.Date(string='Fecha de entrega', copy=False, index=True, tracking=True)
    wah_delivery_window = fields.Selection(WINDOWS, string='Franja de entrega', copy=False, index=True, tracking=True)
    wah_delivery_label = fields.Char(string='Entrega programada', compute='_compute_wah_delivery_label')

    @api.depends('wah_delivery_date', 'wah_delivery_window')
    def _compute_wah_delivery_label(self):
        for order in self:
            order.wah_delivery_label = ('%s · %s' % (order.wah_delivery_date.strftime('%d/%m/%Y'), dict(WINDOWS)[order.wah_delivery_window])) if order.wah_delivery_date and order.wah_delivery_window else False

    @api.model
    def _wah_local_now(self):
        return pytz.UTC.localize(fields.Datetime.now()).astimezone(LOCAL_TZ)

    @api.model
    def _wah_window_is_available(self, day, window):
        if not day or window not in START_HOURS:
            return False
        start = LOCAL_TZ.localize(datetime.combine(day, time(hour=START_HOURS[window])))
        return start > self._wah_local_now()

    def _wah_requires_delivery_window(self):
        self.ensure_one()
        return bool(self.website_id.wah_delivery_windows_enabled and not self.only_services)

    def _wah_has_valid_delivery_window(self):
        self.ensure_one()
        return self._wah_window_is_available(self.wah_delivery_date, self.wah_delivery_window)

    def _wah_check_delivery_window(self):
        for order in self:
            if order._wah_requires_delivery_window() and not order._wah_has_valid_delivery_window():
                raise ValidationError('Elegí una fecha y una franja de entrega que todavía no haya comenzado.')

    @api.constrains('wah_delivery_date', 'wah_delivery_window')
    def _wah_check_schedule_pair(self):
        for order in self:
            if bool(order.wah_delivery_date) != bool(order.wah_delivery_window):
                raise ValidationError('Completá la fecha y la franja de entrega juntas.')

    def action_confirm(self):
        self.filtered(lambda order: order.state in ('draft', 'sent'))._wah_check_delivery_window()
        return super().action_confirm()

    def _check_cart_is_ready_to_be_paid(self):
        self._wah_check_delivery_window()
        return super()._check_cart_is_ready_to_be_paid()


class PreparationWindow(models.Model):
    _inherit = 'wah.preparation'

    wah_delivery_date = fields.Date(related='order_id.wah_delivery_date', readonly=True)
    wah_delivery_window = fields.Selection(related='order_id.wah_delivery_window', readonly=True)
    wah_delivery_label = fields.Char(related='order_id.wah_delivery_label', readonly=True)
