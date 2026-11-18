import math

from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.l10n_ar.controllers.portal import L10nARPortalAccount


class LocalCheckout(WebsiteSale):
    def _wah_local(self):
        return bool(request.website.wah_local_checkout and request.httprequest.path.startswith('/shop/'))

    def _get_default_country(self, **kwargs):
        if self._wah_local():
            return request.env.ref('base.ar')
        return super()._get_default_country(**kwargs)

    def _prepare_address_form_values(self, partner_sudo, *args, **kwargs):
        values = super()._prepare_address_form_values(partner_sudo, *args, **kwargs)
        if self._wah_local():
            country = request.env.ref('base.ar')
            state = request.env['res.country.state'].sudo().search([
                ('country_id', '=', country.id), ('name', '=', 'Santa Fe')], limit=1)
            values.update(wah_country=country, wah_state=state)
        return values

    def _create_or_update_address(self, partner_sudo, **kwargs):
        if not self._wah_local():
            return super()._create_or_update_address(partner_sudo, **kwargs)
        country = request.env.ref('base.ar')
        state = request.env['res.country.state'].sudo().search([
            ('country_id', '=', country.id), ('name', '=', 'Santa Fe')], limit=1)
        # La zona de entrega del piloto se establece también del lado servidor.
        kwargs.update(city='Wheelwright', zip='2722', country_id=str(country.id), state_id=str(state.id))
        invoice = kwargs.get('wah_invoice') == '1'
        if not invoice and not partner_sudo:
            kwargs.update(
                l10n_ar_afip_responsibility_type_id=str(request.env.ref('l10n_ar.res_CF').id),
                l10n_latam_identification_type_id=str(request.env.ref('l10n_ar.it_Sigd').id),
                vat='', company_name='',
            )
        raw_cash = (kwargs.get('wah_cash_tendered') or '').strip()
        try:
            cash = float(raw_cash.replace(',', '.')) if raw_cash else 0.0
            if not math.isfinite(cash) or cash < 0:
                raise ValueError()
            if cash and request.cart.currency_id.compare_amounts(cash, request.cart.amount_total) < 0:
                return partner_sudo, {'invalid_fields': ['wah_cash_tendered'], 'messages': ['El efectivo indicado debe alcanzar el total del pedido.']}
        except (ValueError, TypeError):
            return partner_sudo, {'invalid_fields': ['wah_cash_tendered'], 'messages': ['Indicá un importe válido para preparar el cambio.']}
        notes = (kwargs.get('wah_delivery_notes') or '').strip()
        if len(notes) > 1000:
            return partner_sudo, {'invalid_fields': ['wah_delivery_notes'], 'messages': ['Las observaciones pueden tener hasta 1000 caracteres.']}
        partner, feedback = super()._create_or_update_address(partner_sudo, **kwargs)
        if not partner and not feedback.get('redirectUrl'):
            # El controlador nativo detiene el avance usando invalid_fields.
            # Asegurar que un error de validación sin campos no avance con partner vacío.
            feedback['invalid_fields'] = feedback.get('invalid_fields') or ['name']
        if not feedback.get('invalid_fields') and not feedback.get('messages'):
            request.cart.sudo().write({
                'wah_delivery_notes': notes,
                'wah_cash_tendered': cash,
                'wah_invoice_requested': invoice,
            })
        return partner, feedback


class LocalAddressRules(L10nARPortalAccount):
    def _wah_local(self):
        return bool(request.website.wah_local_checkout and request.httprequest.path.startswith('/shop/'))

    def _get_mandatory_billing_address_fields(self, country_sudo):
        required = super()._get_mandatory_billing_address_fields(country_sudo)
        if self._wah_local():
            required.discard('email')
            if request.params.get('wah_invoice') != '1':
                required.discard('vat')
        return required

    def _get_mandatory_delivery_address_fields(self, country_sudo):
        required = super()._get_mandatory_delivery_address_fields(country_sudo)
        if self._wah_local():
            required.discard('email')
        return required
