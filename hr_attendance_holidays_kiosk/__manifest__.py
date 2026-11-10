# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Attendance Kiosk: Reason for Leaving (CZ/SK)",
    "summary": "Pick a Time Off reason when checking out at the attendance "
    "kiosk; a draft time off is created for HR to approve.",
    "version": "19.0.1.0.0",
    "category": "Human Resources/Attendances",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "depends": ["hr_attendance", "hr_holidays"],
    "data": [
        "views/hr_leave_type_views.xml",
        "views/hr_attendance_views.xml",
    ],
    "assets": {
        "hr_attendance.assets_public_attendance": [
            "hr_attendance_holidays_kiosk/static/src/**/*",
        ],
        # Make the kiosk patch + reason component available to the JS unit-test
        # bundle without shipping them into the production backend bundle. The
        # patch's template extension stays out: its parent,
        # hr_attendance.public_kiosk_app, is not in this bundle, and the tests
        # never render the whole kiosk app.
        "web.assets_unit_tests": [
            "hr_attendance_holidays_kiosk/static/src/kiosk_reason/**/*",
            "hr_attendance_holidays_kiosk/static/src/public_kiosk_app/*.js",
            "hr_attendance_holidays_kiosk/static/tests/**/*",
        ],
    },
    "installable": True,
}
