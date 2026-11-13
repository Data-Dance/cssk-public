/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

// 17.0: the receipt component only receives `props.data`, the object built by
// `export_for_printing`. The EET fields the receipt prints therefore travel
// inside that object.
patch(Order.prototype, {
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        // Set by `pos.order._export_for_ui` on orders reloaded from the server
        // (ticket screen, reprint).
        this.l10n_cz_eet2_pok = json.l10n_cz_eet2_pok || false;
        this.l10n_cz_eet2_state = json.l10n_cz_eet2_state || false;
        this.l10n_cz_eet2_is_test = Boolean(json.l10n_cz_eet2_is_test);
    },
    wait_for_push_order() {
        // 17.0 calls `PaymentScreen._postPushOrderResolve` (where the POK is
        // fetched) only for orders that ask to wait for the push.
        return this.pos.config.l10n_cz_eet2_enabled
            ? true
            : super.wait_for_push_order(...arguments);
    },
    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        // Same test as the backend: contact lines that net to zero (change, an
        // even exchange) register nothing, so they announce nothing.
        const contactTotal = this.get_paymentlines()
            .filter((p) => p.payment_method?.l10n_cz_eet2_contact_payment)
            .reduce((sum, p) => sum + p.get_amount(), 0);
        result.l10n_cz_eet2 = {
            pok: this.l10n_cz_eet2_pok || false,
            state: this.l10n_cz_eet2_state || false,
            is_test: Boolean(this.l10n_cz_eet2_is_test),
            contact:
                Boolean(this.pos.config.l10n_cz_eet2_enabled) && Math.abs(contactTotal) >= 0.005,
        };
        return result;
    },
});
