import * as Chrome from "@point_of_sale/../tests/pos/tours/utils/chrome_util";
import * as Dialog from "@point_of_sale/../tests/generic_helpers/dialog_util";
import * as ProductScreen from "@point_of_sale/../tests/pos/tours/utils/product_screen_util";
import * as PaymentScreen from "@point_of_sale/../tests/pos/tours/utils/payment_screen_util";
import * as ReceiptScreen from "@point_of_sale/../tests/pos/tours/utils/receipt_screen_util";
import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("pos_vrp2_receipt_tour", {
    steps: () =>
        [
            Chrome.startPoS(),
            Dialog.confirm("Open Register"),
            ProductScreen.addOrderline("Káva A 250g", "1"),
            ProductScreen.addOrderline("Káva B 250g", "1"),
            ProductScreen.clickPayButton(),
            PaymentScreen.clickPaymentMethod("Cash"),
            PaymentScreen.clickValidate(),
            ReceiptScreen.isShown(),
            {
                content: "the ticket carries the VRP2 fiscal block",
                trigger: ".pos-receipt-vrp2:contains('POKLADNIČNÝ DOKLAD č. 0019')",
            },
            {
                content: "with the receiptId the QR encodes",
                trigger: ".pos-receipt-vrp2:contains('V-0000000000000000000000000000A019')",
            },
            {
                content: "and the register code",
                trigger: ".pos-receipt-vrp2:contains('99920201234560002')",
            },
            {
                content: "the QR is drawn",
                trigger: ".pos-receipt-vrp2 img.pos-receipt-vrp2-qr[src^='data:image']",
            },
            {
                content: "the official PDF can be opened",
                trigger: ".receipt-screen button.vrp2-pdf",
            },
            ReceiptScreen.clickNextOrder(),
        ].flat(),
});

registry.category("web_tour.tours").add("pos_vrp2_receipt_failed_tour", {
    steps: () =>
        [
            Chrome.startPoS(),
            Dialog.confirm("Open Register"),
            ProductScreen.addOrderline("Káva A 250g", "1"),
            ProductScreen.clickPayButton(),
            PaymentScreen.clickPaymentMethod("Cash"),
            PaymentScreen.clickValidate(),
            ReceiptScreen.isShown(),
            {
                content: "the cashier is told the receipt was not issued",
                trigger: ".o_notification:contains('VRP2 receipt was NOT issued')",
            },
            {
                content: "and the ticket says so instead of faking a fiscal block",
                trigger: ".pos-receipt-vrp2-missing",
            },
            {
                content: "no fiscal block",
                trigger: "body:not(:has(.pos-receipt-vrp2))",
            },
            ReceiptScreen.clickNextOrder(),
        ].flat(),
});
