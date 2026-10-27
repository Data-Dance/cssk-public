# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The base owns the Czech fields and the accrual plans it took over."""

from odoo.tests import TransactionCase, tagged

from ..hooks import MOVED_XMLIDS
from ..models.hr_version import CZ_VERSION_FIELDS


@tagged("post_install", "-at_install")
class TestBaseFields(TransactionCase):
    def _xmlid_modules(self, model, res_id):
        return set(self.env["ir.model.data"].search([
            ("model", "=", model), ("res_id", "=", res_id),
        ]).mapped("module"))

    def test_fields_are_owned_by_the_base(self):
        """Every Czech field carries an external ID of this module, so it
        survives whatever an engine module later stops declaring."""
        for model in ("hr.version", "hr.employee"):
            for name in CZ_VERSION_FIELDS:
                field = self.env["ir.model.fields"]._get(model, name)
                self.assertTrue(field, f"{model}.{name} missing")
                self.assertIn(
                    "l10n_cz_hr_payroll_base",
                    self._xmlid_modules("ir.model.fields", field.id),
                    f"{model}.{name} has no l10n_cz_hr_payroll_base xmlid")

    def test_employee_mirrors_write_through_to_the_version(self):
        employee = self.env["hr.employee"].create({"name": "CZ Mirror"})
        employee.write({
            "l10n_cz_agreement_type": "dpp",
            "l10n_cz_children_t2": 1,
            "l10n_cz_disability": "3",
        })
        version = employee.version_id
        self.assertEqual(version.l10n_cz_agreement_type, "dpp")
        self.assertEqual(version.l10n_cz_children_t2, 1)
        self.assertEqual(version.l10n_cz_disability, "3")

    def test_accrual_plans_belong_to_the_base(self):
        for name, model in MOVED_XMLIDS:
            record = self.env.ref(f"l10n_cz_hr_payroll_base.{name}")
            self.assertEqual(record._name, model)
            # Only ever one copy: the engines no longer declare them.
            self.assertEqual(
                self._xmlid_modules(model, record.id),
                {"l10n_cz_hr_payroll_base"})

    def test_accrual_plan_name_is_translatable(self):
        self.assertTrue(
            self.env["hr.leave.accrual.plan"]._fields["name"].translate)
