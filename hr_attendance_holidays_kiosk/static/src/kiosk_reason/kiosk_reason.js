// Copyright 2026 Data Dance s.r.o.
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import { Component } from "@odoo/owl";

// Odoo's standard 12-colour palette ($o-colors), index 0 = "No color".
const REASON_COLORS = [
    "#a2a2a2", "#ee2d2d", "#dc8534", "#e8bb1d", "#5794dd", "#9f628f",
    "#db8865", "#41a9a2", "#304be0", "#ee2f8a", "#61c36e", "#9872e6",
];

export class KioskLeaveReason extends Component {
    static template = "hr_attendance_holidays_kiosk.KioskLeaveReason";
    static props = {
        employeeData: { type: Object },
        reasons: { type: Array },
        onSelectReason: { type: Function },
        onWorkEnded: { type: Function },
        onClickBack: { type: Function },
        // Optional wording so the same screen works for a live check-out and
        // for logging a reason on a previous automatic check-out.
        greeting: { type: String, optional: true },
        prompt: { type: String, optional: true },
        defaultLabel: { type: String, optional: true },
        notice: { type: [String, { value: false }], optional: true },
    };
    static defaultProps = {
        greeting: "Goodbye",
        prompt: "Reason for leaving",
        defaultLabel: "Work ended",
        notice: false,
    };

    setup() {
        this.employeeName = this.props.employeeData.employee_name;
        this.employeeAvatar = this.props.employeeData.employee_avatar;
        this.lock = false;
    }

    /** Inline style for a reason button based on the Time Off Type colour.
     *  Colour 0 ("No color") keeps the default light button. */
    reasonStyle(color) {
        if (!color) {
            return "";
        }
        const hex = REASON_COLORS[color % REASON_COLORS.length];
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
        const text = luminance > 0.6 ? "#1d1d1d" : "#ffffff";
        return `background-color:${hex};border-color:${hex};color:${text};`;
    }

    async select(reasonId) {
        // Prevent double taps while the RPC is in flight.
        if (this.lock) {
            return;
        }
        this.lock = true;
        try {
            if (reasonId === false) {
                await this.props.onWorkEnded();
            } else {
                await this.props.onSelectReason(reasonId);
            }
        } finally {
            this.lock = false;
        }
    }
}
