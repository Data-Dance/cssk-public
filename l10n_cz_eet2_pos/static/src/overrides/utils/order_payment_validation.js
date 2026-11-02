import OrderPaymentValidation from "@point_of_sale/app/utils/order_payment_validation";
import { patch } from "@web/core/utils/patch";

patch(OrderPaymentValidation.prototype, {
    /**
     * After the order has been pushed to the server (so it exists and has been
     * registered with EET 2.0 in `_process_order`), synchronously fetch the POK
     * and attach it to the local order, blocking the UI until it arrives so the
     * receipt can print it. Failures never block the sale.
     */
    async beforePostPushOrderResolve(order, order_server_ids) {
        if (this.pos.config.l10n_cz_eet2_enabled && order_server_ids?.length) {
            this.pos.env.services.ui.block();
            try {
                const data = await this.pos.data.call(
                    "pos.order",
                    "get_l10n_cz_eet2_pos_data",
                    [order_server_ids],
                    {}
                );
                order.l10n_cz_eet2_pok = data.l10n_cz_eet2_pok;
                order.l10n_cz_eet2_state = data.l10n_cz_eet2_state;
                order.l10n_cz_eet2_is_test = data.l10n_cz_eet2_is_test;
            } catch (error) {
                // EET registration must not block the sale; it can be resent later.
                console.warn("EET 2.0 registration failed:", error);
            } finally {
                this.pos.env.services.ui.unblock();
            }
        }
        return super.beforePostPushOrderResolve(...arguments);
    },
});
