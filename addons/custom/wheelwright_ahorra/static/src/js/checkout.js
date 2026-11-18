/** @odoo-module **/
import { CustomerAddress } from '@portal/interactions/address';
import { patch } from '@web/core/utils/patch';

patch(CustomerAddress.prototype, {
    async saveAddress(ev) {
        if (this.addressForm.classList.contains('wah-checkout')) {
            const invoice = this.addressForm.querySelector('#wah_invoice');
            const vat = this.addressForm.querySelector('#o_vat');
            vat.required = invoice.checked && !vat.readOnly;
            if (invoice.checked) invoice.closest('details').open = true;
        }
        await super.saveAddress(ev);
        for (const field of this.addressForm.querySelectorAll('.is-invalid')) {
            const details = field.closest('details');
            if (details) details.open = true;
        }
    },
    async _onChangeCountry(init = false) {
        if (!this.addressForm.classList.contains('wah-checkout')) {
            return super._onChangeCountry(init);
        }
        // La localidad está fijada por servidor; no reordenar campos ocultos
        // ni convertir los datos fiscales opcionales en campos obligatorios.
        for (const name of ['name', 'phone', 'street']) {
            this._markRequired(name, true);
        }
    },
    _getSelectedCountryCode() {
        if (this.addressForm.classList.contains('wah-checkout')) return 'AR';
        return super._getSelectedCountryCode();
    },
});
