# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Shared fixture and assertions for the reset guard, for both payroll engines.

A plain mixin, not a TestCase: the guard hangs off a real ``hr.payslip``
lifecycle and this module deliberately ships no payroll engine, so the tests
themselves have to be declared in the bridges.

The ASSERTIONS live here and the bridges only name them. Odoo's suite builder
does not collect ``test_*`` methods a TestCase inherits from a plain mixin —
plain unittest does, which makes it an easy way to write two tests that never
run — so the methods are declared there and the bodies are written once here.
"""

from odoo.exceptions import UserError


class GarnishmentResetCommon:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "Garnishment CZ", "country_id": cls.env.ref("base.cz").id})
        cls.env.user.company_ids |= cls.company
        cls.env.user.company_id = cls.company
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Dlužník", "company_id": cls.company.id})
        cls.bailiff = cls.env["res.partner"].create({"name": "Exekutorský úřad"})
        cls.order = cls.env["hr.wage.garnishment"].create({
            "case_number": "123 EX 456/2026",
            "employee_id": cls.employee.id,
            "company_id": cls.company.id,
            "claim_class": "ordinary",
            "date_delivered": "2026-01-10",
            "total_amount": 100000.0,
            "bailiff_partner_id": cls.bailiff.id,
            "state": "running",
        })

    def _payslip(self):
        # ``name`` is NOT NULL on the Enterprise engine and computed on the
        # OCA one; setting it explicitly keeps one fixture valid on both.
        return self.env["hr.payslip"].create({
            "name": "Test payslip 2026-06",
            "employee_id": self.employee.id,
            "company_id": self.company.id,
            "date_from": "2026-06-01",
            "date_to": "2026-06-30",
        })

    def _line_for(self, slip, state):
        return self.env["hr.wage.garnishment.line"].create({
            "garnishment_id": self.order.id,
            "employee_id": self.employee.id,
            "payslip_ref": slip._cssk_garnishment_payslip_ref(),
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "amount": 1000.0,
            "state": state,
        })

    def _check_reset_blocked_after_remittance(self):
        """The employee is debited once; the ledger must say so too.

        ``_cssk_garnishment_unregister`` keeps ``done`` lines — the money has
        gone to the bailiff and only a reversal undoes that — while
        ``_register_allocation`` clears only ``state != 'done'`` before writing
        fresh rows. Confirming a reset payslip therefore left a ``done`` line
        and a ``computed`` line on the same ``payslip_ref``: ``paid_amount``
        inflated and ``remaining_amount`` understated, which on a nearly
        settled order is the direction that ends an exekúcia early.
        """
        slip = self._payslip()
        self._line_for(slip, "done")
        with self.assertRaises(UserError) as cm:
            slip.action_payslip_draft()
        self.assertIn("remitted", str(cm.exception).lower())

    def _check_reset_allowed_before_remittance(self):
        """The guard must not block the ordinary payroll correction."""
        slip = self._payslip()
        self._line_for(slip, "computed")
        slip.action_payslip_draft()
        self.assertEqual(slip.state, "draft")
