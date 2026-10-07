/**
 * VRP2 fiscal receipt at the till.
 *
 * The server issues the VRP2 receipt after the order's sync transaction has
 * committed, before that request returns. Right after validation (and before
 * the automatic print) the till asks the server for the result and keeps it
 * on the order's uiState, so the printed ticket carries the fiscal block
 * and the receipt screen can open the official VRP2 PDF.
 */
import OrderPaymentValidation from "@point_of_sale/app/utils/order_payment_validation";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { generateQRCodeDataUrl } from "@point_of_sale/utils";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

/** VRP2 prints the receipt number with four digits: "č. 0019". */
function padReceiptNumber(number) {
    return number ? String(number).padStart(4, "0") : "";
}

export async function loadVrp2Receipt(pos, order) {
    // An order that never reached the server (offline) has no numeric id
    // and no receipt yet; it is fiscalized when it syncs.
    if (!pos.config.vrp2_enabled || !order || typeof order.id !== "number") {
        return;
    }
    try {
        const info = await pos.data.call("pos.order", "vrp2_receipt_for_ui", [order.id]);
        order.uiState.vrp2 = info;
        if (info.enabled && info.state !== "fiscalized") {
            pos.notification.add(
                _t("The VRP2 receipt was NOT issued: %s", info.error || info.state),
                { type: "danger", sticky: true }
            );
        }
    } catch {
        pos.notification.add(
            _t("Could not read the VRP2 receipt of this order from the server."),
            { type: "warning", sticky: true }
        );
    }
}

patch(OrderPaymentValidation.prototype, {
    async afterOrderValidation() {
        // Before super: it triggers the automatic print.
        await loadVrp2Receipt(this.pos, this.order);
        return await super.afterOrderValidation(...arguments);
    },
});

patch(OrderReceipt.prototype, {
    /** The fiscal block to print, or null when there is none (yet). */
    get vrp2Receipt() {
        const order = this.order;
        if (!order.config.vrp2_enabled) {
            return null;
        }
        const info = order.uiState?.vrp2;
        if (info) {
            return info.state === "fiscalized" && info.receipt_uuid
                ? { ...info, receipt_number: padReceiptNumber(info.receipt_number) }
                : null;
        }
        // A reprint from the order history: the fields were loaded with it.
        if (order.vrp2_state === "fiscalized" && order.vrp2_receipt_uuid) {
            return {
                receipt_number: padReceiptNumber(order.vrp2_receipt_number),
                receipt_uuid: order.vrp2_receipt_uuid,
                okp: order.vrp2_okp,
                dkp: order.config.vrp2_dkp,
                created: false,
            };
        }
        return null;
    },
    get vrp2NotIssued() {
        const info = this.order.uiState?.vrp2;
        return Boolean(info && info.enabled && info.state !== "fiscalized");
    },
    /** The official receipt's QR encodes the receiptId and nothing else. */
    get vrp2QrCode() {
        return generateQRCodeDataUrl(this.vrp2Receipt.receipt_uuid);
    },
});

patch(ReceiptScreen.prototype, {
    get vrp2HasPdf() {
        return Boolean(this.currentOrder?.uiState?.vrp2?.has_pdf);
    },
    openVrp2Pdf() {
        const order = this.currentOrder;
        window.open(`/web/content/pos.order/${order.id}/vrp2_pdf/VRP2-${order.id}.pdf`, "_blank");
    },
});
