/* Copyright 2026 Data Dance s.r.o.
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */
import { _t } from "@web/core/l10n/translation";
import { formatCurrency } from "@web/core/currency";
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ask } from "@point_of_sale/app/utils/make_awaitable_dialog";

// § 4 ods. 1 zákona č. 394/2012 Z. z.; the 15 000 € limit of ods. 2 is only
// between individuals not in business, so it never applies to a till.
// The server sends the limit and the rate of the day before (§ 6 ods. 1) as
// `_l10n_sk_cash_limit` and `_l10n_sk_cash_rate` (company currency per unit
// of the till's currency; false outside Slovakia or when no rate is known).

patch(PaymentScreen.prototype, {
    l10nSkCashTendered() {
        const order = this.currentOrder;
        const cash = order.payment_ids
            .filter((line) => line.payment_method_id.is_cash_count)
            .reduce((total, line) => total + line.getAmount(), 0);
        // Change goes back in cash, so only the net amount changes hands.
        return Math.abs(cash - (order.change > 0 ? order.change : 0));
    },
    async l10nSkCashToday() {
        // § 6 ods. 2: the same customer's cash orders of the day may be parts
        // of one purchase. Offline, the till checks this order alone.
        const partner = this.currentOrder.getPartner();
        if (!partner) {
            return 0;
        }
        try {
            return await this.pos.data.call("pos.order", "l10n_sk_cash_paid_today", [
                partner.id,
                this.pos.config.id,
            ]);
        } catch {
            return 0;
        }
    },
    async l10nSkCashLimitCheck() {
        const rate = this.pos.config._l10n_sk_cash_rate;
        const limit = this.pos.config._l10n_sk_cash_limit;
        if (!rate || !limit) {
            return null;
        }
        const tendered = this.l10nSkCashTendered() * rate;
        if (!tendered) {
            return null;
        }
        // A refund paid out stands on its own; only payments in add up.
        const earlier = this.currentOrder.isRefund ? 0 : await this.l10nSkCashToday();
        const total = tendered + earlier;
        return total - limit > 0.005 ? { tendered, earlier, total } : null;
    },
    async validateOrder(isForceValidate) {
        const over = await this.l10nSkCashLimitCheck();
        if (over) {
            // Amounts are in company currency, which is what the limit is in.
            const euro = (amount) => formatCurrency(amount, this.pos.company.currency_id?.id);
            const body = over.earlier
                ? _t(
                      "This order takes %(cash)s in cash and the customer already paid %(earlier)s in cash today, %(total)s together, above the 5 000 € limit of § 4 zákona č. 394/2012 Z. z. Payments for one purchase are added together (§ 6 ods. 2). Continue only if these are separate purchases or an exemption under § 8 applies; otherwise take the rest by card or transfer.",
                      { cash: euro(over.tendered), earlier: euro(over.earlier), total: euro(over.total) }
                  )
                : _t(
                      "This order takes %s in cash, above the 5 000 € limit of § 4 zákona č. 394/2012 Z. z. Continue only if an exemption under § 8 applies; otherwise take the rest by card or transfer.",
                      euro(over.total)
                  );
            const confirmed = await ask(this.dialog, {
                title: _t("Cash payment limit"),
                body,
                confirmLabel: _t("Continue"),
                cancelLabel: _t("Back"),
            });
            if (!confirmed) {
                return;
            }
        }
        return super.validateOrder(...arguments);
    },
});
