"""La falta del generador PDF no debe impedir confirmar una compra web."""
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _send_order_notification_mail(self, mail_template, allow_deferred_sending=True):
        self.ensure_one()
        order = self
        if self.website_id and self.env['ir.actions.report'].get_wkhtmltopdf_state() == 'install':
            order = self.with_context(wah_optional_order_pdf=True)
        return super(SaleOrder, order)._send_order_notification_mail(
            mail_template, allow_deferred_sending=allow_deferred_sending)


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    def _generate_template_attachments(self, res_ids, render_fields, render_results=None):
        self.ensure_one()
        skip_pdf = (
            self.env.context.get('wah_optional_order_pdf')
            and self.model == 'sale.order'
            and 'report_template_ids' in render_fields
            and self.report_template_ids
            and all(report.report_type in ('qweb-html', 'qweb-pdf') for report in self.report_template_ids)
            and self.env['ir.actions.report'].get_wkhtmltopdf_state() == 'install'
        )
        if skip_pdf:
            render_fields = [name for name in render_fields if name != 'report_template_ids']
            _logger.warning('Confirmación web sin PDF adjunto: wkhtmltopdf no está instalado; plantilla %s.', self.id)
        result = super()._generate_template_attachments(res_ids, render_fields, render_results=render_results)
        if skip_pdf:
            for record_id in res_ids:
                result.setdefault(record_id, {}).setdefault('attachments', [])
        return result
