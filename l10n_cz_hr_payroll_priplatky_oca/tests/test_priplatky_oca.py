# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The Czech surcharges as they land on an OCA-engine payslip.

Figures are hand-derived from the statute and the shipped rate data, not read
back off the rules under test.
"""

from datetime import date

from odoo.tests import TransactionCase, tagged

MOD = "l10n_cz_hr_payroll_priplatky"


@tagged("post_install", "-at_install")
class TestCzPriplatkyOca(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "CZ Priplatky Co", "country_id": cls.env.ref("base.cz").id}
        )
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(context=dict(cls.env.context,
                                       allowed_company_ids=cls.company.ids))
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Příplatkový Zaměstnanec", "company_id": cls.company.id}
        )
        # On 19.0 the contract IS hr.version, reached through the employee;
        # the OCA engine merely kept the field name contract_id for it.
        cls.contract = cls.employee.version_id
        cls.contract.write(
            {
                "date_version": date(2026, 1, 1),
                "contract_date_start": date(2026, 1, 1),
                "wage": 50000.0,
            }
        )

    def _payslip(self, inputs=None):
        vals = {
            "name": "Test",
            "employee_id": self.employee.id,
            "contract_id": self.contract.id,
            "company_id": self.company.id,
            "date_from": date(2026, 6, 1),
            "date_to": date(2026, 6, 30),
        }
        if inputs:
            vals["input_line_ids"] = [
                (0, 0, {
                    "name": code,
                    "code": code,
                    "amount": hours,
                    "contract_id": self.contract.id,
                })
                for code, hours in inputs.items()
            ]
        return self.env["hr.payslip"].create(vals)

    def test_the_mixin_is_on_the_oca_payslip(self):
        self.assertIn("cz.surcharge.payslip.mixin",
                      self.env["hr.payslip"]._inherit)

    def test_work100_is_gross_on_this_engine(self):
        """The OCA engine leaves absences inside WORK100; the mixin defaults
        to False and this bridge must flip it, or absences get paid twice."""
        self.assertTrue(self.env["hr.payslip"]._l10n_cz_work100_is_gross())

    def test_hours_are_read_off_the_inputs(self):
        slip = self._payslip({"NOCNI": 12.0, "PRESCAS": 5.0})
        self.assertEqual(slip._l10n_cz_surcharge_hours("NOCNI"), 12.0)
        self.assertEqual(slip._l10n_cz_surcharge_hours("PRESCAS"), 5.0)
        self.assertEqual(slip._l10n_cz_surcharge_hours("VIKEND"), 0.0)

    def test_the_five_rules_are_installed(self):
        for code in ("PRESCAS", "SVATEK", "NOCNI", "VIKEND", "ZTIZENE"):
            rule = self.env["hr.salary.rule"].search(
                [("code", "=", "PRIPLATEK_" + code)], limit=1
            )
            self.assertTrue(rule, "missing salary rule for %s" % code)

    def test_difficult_environment_needs_a_factor_count(self):
        """§ 117 pays per aggravating influence, so hours alone must not pay.

        This is the trap the Slovak module does not have: there, difficult
        work is a percentage with no multiplier. Here a contract that records
        difficult hours but no influences owes nothing.
        """
        slip = self._payslip({"ZTIZENE": 8.0})
        self.assertEqual(slip._l10n_cz_surcharge_hours("ZTIZENE"), 8.0)
        self.assertEqual(slip._l10n_cz_difficult_factors(), 0)
        self.assertEqual(slip._l10n_cz_surcharge_amount("ZTIZENE"), 0.0)
