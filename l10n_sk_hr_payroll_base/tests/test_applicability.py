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
    DISABILITY,
    DISABILITY_OVER_70,
    EARLY_OLD_AGE,
    NEEDS_LEGAL_CONFIRMATION,
    OLD_AGE,
    PENSION_TYPES,
    SERVICE_AT_AGE,
    applies,
)


class TestApplicability(TransactionCase):
    def test_the_fund_set_follows_regularity_not_the_agreement(self):
        """The defect the table exists to prevent, stated as a property."""
        for form in (EMPLOYMENT, DOVP, DOPC):
            self.assertTrue(applies("SICKNESS_INSURANCE", form, income_regular=True))
            self.assertFalse(applies("SICKNESS_INSURANCE", form, income_regular=False))
            self.assertTrue(applies("UNEMPLOYMENT_INSURANCE", form, True))
            self.assertFalse(applies("UNEMPLOYMENT_INSURANCE", form, False))

    def test_dobps_student_is_never_sickness_or_unemployment_insured(self):
        """§ 4 ods. 1 písm. a) zákona 461/2003: "okrem fyzickej osoby v právnom
        vzťahu na základe dohody o brigádnickej práci študentov" — whatever
        the regularity of the income (pension only, § 4 ods. 2 písm. b) bod 1)."""
        for regular in (True, False):
            for concept in ("SICKNESS_INSURANCE", "UNEMPLOYMENT_INSURANCE",
                            "SHORTTIME_CONTRIBUTION", "SICKNESS_COMPENSATION"):
                self.assertFalse(applies(concept, DOBPS, regular), concept)
            self.assertTrue(applies("PENSION_INSURANCE", DOBPS, regular))

    def test_pension_and_disability_are_owed_by_everyone(self):
        for form in ALL_FORMS:
            for regular in (True, False):
                self.assertTrue(applies("PENSION_INSURANCE", form, regular))
                self.assertTrue(applies("DISABILITY_INSURANCE", form, regular))

    def test_a_dohodar_with_a_pension_is_pension_insured_only(self):
        """§ 4 ods. 1 písm. b) zákona 461/2003: a DoVP/DoPČ holder with any
        dôchodok is no zamestnanec for sickness or unemployment, regular
        income or not; § 4 ods. 2 keeps them pension-insured."""
        for form in (DOVP, DOPC):
            for pension in PENSION_TYPES:
                for concept in ("SICKNESS_INSURANCE", "UNEMPLOYMENT_INSURANCE",
                                "SICKNESS_COMPENSATION"):
                    self.assertFalse(
                        applies(concept, form, True, pension),
                        "%s / %s / %s" % (concept, form, pension))
                self.assertTrue(applies("PENSION_INSURANCE", form, True, pension))

    def test_unemployment_follows_par_19_on_employment(self):
        """§ 19 ods. 3 písm. b): no unemployment insurance after a starobný,
        predčasný starobný or > 70 % invalidný dôchodok — but a pracovný pomer
        stays sickness-insured, and a ≤ 70 % invalidný pensioner keeps both."""
        for pension in (OLD_AGE, EARLY_OLD_AGE, DISABILITY_OVER_70):
            self.assertFalse(applies("UNEMPLOYMENT_INSURANCE", EMPLOYMENT, True, pension))
            self.assertTrue(applies("SICKNESS_INSURANCE", EMPLOYMENT, True, pension))
        self.assertTrue(applies("UNEMPLOYMENT_INSURANCE", EMPLOYMENT, True, DISABILITY))

    def test_disability_premium_follows_par_128(self):
        """§ 128 ods. 3: no invalidné after a starobný / predčasný starobný
        dôchodok or a výsluhový at dôchodkový vek — on every form — while an
        invalidný pensioner still pays it."""
        for form in ALL_FORMS:
            for pension in (OLD_AGE, EARLY_OLD_AGE, SERVICE_AT_AGE):
                self.assertFalse(applies("DISABILITY_INSURANCE", form, True, pension))
            for pension in (DISABILITY, DISABILITY_OVER_70):
                self.assertTrue(applies("DISABILITY_INSURANCE", form, True, pension))

    def test_short_time_contribution_is_employment_only(self):
        """§ 128 ods. 1 písm. g): "na financovanie podpory zamestnávateľ za
        zamestnanca v pracovnom pomere" — never for a dohoda."""
        self.assertTrue(applies("SHORTTIME_CONTRIBUTION", EMPLOYMENT))
        self.assertTrue(applies("SHORTTIME_CONTRIBUTION", EMPLOYMENT, True, OLD_AGE))
        for form in AGREEMENTS:
            for regular in (True, False):
                self.assertFalse(applies("SHORTTIME_CONTRIBUTION", form, regular))

    def test_an_unknown_pension_type_raises(self):
        with self.assertRaises(KeyError):
            applies("PENSION_INSURANCE", EMPLOYMENT, True, "vdovsky")

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
                    for pension in (False,) + PENSION_TYPES:
                        self.assertIsInstance(
                            applies(concept, form, regular, pension), bool)
