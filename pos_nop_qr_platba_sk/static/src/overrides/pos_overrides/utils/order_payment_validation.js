/**
 * Patch the online-payment validation flow for QR Platba lines.
 *
 * QR Platba is not a classic online-payment provider: the customer pays from
 * their banking app and the confirmation arrives out-of-band via NOP. While
 * waiting, the cashier has three possible exits:
 *
 *   1. NOP confirms (bus push resolves the payment line) — normal path.
 *   2. Cashier picks "Close without confirmation" — the non-confirmation
 *      receipt ("doklad o nepotvrdení zrealizovanej platby") is printed,
 *      the QR Platba line is dropped, and the cashier chooses another
 *      payment method. Any late NOP push becomes a refund owed to the
 *      debtor (handled server-side by ``nop.transaction`` state transitions).
 *   3. Cashier picks "Cancel" — customer walked away without paying.
 */
import OrderPaymentValidation from "@point_of_sale/app/utils/order_payment_validation";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { qrCodeSrc } from "@point_of_sale/utils";
import { QrPlatbaPopup } from "@pos_nop_qr_platba_sk/app/components/qr_platba_popup/qr_platba_popup";
import { NonConfirmationReceipt } from "@pos_nop_qr_platba_sk/app/components/non_confirmation_receipt/non_confirmation_receipt";

const QR_PLATBA_POLL_INTERVAL_MS = 2000;

patch(OrderPaymentValidation.prototype, {
    async isOrderValid(isForceValidate) {
        const qrPlatbaLines = this.paymentLines.filter(
            (line) =>
                line.payment_method_id.is_qr_platba_sk &&
                line.getPaymentStatus() !== "done"
        );
        if (qrPlatbaLines.length === 0) {
            return await super.isOrderValid(...arguments);
        }

        if (!this.order.id) {
            await this.pos.syncAllOrders({ orders: [this.order] });
        }
        if (!this.order.id) {
            this.pos.dialog.add(AlertDialog, {
                title: _t("QR Platba unavailable"),
                body: _t("The order could not be saved on the server."),
            });
            return false;
        }

        for (const line of qrPlatbaLines) {
            const ok = await this._processQrPlatbaLine(line);
            if (!ok) {
                return false;
            }
        }

        return await super.isOrderValid(...arguments);
    },

    async _processQrPlatbaLine(paymentLine) {
        const amount = paymentLine.getAmount();
        if (amount <= 0) {
            this.pos.dialog.add(AlertDialog, {
                title: _t("Invalid QR Platba amount"),
                body: _t("QR Platba cannot be used for a zero or negative amount."),
            });
            return false;
        }

        let response;
        try {
            response = await this.pos.data.call(
                "pos.order",
                "create_qr_platba_transaction",
                [this.order.id, amount]
            );
        } catch (ex) {
            this.pos.dialog.add(AlertDialog, {
                title: _t("QR Platba unavailable"),
                body: ex?.data?.message || ex?.message || String(ex),
            });
            return false;
        }

        paymentLine.qr_platba_nop_transaction_id = response.nop_transaction_id;
        paymentLine.setPaymentStatus("waiting");
        this.order.selectPaymentline(paymentLine);

        // Shared between the popup callbacks and the resolver.
        const state = { outcome: null };

        const popupProps = {
            qrCode: qrCodeSrc(response.qr_url),
            formattedAmount: this.pos.env.utils.formatCurrency(amount),
            orderName: this.order.name,
            // Server-driven, falls back to the popup's own 300 s default if
            // the backend didn't send a value (older pos.payment.method).
            timeoutSeconds: response.timeout_seconds
                || paymentLine.payment_method_id.qr_platba_timeout_seconds
                || 300,
            onCloseWithoutConfirmation: async () => {
                state.outcome = "unconfirmed";
                paymentLine.onlinePaymentResolver?.(false);
            },
            onCancel: async () => {
                state.outcome = "cancel";
                paymentLine.onlinePaymentResolver?.(false);
            },
        };

        const closePopup = this.pos.dialog.add(QrPlatbaPopup, popupProps, {
            onClose: () => paymentLine.onlinePaymentResolver?.(false),
        });

        const pollHandle = setInterval(() => {
            this.pos.updateOnlinePaymentsDataWithServer(this.order, false);
        }, QR_PLATBA_POLL_INTERVAL_MS);

        const paid = await new Promise((resolve) => {
            paymentLine.onlinePaymentResolver = resolve;
        });

        clearInterval(pollHandle);
        closePopup();

        if (paid) {
            if (paymentLine.getPaymentStatus() === "waiting") {
                paymentLine.setPaymentStatus("done");
            }
            return true;
        }

        // Not confirmed through the normal path. Decide what to do based on
        // which button the cashier pressed (or assume "unconfirmed" on timeout-
        // less dialog dismissal, to be safe — a missed refund is worse than
        // a duplicate one).
        const nopTxId = paymentLine.qr_platba_nop_transaction_id;
        if (state.outcome === "cancel") {
            if (nopTxId) {
                this.pos.data
                    .call("pos.order", "cancel_qr_platba_transaction", [this.order.id, nopTxId])
                    .catch(() => {});
            }
            paymentLine.delete({ backend: true });
            return false;
        }

        // Default (incl. ESC / click-outside) → close as unconfirmed, which is
        // the safer outcome: if the customer *did* pay we hand them a receipt
        // that lets them claim the refund.
        return await this._closeUnconfirmed(paymentLine, nopTxId);
    },

    async _closeUnconfirmed(paymentLine, nopTxId) {
        if (!nopTxId) {
            paymentLine.delete({ backend: true });
            return false;
        }
        let response;
        try {
            response = await this.pos.data.call(
                "pos.order",
                "close_qr_platba_unconfirmed",
                [this.order.id, nopTxId]
            );
        } catch (ex) {
            this.pos.dialog.add(AlertDialog, {
                title: _t("Could not close the QR Platba transaction"),
                body: ex?.data?.message || ex?.message || String(ex),
            });
            return false;
        }

        if (response.already_confirmed) {
            // Race: NOP confirmed while the cashier was deciding. Let the
            // normal online-payment flow re-sync and finalize.
            paymentLine.setPaymentStatus("done");
            await this.pos.updateOnlinePaymentsDataWithServer(this.order, false);
            return true;
        }

        // Print the non-confirmation receipt and remove the QR Platba line
        // so the cashier can select another payment method.
        try {
            await this.pos.printer.print(
                NonConfirmationReceipt,
                {
                    receipt: response.receipt,
                    logoUrl: this.pos.config?.receiptLogoUrl,
                },
                this.pos.printOptions
            );
        } catch (ex) {
            // eslint-disable-next-line no-console
            console.error("Failed to print non-confirmation receipt", ex);
            this.pos.dialog.add(AlertDialog, {
                title: _t("Non-confirmation receipt could not be printed"),
                body: _t(
                    "The non-confirmation receipt did not print automatically. "
                    + "Open the transaction %s in the back-office and reprint it manually.",
                    response.receipt.transaction_id
                ),
            });
        }

        paymentLine.delete({ backend: true });
        return false;
    },
});
