# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""One declaration of the taxpayer for one employer.

Two employee records with the same birth number in one company are one
taxpayer at one employer (an employment and an agreement beside it). § 36 ods.
6 zákona č. 595/2003 Z. z. has the declaration given to an employer, so the
box may be ticked on one of the records at a time.

The box belongs to the payroll engines; this file runs with either of them
and is skipped where neither is installed.
"""

from datetime import date
from unittest import SkipTest

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTaxDeclarationGuard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if "l10n_sk_tax_declaration_signed" not in cls.env["hr.version"]._fields:
            raise SkipTest("no Slovak payroll engine is installed")
        cls.company = cls.env["res.company"].create(
            {"name": "SK one declaration", "country_id": cls.env.ref("base.sk").id}
        )
        cls.other_company = cls.env["res.company"].create(
            {"name": "SK other employer", "country_id": cls.env.ref("base.sk").id}
        )
        cls.env.user.company_ids |= cls.company | cls.other_company

    def _record(self, name, birth_number="850101/1234", signed=False,
                start=date(2026, 1, 1), end=False, company=None):
        return self.env["hr.employee"].create(
            {
                "name": name,
                "company_id": (company or self.company).id,
                "identification_id": birth_number,
                "date_version": start,
                "contract_date_start": start,
                "contract_date_end": end,
                "l10n_sk_tax_declaration_signed": signed,
            }
        )

    def test_second_declaration_of_one_person_is_refused(self):
        self._record("Employment", signed=True)
        with self.assertRaises(ValidationError):
            self._record("Agreement", signed=True)
        agreement = self._record("Agreement")
        with self.assertRaises(ValidationError):
            agreement.l10n_sk_tax_declaration_signed = True

    def test_the_slash_of_a_birth_number_does_not_matter(self):
        self._record("Employment", birth_number="850101/1234", signed=True)
        with self.assertRaises(ValidationError):
            self._record("Agreement", birth_number="8501011234", signed=True)

    def test_a_birth_number_entered_later_is_checked(self):
        self._record("Employment", signed=True)
        agreement = self._record("Agreement", birth_number=False, signed=True)
        with self.assertRaises(ValidationError):
            agreement.identification_id = "850101/1234"

    def test_records_without_a_birth_number_are_not_matched(self):
        self._record("First", birth_number=False, signed=True)
        self._record("Second", birth_number=False, signed=True)
        self._record("Third", birth_number=" ", signed=True)
        self._record("Fourth", birth_number="/", signed=True)

    def test_another_person_keeps_the_declaration(self):
        self._record("One person", birth_number="850101/1234", signed=True)
        self._record("Another person", birth_number="900202/4321", signed=True)

    def test_another_employer_keeps_the_declaration(self):
        # A matter between the employee and the two employers (§ 36 ods. 3),
        # not something one company's records can show.
        self._record("Here", signed=True)
        self._record("There", signed=True, company=self.other_company)

    def test_contracts_that_do_not_share_a_day_both_keep_it(self):
        self._record("To March", signed=True, end=date(2026, 3, 31))
        later = self._record("From April", signed=True, start=date(2026, 4, 1))
        # Moved onto a day the other contract still runs: refused.
        with self.assertRaises(ValidationError):
            later.contract_date_start = date(2026, 3, 31)

    def test_a_new_version_takes_the_declaration_over(self):
        """Unticked from 1 July on one record, ticked from 1 July on the other."""
        first = self._record("Employment", signed=True)
        second = self._record("Agreement")
        first.create_version(
            {"date_version": date(2026, 7, 1), "l10n_sk_tax_declaration_signed": False}
        )
        version = second.create_version(
            {"date_version": date(2026, 7, 1), "l10n_sk_tax_declaration_signed": True}
        )
        # Moved before the day the first record gave it up: refused.
        with self.assertRaises(ValidationError):
            version.date_version = date(2026, 6, 30)

    def test_versions_of_one_record_do_not_conflict(self):
        record = self._record("Employment", signed=True)
        record.create_version({"date_version": date(2026, 7, 1)})
        self.assertEqual(
            record.version_ids.mapped("l10n_sk_tax_declaration_signed"), [True, True]
        )

    def test_offenders_can_be_listed(self):
        """What the update writes into the log for data that is already wrong."""
        first = self._record("Employment", signed=True)
        second = self._record("Agreement")
        # Data from before the rule: written past the constraint.
        self.env.cr.execute(
            "UPDATE hr_version SET l10n_sk_tax_declaration_signed = TRUE WHERE id = %s",
            [second.version_id.id],
        )
        second.version_id.invalidate_recordset()
        self.assertEqual(
            first.version_id._l10n_sk_tax_declaration_conflicts(), second.version_id
        )
        self.assertEqual(
            self.env["hr.version"]._l10n_sk_tax_declaration_offenders(),
            [(first.version_id, second.version_id)],
        )
