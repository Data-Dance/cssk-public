# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.l10n_cssk_hr_payroll_garnishment_base.tests.common_reset_guard import (
    GarnishmentResetCommon,
)
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGarnishmentResetOca(GarnishmentResetCommon, TransactionCase):
    """The reset guard on the OCA payroll engine."""

    def test_reset_is_blocked_once_the_deduction_is_remitted(self):
        self._check_reset_blocked_after_remittance()

    def test_reset_is_allowed_while_nothing_has_been_remitted(self):
        self._check_reset_allowed_before_remittance()
