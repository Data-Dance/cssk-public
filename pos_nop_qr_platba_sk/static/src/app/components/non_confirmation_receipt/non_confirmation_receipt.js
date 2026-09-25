import { Component } from "@odoo/owl";

/**
 * Thermal-printer-friendly receipt for "doklad o nepotvrdení zrealizovanej
 * platby" — printed by the POS via ``pos.printer.print(...)`` using the same
 * hardware path as the main sale receipt.
 *
 * Layout mirrors ``point_of_sale.OrderReceipt`` (logo + merchant header,
 * centred body) so the customer receives two visually-consistent slips.
 */
export class NonConfirmationReceipt extends Component {
    static template = "pos_nop_qr_platba_sk.NonConfirmationReceipt";
    static props = {
        receipt: Object,
        logoUrl: { type: String, optional: true },
    };

    formatDateTime(iso) {
        if (!iso) return "";
        try {
            return new Date(iso).toISOString().replace("T", " ").replace(/\..+$/, "") + " UTC";
        } catch (_) {
            return iso;
        }
    }

    get receipt() {
        return this.props.receipt;
    }
}
