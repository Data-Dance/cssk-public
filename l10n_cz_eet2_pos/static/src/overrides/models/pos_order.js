import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

// 18.0: the receipt component only receives `props.data`, the object built by
// `export_for_printing` (19.0 hands it the order itself). The EET fields the
// receipt prints therefore travel inside that object.
patch(PosOrder.prototype, {
    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(...arguments);
        // Same test as the backend: contact lines that net to zero (change, an
        // even exchange) register nothing, so they announce nothing.
        const contactTotal = this.payment_ids
            .filter((p) => p.payment_method_id?.l10n_cz_eet2_contact_payment)
            .reduce((sum, p) => sum + p.amount, 0);
        result.l10n_cz_eet2 = {
            pok: this.l10n_cz_eet2_pok || false,
            state: this.l10n_cz_eet2_state || false,
            is_test: Boolean(this.l10n_cz_eet2_is_test),
            contact: Boolean(this.config?.l10n_cz_eet2_enabled) && Math.abs(contactTotal) >= 0.005,
        };
        return result;
    },
});
