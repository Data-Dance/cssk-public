# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestKioskReasonJs(HttpCase):
    """Runs the module's hoot (JS) unit tests in a headless browser.

    Kept in its own class so it can be selected/skipped independently of the
    pure-Python tests (it needs a Chrome/Chromium binary)."""

    def test_kiosk_reason_hoot(self):
        self.browser_js(
            "/web/tests?headless&loglevel=2&preset=desktop&tag=kiosk_reason_dd&timeout=15000",
            "", "",
            login="admin",
            timeout=900,
            success_signal="[HOOT] Test suite succeeded",
        )
