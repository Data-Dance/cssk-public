/* Copyright 2026 Data Dance s.r.o.
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ask } from "@point_of_sale/app/utils/make_awaitable_dialog";

// § 4 ods. 1 zákona č. 394/2012 Z. z.; the 15 000 € limit of ods. 2 is only
// between individuals not in business, so it never applies to a till.
export const CASH_PAYMENT_LIMIT = 5000;

patch(PaymentScreen.prototype, {
    l10nSkCashTendered() {
        const order = this.currentOrder;
        const cash = order.payment_ids
            .filter((line) => line.payment_method_id.is_cash_count)
            .reduce((total, line) => total + line.getAmount(), 0);
        // Change goes back in cash, so only the net amount changes hands.
        return Math.abs(cash - (order.change > 0 ? order.change : 0));
    },
    l10nSkOverCashLimit() {
        const company = this.pos.company;
        if ((company.account_fiscal_country_id || company.country_id)?.code !== "SK") {
            return false;
        }
        if (this.pos.currency.name !== "EUR") {
            return false; // the back office converts and warns on the order
        }
        return this.l10nSkCashTendered() - CASH_PAYMENT_LIMIT > this.pos.currency.rounding / 2;
    },
    async validateOrder(isForceValidate) {
        if (this.l10nSkOverCashLimit()) {
            const confirmed = await ask(this.dialog, {
                title: _t("Cash payment limit"),
                body: _t(
                    "This order takes %s in cash, above the 5 000 € limit of § 4 zákona č. 394/2012 Z. z. Continue only if an exemption under § 8 applies; otherwise take the rest by card or transfer.",
                    this.env.utils.formatCurrency(this.l10nSkCashTendered())
                ),
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
