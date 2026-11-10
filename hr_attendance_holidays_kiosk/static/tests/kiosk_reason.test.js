// Copyright 2026 Data Dance s.r.o.
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import { expect, test } from "@odoo/hoot";
import { contains, makeMockEnv, mountWithCleanup, onRpc } from "@web/../tests/web_test_helpers";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";

import { KioskLeaveReason } from "@hr_attendance_holidays_kiosk/kiosk_reason/kiosk_reason";
import publicKioskApp from "@hr_attendance/public_kiosk/public_kiosk_app";

const { kioskAttendanceApp } = publicKioskApp;

defineMailModels();

const EMP = { employee_name: "Kiosk Tester", employee_avatar: false };
const REASONS = [
    { id: 1, name: "Doctor", color: 1 },
    { id: 2, name: "Personal", color: 3 },
];

test.tags("desktop", "kiosk_reason_dd");
test("reason screen renders Work ended + each reason and wires the callbacks", async () => {
    const events = [];
    await mountWithCleanup(KioskLeaveReason, {
        props: {
            employeeData: EMP,
            reasons: REASONS,
            onSelectReason: (id) => events.push(["reason", id]),
            onWorkEnded: () => events.push(["work_ended"]),
            onClickBack: () => events.push(["back"]),
        },
    });

    expect(".btn-success").toHaveCount(1); // the default "Work ended" button
    expect("button:contains(Doctor)").toHaveCount(1);
    expect("button:contains(Personal)").toHaveCount(1);

    await contains("button:contains(Doctor)").click();
    await contains(".btn-success").click();
    await contains(".o_hr_kiosk_mode_bottom button").click();

    expect(events).toEqual([["reason", 1], ["work_ended"], ["back"]]);
});

test.tags("desktop", "kiosk_reason_dd");
test("check-out routes to the reason screen and kiosk_action carries the reason", async () => {
    onRpc("/hr_attendance/kiosk_identify", () => ({
        ...EMP,
        valid: true,
        will_check_out: true,
        reasons: REASONS,
        attendance: { check_in: false, check_out: false },
    }));
    // Nothing is mounted here, so start the mock server explicitly or the
    // rpc() call above goes to the network.
    await makeMockEnv();

    const actionCalls = [];
    // An instance of the patched prototype without mounting the whole kiosk
    // app: the patch's own helpers and switchDisplay ("reason" included) run
    // for real, only the network-facing pieces are stubbed.
    const self = Object.assign(Object.create(kioskAttendanceApp.prototype), {
        props: { token: "tok" },
        state: { active_display: "manual" },
        currentReasons: [],
        pendingAction: {},
        displayNotification() {},
        async makeRpcWithGeolocation(route, params) {
            actionCalls.push({ route, params });
            return { ...EMP, attendance: { check_in: "x", check_out: "y" } };
        },
    });

    await self.onManualSelection(7, false);
    expect(self.state.active_display).toBe("reason");
    expect(self.currentReasons).toHaveLength(2);
    expect(self.pendingAction).toEqual({ employee_id: 7, pin_code: false });

    await self.onReasonSelected(1);
    expect(actionCalls).toHaveLength(1);
    expect(actionCalls[0].route).toBe("/hr_attendance/kiosk_action");
    expect(actionCalls[0].params.reason_id).toBe(1);
    expect(self.state.active_display).toBe("greet");
});
