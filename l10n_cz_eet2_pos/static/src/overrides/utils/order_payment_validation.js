import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

// NOTE (18.0 port): 19.0 extracted the payment-validation flow into a standalone
// `OrderPaymentValidation` utility class with a `beforePostPushOrderResolve` hook.
// 18.0 still keeps that logic inside the `PaymentScreen` component, where the
// equivalent post-push hook is `_postPushOrderResolve(order, order_server_ids)`
// (invoked from `postPushOrderResolve` after the order has been synced to the
// server, i.e. after EET registration ran server-side in `_process_order`).
patch(PaymentScreen.prototype, {
    /**
     * After the order has been pushed to the server (so it exists and has been
     * registered with EET 2.0 in `_process_order`), synchronously fetch the POK
     * and attach it to the local order, blocking the UI until it arrives so the
     * receipt can print it. Failures never block the sale.
     */
    async _postPushOrderResolve(order, order_server_ids) {
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
        return super._postPushOrderResolve(...arguments);
    },
});
