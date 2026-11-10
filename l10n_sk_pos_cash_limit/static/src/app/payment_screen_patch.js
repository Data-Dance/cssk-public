/* Copyright 2026 Data Dance s.r.o.
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */
import { _t } from "@web/core/l10n/translation";
import { formatCurrency } from "@web/core/currency";
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ask } from "@point_of_sale/app/store/make_awaitable_dialog";

// § 4 ods. 1 zákona č. 394/2012 Z. z.; the 15 000 € limit of ods. 2 is only
// between individuals not in business, so it never applies to a till.
export const CASH_PAYMENT_LIMIT = 5000;

patch(PaymentScreen.prototype, {
    l10nSkCashTendered() {
        const order = this.currentOrder;
        const cash = order.payment_ids
            .filter((line) => line.payment_method_id.is_cash_count)
            .reduce((total, line) => total + line.get_amount(), 0);
        // Change goes back in cash, so only the net amount changes hands.
        const change = order.get_change();
        return Math.abs(cash - (change > 0 ? change : 0));
    },
    async l10nSkCashContext() {
        // The server knows the rate of the day before (§ 6 ods. 1) and the
        // customer's cash of the day (§ 6 ods. 2). Offline, a euro till
        // checks this order alone; any other till cannot convert and skips.
        const partner = this.currentOrder.get_partner();
        try {
            return await this.pos.data.call("pos.config", "l10n_sk_cash_limit_context", [
                [this.pos.config.id],
                partner && !this.currentOrder._isRefundOrder() ? partner.id : false,
            ]);
        } catch {
            const company = this.pos.company;
            const slovak = (company.account_fiscal_country_id || company.country_id)?.code === "SK";
            return slovak && this.pos.currency.name === "EUR"
                ? { rate: 1, limit: CASH_PAYMENT_LIMIT, earlier: 0 }
                : { rate: false };
        }
    },
    async l10nSkCashLimitCheck() {
        const cash = this.l10nSkCashTendered();
        if (!cash) {
            return null;
        }
        const { rate, limit, earlier } = await this.l10nSkCashContext();
        if (!rate || !limit) {
            return null;
        }
        const tendered = cash * rate;
        const total = tendered + (earlier || 0);
        return total - limit > 0.005 ? { tendered, earlier: earlier || 0, total } : null;
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
