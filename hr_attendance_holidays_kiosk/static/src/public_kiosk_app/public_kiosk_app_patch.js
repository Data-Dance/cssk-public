// Copyright 2026 Data Dance s.r.o.
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { deserializeDateTime } from "@web/core/l10n/dates";

import publicKioskApp from "@hr_attendance/public_kiosk/public_kiosk_app";
import { KioskLeaveReason } from "@hr_attendance_holidays_kiosk/kiosk_reason/kiosk_reason";

const { kioskAttendanceApp } = publicKioskApp;

// Make the reason screen component available to the kiosk app template.
kioskAttendanceApp.components = {
    ...kioskAttendanceApp.components,
    KioskLeaveReason,
};

patch(kioskAttendanceApp.prototype, {
    setup() {
        super.setup();
        this.formatDateTime = registry.category("formatters").get("datetime");
        this.currentReasons = [];
        this.pendingAction = {};
        this.reasonGreeting = _t("Goodbye");
        this.reasonPrompt = _t("Reason for leaving");
        this.reasonDefaultLabel = _t("Work ended");
        this.reasonNotice = false;
    },

    switchDisplay(screen) {
        if (screen === "reason") {
            this.state.active_display = "reason";
            return;
        }
        super.switchDisplay(screen);
    },

    /**
     * Decide what to do once the employee has been identified:
     *  - about to check out with kiosk reasons -> reason screen ("checkout"),
     *  - returning after an automatic check-out -> reason screen ("auto"),
     *  - otherwise just perform the action.
     */
    async _routeAfterIdentify(info, idParams) {
        this.employeeData = info;
        const reasons = info.reasons || [];
        if (info.will_check_out && reasons.length) {
            this._enterReasonScreen("checkout", idParams);
        } else if (info.auto_checkout_pending && reasons.length) {
            this._enterReasonScreen("auto", idParams, info.auto_checkout_datetime);
        } else {
            await this._performKioskAction(idParams);
        }
    },

    _enterReasonScreen(mode, idParams, autoDatetime) {
        this.currentReasons = this.employeeData.reasons || [];
        this.pendingAction = idParams;
        if (mode === "auto") {
            this.reasonGreeting = _t("Welcome back");
            this.reasonPrompt = _t("Reason for your earlier departure?");
            this.reasonDefaultLabel = _t("No reason / check in");
            let when = "";
            if (autoDatetime) {
                when = this.formatDateTime(deserializeDateTime(autoDatetime));
            }
            this.reasonNotice = when
                ? _t("You were automatically checked out at %(time)s.", { time: when })
                : _t("You were automatically checked out earlier.");
        } else {
            this.reasonGreeting = _t("Goodbye");
            this.reasonPrompt = _t("Reason for leaving");
            this.reasonDefaultLabel = _t("Work ended");
            this.reasonNotice = false;
        }
        this.switchDisplay("reason");
    },

    /**
     * Identify first (no check-in/out yet), then route to the right screen.
     */
    async onBarcodeScanned(barcode) {
        if (this.lockScanner || this.state.active_display !== "main") {
            return;
        }
        this.lockScanner = true;
        this.ui.block();
        try {
            const info = await rpc("/hr_attendance/kiosk_identify", {
                token: this.props.token,
                barcode: barcode,
            });
            if (!info || !info.employee_name) {
                this.displayNotification(
                    _t("No employee corresponding to Badge ID '%(barcode)s.'", { barcode })
                );
                return;
            }
            await this._routeAfterIdentify(info, { barcode: barcode });
        } catch (error) {
            this.displayNotification((error.data && error.data.message) || error.message);
        } finally {
            this.lockScanner = false;
            this.ui.unblock();
        }
    },

    /**
     * Manual selection (with optional PIN): identify + PIN check first.
     */
    async onManualSelection(employeeId, enteredPin) {
        const info = await rpc("/hr_attendance/kiosk_identify", {
            token: this.props.token,
            employee_id: employeeId,
            pin_code: enteredPin,
        });
        if (!info || info.valid === false || !info.employee_name) {
            if (enteredPin) {
                this.displayNotification(_t("Wrong Pin"));
            }
            return;
        }
        await this._routeAfterIdentify(info, { employee_id: employeeId, pin_code: enteredPin });
    },

    /** Called from the reason screen. `reasonId === false` means the default. */
    async onReasonSelected(reasonId) {
        await this._performKioskAction(this.pendingAction || {}, reasonId);
    },

    /** Perform the actual check-in/out (with geolocation when enabled). */
    async _performKioskAction(idParams, reasonId = false) {
        const result = await this.makeRpcWithGeolocation("/hr_attendance/kiosk_action", {
            token: this.props.token,
            reason_id: reasonId,
            ...idParams,
        });
        if (result && result.employee_name) {
            this.employeeData = result;
            this.switchDisplay("greet");
        } else if (idParams.pin_code) {
            this.displayNotification(_t("Wrong Pin"));
        }
        return result;
    },
});
