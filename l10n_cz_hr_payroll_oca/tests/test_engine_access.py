# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The Czech fields come from l10n_cz_hr_payroll_base with an HR-manager
floor; this module must narrow them to its own payroll users. A lost
re-declaration would widen access to tax and disability data silently."""

from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_cz_hr_payroll_base.models.hr_version import CZ_VERSION_FIELDS


@tagged("post_install", "-at_install")
class TestEngineAccess(TransactionCase):
    def test_czech_fields_are_restricted_to_payroll_users(self):
        for model in ("hr.version", "hr.employee"):
            fields = self.env[model]._fields
            for name in CZ_VERSION_FIELDS:
                self.assertEqual(
                    fields[name].groups, "payroll.group_payroll_user", f"{model}.{name}")
