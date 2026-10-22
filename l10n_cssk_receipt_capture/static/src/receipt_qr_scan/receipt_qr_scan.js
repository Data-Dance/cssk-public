// Copyright 2026 Data Dance s.r.o.
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import { Component, onMounted, useState } from "@odoo/owl";
import { scanBarcode } from "@web/core/barcode/barcode_dialog";
import { isBarcodeScannerSupported } from "@web/core/barcode/barcode_video_scanner";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * Scan a receipt's QR code with the camera and capture it.
 *
 * Built on Odoo's own scanner (native BarcodeDetector, with the bundled ZXing
 * polyfill where the browser lacks one), so it works the same in the Odoo
 * mobile app and in a phone's browser. A live camera is the best chance at a
 * dense off-line code that no still photograph would yield: many frames,
 * autofocus, and the user can hold the paper flat.
 *
 * The scanner's promise never settles if its dialog is simply closed, so this
 * screen does not wait on it to learn about a cancel: it stays up with a
 * "Scan again" button instead.
 */
export class ReceiptQrScan extends Component {
    static template = "l10n_cssk_receipt_capture.ReceiptQrScan";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.state = useState({
            busy: false,
            message: "",
            supported: isBarcodeScannerSupported(),
        });
        onMounted(() => {
            if (this.state.supported) {
                this.scan();
            }
        });
    }

    get context() {
        return (this.props.action && this.props.action.context) || {};
    }

    async scan() {
        this.state.message = "";
        let text;
        try {
            text = await scanBarcode(this.env, "environment");
        } catch (error) {
            this.state.message =
                (error && error.message) ||
                _t("The camera could not be opened. Check the browser's permission for it.");
            return;
        }
        if (!text) {
            return;
        }
        this.state.busy = true;
        try {
            // The Expenses app opens this with cssk_scan_model = "hr.expense",
            // whose entry point lands an employee on an expense they can open.
            const model = this.context.cssk_scan_model || "cssk.receipt";
            const result = await this.orm.call(
                model,
                "action_capture_from_scan",
                [text],
                { context: this.context }
            );
            if (result.retry) {
                // Usually the loyalty link printed above the fiscal code.
                this.state.message = result.message;
                this.notification.add(result.message, { type: "warning" });
                return;
            }
            await this.action.doAction(result.action);
        } finally {
            this.state.busy = false;
        }
    }

    back() {
        this.action.restore();
    }
}

registry
    .category("actions")
    .add("l10n_cssk_receipt_capture.scan_receipt_qr", ReceiptQrScan);
