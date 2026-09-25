import { Component, useState, onWillUnmount } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";

/**
 * Popup shown while the customer scans the payme.sk QR and their banking
 * app pushes the payment through NOP.
 *
 * Three exit paths:
 *   - ``confirm()`` — NOP confirmed the payment server-side; the bus push
 *     already resolved the payment line, we just close the dialog.
 *   - ``onCloseWithoutConfirmation()`` — cashier chose to close the sale
 *     without waiting. Will trigger the "doklad o nepotvrdení zrealizovanej
 *     platby" receipt and return to the payment screen so another method
 *     can be used.
 *   - ``onCancel()`` — cashier confirms the customer did not pay at all;
 *     the tx is cancelled.
 *
 * After ``timeoutSeconds`` the popup starts flashing a prompt encouraging
 * the cashier to pick one of the two exit actions rather than waiting
 * forever.
 */
export class QrPlatbaPopup extends Component {
    static template = "pos_nop_qr_platba_sk.QrPlatbaPopup";
    static components = { Dialog };
    static props = {
        qrCode: String,
        formattedAmount: String,
        orderName: String,
        timeoutSeconds: { type: Number, optional: true },
        onCloseWithoutConfirmation: Function,
        onCancel: Function,
        close: Function,  // provided by Dialog service
    };
    static defaultProps = {
        timeoutSeconds: 300,
    };

    setup() {
        this.state = useState({
            elapsed: 0,
            promptTimeout: false,
            busy: false,
        });
        this._ticker = setInterval(() => {
            this.state.elapsed += 1;
            if (this.state.elapsed >= this.props.timeoutSeconds) {
                this.state.promptTimeout = true;
            }
        }, 1000);
        onWillUnmount(() => clearInterval(this._ticker));
    }

    get timeoutLabel() {
        const s = Math.max(0, this.props.timeoutSeconds - this.state.elapsed);
        const mm = Math.floor(s / 60).toString().padStart(2, "0");
        const ss = (s % 60).toString().padStart(2, "0");
        return `${mm}:${ss}`;
    }

    async _closeUnconfirmed() {
        if (this.state.busy) return;
        this.state.busy = true;
        try {
            await this.props.onCloseWithoutConfirmation();
        } finally {
            this.state.busy = false;
        }
    }

    async _cancel() {
        if (this.state.busy) return;
        this.state.busy = true;
        try {
            await this.props.onCancel();
        } finally {
            this.state.busy = false;
        }
    }
}
