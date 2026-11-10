/* Copyright 2026 Data Dance s.r.o.
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */
import * as Chrome from "@point_of_sale/../tests/tours/utils/chrome_util";
import * as Dialog from "@point_of_sale/../tests/tours/utils/dialog_util";
import * as ProductScreen from "@point_of_sale/../tests/tours/utils/product_screen_util";
import * as PaymentScreen from "@point_of_sale/../tests/tours/utils/payment_screen_util";
import * as ReceiptScreen from "@point_of_sale/../tests/tours/utils/receipt_screen_util";
import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("l10n_sk_pos_cash_limit_tour", {
    steps: () =>
        [
            Chrome.startPoS(),
            Dialog.confirm("Open Register"),
            // 4 000 € in cash: below the limit, no question asked.
            ProductScreen.addOrderline("Strieborná tehla", "1"),
            ProductScreen.clickPayButton(),
            PaymentScreen.clickPaymentMethod("Cash"),
            PaymentScreen.clickValidate(),
            ReceiptScreen.isShown(),
            ReceiptScreen.clickNextOrder(),
            // 6 000 € in cash: the cashier is stopped and may go back.
            ProductScreen.addOrderline("Zlatá tehla", "1"),
            ProductScreen.clickPayButton(),
            PaymentScreen.clickPaymentMethod("Cash"),
            PaymentScreen.clickValidate(),
            // Selectors avoid labels, which a Slovak-loaded database translates.
            {
                content: "the cash limit dialog cites the act",
                trigger: ".modal .modal-body:contains('394/2012')",
            },
            Dialog.confirm(false, ".btn-secondary"),
            PaymentScreen.isShown(),
            // ... and confirm an exemption to go on.
            PaymentScreen.clickValidate(),
            {
                content: "the dialog asks again",
                trigger: ".modal .modal-body:contains('394/2012')",
            },
            Dialog.confirm(false),
            ReceiptScreen.isShown(),
        ].flat(),
});

registry.category("web_tour.tours").add("l10n_sk_pos_cash_limit_same_customer_tour", {
    steps: () =>
        [
            Chrome.startPoS(),
            Dialog.confirm("Open Register"),
            // 4 000 € in cash from a customer: below the limit.
            ProductScreen.addOrderline("Strieborná tehla", "1"),
            ProductScreen.clickPartnerButton(),
            ProductScreen.clickCustomer("Kupec Opakovaný"),
            ProductScreen.clickPayButton(),
            PaymentScreen.clickPaymentMethod("Cash"),
            PaymentScreen.clickValidate(),
            ReceiptScreen.isShown(),
            ReceiptScreen.clickNextOrder(),
            // Another 4 000 € the same day: 8 000 € together (§ 6 ods. 2).
            ProductScreen.addOrderline("Strieborná tehla", "1"),
            ProductScreen.clickPartnerButton(),
            ProductScreen.clickCustomer("Kupec Opakovaný"),
            ProductScreen.clickPayButton(),
            PaymentScreen.clickPaymentMethod("Cash"),
            PaymentScreen.clickValidate(),
            {
                content: "the dialog adds the customer's earlier cash",
                trigger: ".modal .modal-body:contains('§ 6 ods. 2')",
            },
            Dialog.confirm(false),
            ReceiptScreen.isShown(),
        ].flat(),
});
