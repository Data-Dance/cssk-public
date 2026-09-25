# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The applicability table, and that every row is answerable for every form."""

from odoo.tests import TransactionCase

from ..applicability import (
    AGREEMENTS,
    ALL_FORMS,
    APPLICABILITY,
    DOBPS,
    DOPC,
    DOVP,
    EMPLOYMENT,
    NEEDS_LEGAL_CONFIRMATION,
    applies,
)


class TestApplicability(TransactionCase):
    def test_the_fund_set_follows_regularity_not_the_agreement(self):
        """The defect the table exists to prevent, stated as a property."""
        for form in ALL_FORMS:
            self.assertTrue(applies("SICKNESS_INSURANCE", form, income_regular=True))
            self.assertFalse(applies("SICKNESS_INSURANCE", form, income_regular=False))
            self.assertTrue(applies("UNEMPLOYMENT_INSURANCE", form, True))
            self.assertFalse(applies("UNEMPLOYMENT_INSURANCE", form, False))

    def test_pension_and_disability_are_owed_by_everyone(self):
        for form in ALL_FORMS:
            for regular in (True, False):
                self.assertTrue(applies("PENSION_INSURANCE", form, regular))
                self.assertTrue(applies("DISABILITY_INSURANCE", form, regular))

    def test_min_wage_claim_is_employment_only(self):
        """§ 120 covers a pracovný pomer; dohodári get the hourly minimum."""
        self.assertTrue(applies("MIN_WAGE_CLAIM", EMPLOYMENT))
        for form in AGREEMENTS:
            self.assertFalse(applies("MIN_WAGE_CLAIM", form))

    def test_holiday_is_employment_only(self):
        self.assertTrue(applies("HOLIDAY_ENTITLEMENT", EMPLOYMENT))
        for form in (DOVP, DOPC, DOBPS):
            self.assertFalse(applies("HOLIDAY_ENTITLEMENT", form))

    def test_sickness_compensation_needs_sickness_insurance(self):
        self.assertTrue(applies("SICKNESS_COMPENSATION", DOPC, income_regular=True))
        self.assertFalse(applies("SICKNESS_COMPENSATION", DOVP, income_regular=False))

    def test_an_unknown_concept_raises(self):
        """A default would let a typo look like a legal answer."""
        with self.assertRaises(KeyError):
            applies("NEEXISTUJE", EMPLOYMENT)

    def test_a_concept_awaiting_confirmation_raises_with_its_reason(self):
        for concept in NEEDS_LEGAL_CONFIRMATION:
            with self.assertRaises(KeyError) as caught:
                applies(concept, EMPLOYMENT)
            self.assertIn("legal confirmation", str(caught.exception))

    def test_every_row_is_answerable_for_every_form(self):
        """Adding a form must force every row to be revisited, not skipped."""
        for concept in APPLICABILITY:
            for form in ALL_FORMS:
                for regular in (True, False):
                    self.assertIsInstance(applies(concept, form, regular), bool)
