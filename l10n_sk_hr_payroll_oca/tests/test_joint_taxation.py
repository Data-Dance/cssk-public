# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Several employee records of one person, taxed together.

§ 35 ods. 1 zákona č. 595/2003 Z. z. taxes the total the employer pays the
employee in the month, less the employee's premiums and one non-taxable
amount. June 2026: employee premiums 9.4 % social and 5 % health, non-taxable
amount 497.23, 19 % up to a taxable wage of 3 665.28 and 25 % above.

The example: an employment of 400 with the declaration signed and a DoPČ of
300 beside it. Their bases are 400 - 57.60 = 342.40 and 300 - 43.20 = 256.80.
Taxed separately: 0.00 (342.40 is under 497.23) and 256.80 x 19 % = 48.79.
Taxed together: (342.40 + 256.80 - 497.23) x 19 % = 19.3743, so 19.37.
"""

from calendar import monthrange
from datetime import date
from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSkJointTaxation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "SK Joint Tax Co", "country_id": cls.env.ref("base.sk").id}
        )
        cls.env.user.company_ids |= cls.company
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "SK 40h/week", "company_id": cls.company.id}
        )
        cls.employment = cls.env.ref(
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary"
        )
        cls.dopc = cls.env.ref("l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_dopc")

    def setUp(self):
        super().setUp()
        # The wages here are below the minimum wage claim; its top-up has its
        # own tests in l10n_sk_hr_payroll_surcharges.
        Payslip = type(self.env["hr.payslip"])
        if hasattr(Payslip, "_l10n_sk_min_wage_claim_applies"):
            patcher = patch.object(
                Payslip, "_l10n_sk_min_wage_claim_applies", return_value=False
            )
            patcher.start()
            self.addCleanup(patcher.stop)

    # ------------------------------------------------------------------
    def _record(self, name, wage, structure=None, end=None,
                number="850101/1234", **vals):
        employee = self.env["hr.employee"].create(
            {
                "name": name,
                "company_id": self.company.id,
                "resource_calendar_id": self.calendar.id,
                "identification_id": number,
            }
        )
        values = {
            "contract_date_start": date(2024, 1, 1),
            "date_version": date(2024, 1, 1),
            "wage": wage,
            "resource_calendar_id": self.calendar.id,
            "struct_id": (structure or self.employment).id,
        }
        if end:
            values["contract_date_end"] = end
        values.update(vals)
        employee.version_id.write(values)
        return employee

    def _pair(self, wage=400.0, linked_wage=300.0, link=True,
              number="850101/1234", **vals):
        principal = self._record(
            "Employment", wage, number=number,
            l10n_sk_tax_declaration_signed=True, **vals
        )
        linked = self._record("Agreement", linked_wage, self.dopc, number=number)
        if link:
            linked.l10n_sk_tax_principal_id = principal
        return principal, linked

    def _draft(self, employee, inputs=(), month=6):
        contract = employee.version_id
        return (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "%s/2026 %s" % (month, employee.name),
                    "employee_id": employee.id,
                    "contract_id": contract.id,
                    "struct_id": contract.struct_id.id,
                    "company_id": self.company.id,
                    "date_from": date(2026, month, 1),
                    "date_to": date(2026, month, monthrange(2026, month)[1]),
                    "input_line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": code,
                                "code": code,
                                "amount": amount,
                                "contract_id": contract.id,
                            },
                        )
                        for code, amount in inputs
                    ],
                }
            )
        )

    def _slip(self, employee, inputs=()):
        slip = self._draft(employee, inputs)
        slip.compute_sheet()
        return slip

    @staticmethod
    def _line(slip, code):
        return round(
            sum(slip.line_ids.filtered(lambda row: row.code == code).mapped("total")), 2
        )

    def _codes(self, slip):
        return set(slip.line_ids.mapped("code"))

    def _tax(self, slip):
        return self._line(slip, "INCOMETAX")

    # ------------------------------------------------------------------
    # the example
    # ------------------------------------------------------------------
    def test_separate_records_are_taxed_separately(self):
        principal, linked = self._pair(link=False)
        agreement = self._slip(linked)
        employment = self._slip(principal)
        self.assertEqual(self._line(employment, "TAXBASE"), 342.40)
        self.assertEqual(self._line(agreement, "TAXBASE"), 256.80)
        self.assertEqual(self._tax(employment), 0.0)
        self.assertEqual(self._tax(agreement), -48.79)
        for slip in employment | agreement:
            self.assertFalse(self._codes(slip) & {"TAXBASE_MOVED", "TAXBASE_TAKEN"})

    def test_month_is_taxed_once_on_the_principal(self):
        principal, linked = self._pair()
        agreement = self._slip(linked)
        self.assertEqual(self._line(agreement, "TAXBASE"), 256.80)
        self.assertEqual(self._line(agreement, "TAXBASE_MOVED"), 256.80)
        self.assertEqual(self._tax(agreement), 0.0)
        self.assertEqual(self._line(agreement, "CHILD_BONUS"), 0.0)
        # 300 - 43.20 of premiums, and no tax here.
        self.assertEqual(self._line(agreement, "NET"), 256.80)
        self.assertNotIn("TAXBASE_TAKEN", self._codes(agreement))

        employment = self._slip(principal)
        self.assertEqual(self._line(employment, "TAXBASE"), 342.40)
        self.assertEqual(self._line(employment, "TAXBASE_TAKEN"), 256.80)
        self.assertNotIn("TAXBASE_MOVED", self._codes(employment))
        # (342.40 + 256.80 - 497.23) x 19 % = 19.3743
        self.assertEqual(self._tax(employment), -19.37)
        # 400 - 57.60 - 19.37
        self.assertEqual(self._line(employment, "NET"), 323.03)

    def test_declaration_of_the_linked_record_is_not_used(self):
        """The principal's declaration decides: without it, no allowance."""
        principal = self._record("Employment", 400.0)
        linked = self._record(
            "Agreement", 300.0, self.dopc, l10n_sk_tax_declaration_signed=True
        )
        linked.l10n_sk_tax_principal_id = principal
        agreement = self._slip(linked)
        employment = self._slip(principal)
        self.assertEqual(self._tax(agreement), 0.0)
        # 599.20 x 19 % = 113.848
        self.assertEqual(self._tax(employment), -113.85)

    # ------------------------------------------------------------------
    # child bonus and bands on the combined base
    # ------------------------------------------------------------------
    def test_child_bonus_cap_uses_the_combined_base(self):
        """One child under 15: 100.00, capped at 29 % of the base.

        On the employment's base alone 29 % of 342.40 is 99.296, so 99.30;
        on the month's base of 599.20 the cap is 173.77 and the bonus whole.
        """
        principal, linked = self._pair(
            link=False, number="900202/4321", l10n_sk_children_under_15=1)
        self.assertEqual(self._line(self._slip(principal), "CHILD_BONUS"), 99.30)
        principal, linked = self._pair(l10n_sk_children_under_15=1)
        linked.version_id.l10n_sk_children_under_15 = 1
        agreement = self._slip(linked)
        employment = self._slip(principal)
        self.assertEqual(self._line(agreement, "CHILD_BONUS"), 0.0)
        self.assertEqual(self._line(employment, "CHILD_BONUS"), 100.0)

    def test_bases_over_the_first_band_together(self):
        """3 000 and 2 500: bases 2 568.00 and 2 140.00, each under 3 665.28.

        Separately: (2 568.00 - 497.23) x 19 % = 393.45 and 2 140.00 x 19 % =
        406.60. Together 4 708.00 - 497.23 = 4 210.77: 3 665.28 x 19 % =
        696.4032 and 545.49 x 25 % = 136.3725, 832.7757 in all.
        """
        principal, linked = self._pair(3000.0, 2500.0, link=False, number="900202/4321")
        self.assertEqual(self._tax(self._slip(principal)), -393.45)
        self.assertEqual(self._tax(self._slip(linked)), -406.60)
        principal, linked = self._pair(3000.0, 2500.0)
        agreement = self._slip(linked)
        employment = self._slip(principal)
        self.assertEqual(self._line(employment, "TAXBASE_TAKEN"), 2140.0)
        self.assertEqual(self._tax(agreement), 0.0)
        self.assertEqual(self._tax(employment), -832.78)

    def test_the_total_is_floored_at_zero_once(self):
        principal, linked = self._pair()
        self._slip(linked)
        employment = self._slip(principal)
        # Own base of -10.00 with 256.80 taken over.
        self.assertEqual(employment._l10n_sk_monthly_tax_base(-10.0), 246.80)
        self.assertEqual(employment._l10n_sk_monthly_tax_base(-300.0), 0.0)
        alone = self._slip(self._record("Alone", 400.0, number="900202/4321"))
        self.assertEqual(alone._l10n_sk_monthly_tax_base(-10.0), 0.0)
        self.assertEqual(alone._l10n_sk_monthly_tax_base(342.40), 342.40)

    # ------------------------------------------------------------------
    # the link
    # ------------------------------------------------------------------
    def test_unlinking_restores_separate_taxation(self):
        principal, linked = self._pair()
        agreement = self._slip(linked)
        employment = self._slip(principal)
        self.assertEqual(self._tax(employment), -19.37)
        linked.l10n_sk_tax_principal_id = False
        agreement.compute_sheet()
        employment.compute_sheet()
        self.assertEqual(self._tax(agreement), -48.79)
        self.assertEqual(self._tax(employment), 0.0)
        for slip in employment | agreement:
            self.assertFalse(self._codes(slip) & {"TAXBASE_MOVED", "TAXBASE_TAKEN"})

    def test_linked_record_without_a_payslip_changes_nothing(self):
        principal, _linked = self._pair()
        employment = self._slip(principal)
        self.assertEqual(self._tax(employment), 0.0)
        self.assertNotIn("TAXBASE_TAKEN", self._codes(employment))
        employment.action_payslip_done()
        self.assertEqual(employment.state, "done")

    def test_month_without_a_contract_of_the_principal(self):
        """The employment ended in May: the agreement is taxed on its own."""
        principal, linked = self._pair(end=date(2026, 5, 31))
        agreement = self._slip(linked)
        self.assertNotIn("TAXBASE_MOVED", self._codes(agreement))
        self.assertEqual(self._tax(agreement), -48.79)

    def test_payslip_confirmed_before_the_link_stays_taxed_alone(self):
        principal, linked = self._pair(link=False)
        agreement = self._slip(linked)
        agreement.action_payslip_done()
        linked.l10n_sk_tax_principal_id = principal
        employment = self._slip(principal)
        self.assertEqual(self._tax(agreement), -48.79)
        self.assertNotIn("TAXBASE_TAKEN", self._codes(employment))
        self.assertEqual(self._tax(employment), 0.0)

    # ------------------------------------------------------------------
    # order and consistency
    # ------------------------------------------------------------------
    def test_principal_waits_for_the_linked_payslip(self):
        principal, linked = self._pair()
        agreement = self._draft(linked)
        employment = self._draft(principal)
        with self.assertRaises(UserError) as error:
            employment.compute_sheet()
        self.assertIn(agreement.display_name, str(error.exception))
        self.assertIn("Agreement", str(error.exception))
        agreement.compute_sheet()
        employment.compute_sheet()
        self.assertEqual(self._tax(employment), -19.37)

    def test_payslip_computed_before_the_link_is_computed_again(self):
        principal, linked = self._pair(link=False)
        agreement = self._slip(linked)
        linked.l10n_sk_tax_principal_id = principal
        with self.assertRaises(UserError):
            self._slip(principal)
        agreement.compute_sheet()
        self.assertEqual(self._tax(self._slip(principal)), -19.37)

    def test_one_batch_computes_the_linked_payslips_first(self):
        principal, linked = self._pair()
        employment = self._draft(principal)
        agreement = self._draft(linked)
        (employment | agreement).compute_sheet()
        self.assertEqual(self._tax(agreement), 0.0)
        self.assertEqual(self._tax(employment), -19.37)

    def test_stale_principal_is_not_confirmed(self):
        """The agreement is raised to 500 after the employment was computed.

        Its base becomes 500 - 72.00 = 428.00 and the month's tax
        (342.40 + 428.00 - 497.23) x 19 % = 51.9023, so 51.90.
        """
        principal, linked = self._pair()
        agreement = self._slip(linked)
        employment = self._slip(principal)
        linked.version_id.wage = 500.0
        agreement.compute_sheet()
        self.assertEqual(self._line(agreement, "TAXBASE_MOVED"), 428.0)
        # Confirmed as it stands, it would withhold the tax of the old base.
        with self.assertRaises(UserError):
            employment.with_context(without_compute_sheet=True).action_payslip_done()
        self.assertEqual(employment.state, "verify")
        # This engine computes a payslip again when it is confirmed.
        employment.action_payslip_done()
        self.assertEqual(employment.state, "done")
        self.assertEqual(self._line(employment, "TAXBASE_TAKEN"), 428.0)
        self.assertEqual(self._tax(employment), -51.90)

    def test_linked_payslip_is_frozen_once_the_principal_is_confirmed(self):
        principal, linked = self._pair()
        agreement = self._slip(linked)
        employment = self._slip(principal)
        employment.action_payslip_done()
        # Computed again with the same base: nothing to object to.
        agreement.compute_sheet()
        linked.version_id.wage = 500.0
        with self.assertRaises(UserError) as error:
            agreement.compute_sheet()
        self.assertIn(employment.display_name, str(error.exception))
        with self.assertRaises(UserError):
            agreement.action_payslip_cancel()
        with self.assertRaises(UserError):
            agreement.refund_sheet()
        with self.assertRaises(UserError):
            agreement.unlink()
        # A new payslip of the linked record in the month is refused too.
        with self.assertRaises(UserError):
            self._slip(linked)
        self.assertEqual(self._tax(employment), -19.37)
        self.assertEqual(employment.state, "done")

    def test_refunding_the_principal_releases_the_linked_payslip(self):
        principal, linked = self._pair()
        agreement = self._slip(linked)
        employment = self._slip(principal)
        employment.action_payslip_done()
        employment.refund_sheet()
        refund = self.env["hr.payslip"].search(
            [("employee_id", "=", principal.id), ("credit_note", "=", True)]
        )
        # The refund is the payslip over again: the whole tax of the month.
        self.assertEqual(self._tax(refund), -19.37)
        linked.version_id.wage = 500.0
        agreement.compute_sheet()
        self.assertEqual(self._line(agreement, "TAXBASE_MOVED"), 428.0)
        corrected = self._slip(principal)
        self.assertEqual(self._tax(corrected), -51.90)

    def test_refund_of_a_linked_payslip_takes_its_base_back(self):
        principal, linked = self._pair()
        agreement = self._slip(linked)
        agreement.action_payslip_done()
        employment = self._slip(principal)
        self.assertEqual(self._tax(employment), -19.37)
        agreement.refund_sheet()
        # Neither the refunded payslip nor its refund moves a base any more.
        with self.assertRaises(UserError):
            employment.with_context(without_compute_sheet=True).action_payslip_done()
        employment.compute_sheet()
        self.assertNotIn("TAXBASE_TAKEN", self._codes(employment))
        self.assertEqual(self._tax(employment), 0.0)
        # The agreement paid again, with 500.
        linked.version_id.wage = 500.0
        self._slip(linked)
        employment.compute_sheet()
        self.assertEqual(self._tax(employment), -51.90)

    def test_link_cannot_change_in_a_month_half_done(self):
        principal, linked = self._pair()
        agreement = self._slip(linked)
        employment = self._slip(principal)
        # Both payslips open: the link may still go, and comes back.
        linked.l10n_sk_tax_principal_id = False
        linked.l10n_sk_tax_principal_id = principal
        agreement.action_payslip_done()
        # The agreement's base is confirmed as moved and nothing taxed it yet.
        with self.assertRaises(ValidationError):
            linked.l10n_sk_tax_principal_id = False
        employment.action_payslip_done()
        # Both confirmed: the month is settled.
        linked.l10n_sk_tax_principal_id = False
        self.assertEqual(self._tax(employment), -19.37)

    def test_link_cannot_change_while_the_linked_payslip_is_open(self):
        principal, linked = self._pair()
        self._slip(linked)
        self._slip(principal).action_payslip_done()
        # Unlinked and computed again, the base would be taxed twice.
        with self.assertRaises(ValidationError):
            linked.l10n_sk_tax_principal_id = False

    def test_one_payslip_of_the_principal_takes_the_month_over(self):
        principal, linked = self._pair()
        self._slip(linked)
        first = self._slip(principal)
        second = self._slip(principal)
        self.assertEqual(self._line(first, "TAXBASE_TAKEN"), 256.80)
        self.assertNotIn("TAXBASE_TAKEN", self._codes(second))
        self.assertEqual(self._tax(second), 0.0)

    def test_payslip_computed_under_another_link_is_not_confirmed(self):
        principal, linked = self._pair()
        agreement = self._slip(linked)
        linked.l10n_sk_tax_principal_id = False
        # Still shows no tax and a base moved to a record that will not take it.
        with self.assertRaises(UserError):
            agreement.with_context(without_compute_sheet=True).action_payslip_done()
        agreement.compute_sheet()
        agreement.action_payslip_done()
        self.assertEqual(self._tax(agreement), -48.79)

    # ------------------------------------------------------------------
    # wage garnishment
    # ------------------------------------------------------------------
    def test_garnishment_is_refused_on_payslips_taxed_together(self):
        principal, linked = self._pair()
        with self.assertRaises(UserError) as error:
            self._slip(linked, inputs=[("GARNISHMENT", 100.0)])
        self.assertIn("§ 69", str(error.exception))
        self._slip(linked)
        with self.assertRaises(UserError):
            self._slip(principal, inputs=[("GARNISHMENT", 100.0)])

    def test_garnishment_of_a_principal_without_linked_payslips(self):
        principal, _linked = self._pair(wage=2000.0)
        slip = self._slip(principal, inputs=[("GARNISHMENT", 100.0)])
        self.assertEqual(self._line(slip, "GARNISHMENT"), -100.0)

    # ------------------------------------------------------------------
    # the year
    # ------------------------------------------------------------------
    def _confirmed_month(self, employee, month):
        slip = self._draft(employee, month=month)
        slip.compute_sheet()
        slip.action_payslip_done()
        return slip

    def test_annual_reconciliation_gathers_the_person(self):
        """January and February 2026 of both records, one reconciliation.

        Bases 2 x (342.40 + 256.80) = 1 198.40, advances 2 x 19.37 = 38.74.
        """
        principal, linked = self._pair()
        for month in (1, 2):
            self._confirmed_month(linked, month)
            self._confirmed_month(principal, month)
        Reconciliation = self.env["l10n.sk.tax.reconciliation"]
        rec = Reconciliation.create(
            {"employee_id": principal.id, "company_id": self.company.id, "year": 2026}
        )
        rec.action_compute()
        self.assertEqual(rec.annual_tax_base, 1198.40)
        self.assertEqual(rec.annual_advance_tax, 38.74)
        # Not for the linked record alone.
        with self.assertRaises(ValidationError) as error:
            Reconciliation.create(
                {"employee_id": linked.id, "company_id": self.company.id, "year": 2026}
            )
        self.assertIn("Employment", str(error.exception))

    def test_one_annual_reconciliation_for_one_birth_number(self):
        principal, linked = self._pair(link=False)
        Reconciliation = self.env["l10n.sk.tax.reconciliation"]
        Reconciliation.create(
            {"employee_id": principal.id, "company_id": self.company.id, "year": 2026}
        )
        with self.assertRaises(ValidationError):
            Reconciliation.create(
                {"employee_id": linked.id, "company_id": self.company.id, "year": 2026}
            )
        # Another year, and another person, are free.
        Reconciliation.create(
            {"employee_id": linked.id, "company_id": self.company.id, "year": 2025}
        )
        stranger = self._record("Stranger", 1000.0, number="900202/4321")
        Reconciliation.create(
            {"employee_id": stranger.id, "company_id": self.company.id, "year": 2026}
        )
