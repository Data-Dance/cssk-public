# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The partner's Entity Type follows the register.

Found on 2026-11-24: a Czech sole trader signed up, the register confirmed
the IČO, and the partner said nothing about being a person rather than a
company. These tests feed ``_cssk_store_verification`` the result dict
directly; how the register's payload becomes ``legal_form`` and
``natural_person`` is pinned in ``test_verify``.
"""
from odoo.tests.common import TransactionCase


def _result(**vals):
    return dict(
        {
            "outcome": "verified",
            "name": "Subject",
            "active": True,
            "name_verdict": "match",
            "name_score": 1.0,
            "legal_form": "",
            "natural_person": False,
        },
        **vals,
    )


class TestPersonTypeFromRegister(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cz = cls.env.ref("base.cz")
        cls.sk = cls.env.ref("base.sk")
        cls.Type = cls.env["cssk.person.type"]

    def _partner(self, country, **vals):
        return self.env["res.partner"].create(
            dict({"name": "Subject", "is_company": True,
                  "country_id": country.id}, **vals))

    def _code(self, partner):
        return partner.l10n_cssk_person_type_id.code

    def test_a_czech_sole_trader_is_a_natural_person(self):
        partner = self._partner(self.cz)
        partner._cssk_store_verification(
            _result(legal_form="101", natural_person=True))
        self.assertEqual(self._code(partner), "CZ-FO")

    def test_a_slovak_sole_trader_is_a_natural_person(self):
        partner = self._partner(self.sk)
        partner._cssk_store_verification(
            _result(legal_form="101", natural_person=True))
        self.assertEqual(self._code(partner), "SK-FO")

    def test_a_person_the_register_names_no_form_for(self):
        """ORSF marks a person by the locked address even where it words the
        legal form in a way nobody has seen."""
        partner = self._partner(self.sk)
        partner._cssk_store_verification(_result(natural_person=True))
        self.assertEqual(self._code(partner), "SK-FO")

    def test_a_company_is_a_legal_entity(self):
        czech = self._partner(self.cz)
        czech._cssk_store_verification(_result(legal_form="112"))
        self.assertEqual(self._code(czech), "CZ-PO")
        slovak = self._partner(self.sk)
        slovak._cssk_store_verification(
            _result(legal_form="Spoločnosť s ručením obmedzeným"))
        self.assertEqual(self._code(slovak), "SK-PO")

    def test_an_answer_without_a_legal_form_says_nothing(self):
        """Every lookup cached before the legal form was read looks like
        this. Reading it as "a company" would mislabel the sole traders."""
        partner = self._partner(self.cz)
        partner._cssk_store_verification(_result())
        self.assertFalse(partner.l10n_cssk_person_type_id)
        legacy = _result()
        del legacy["legal_form"], legacy["natural_person"]
        partner._cssk_store_verification(legacy)
        self.assertFalse(partner.l10n_cssk_person_type_id)

    def test_nothing_is_learnt_from_a_failed_lookup(self):
        partner = self._partner(self.cz)
        for outcome in ("absent", "unavailable", "unsupported", "invalid"):
            partner._cssk_store_verification(
                _result(outcome=outcome, legal_form="101", natural_person=True))
            self.assertFalse(partner.l10n_cssk_person_type_id, outcome)

    def test_a_type_that_contradicts_the_register_is_replaced(self):
        partner = self._partner(
            self.cz,
            l10n_cssk_person_type_id=self.Type._cssk_for_subject("CZ", False).id)
        partner._cssk_store_verification(
            _result(legal_form="101", natural_person=True))
        self.assertEqual(self._code(partner), "CZ-FO")

    def test_a_type_of_the_other_country_is_replaced(self):
        partner = self._partner(
            self.cz,
            l10n_cssk_person_type_id=self.Type._cssk_for_subject("SK", True).id)
        partner._cssk_store_verification(
            _result(legal_form="101", natural_person=True))
        self.assertEqual(self._code(partner), "CZ-FO")

    def test_a_finer_type_that_agrees_is_kept(self):
        farmer = self.Type.create({
            "name": "Farmer", "code": "CZ-FO-SHR", "country_code": "CZ",
            "is_legal_entity": False, "sequence": 90,
        })
        partner = self._partner(self.cz, l10n_cssk_person_type_id=farmer.id)
        partner._cssk_store_verification(
            _result(legal_form="107", natural_person=True))
        self.assertEqual(partner.l10n_cssk_person_type_id, farmer)

    def test_a_partner_outside_the_two_countries_gets_none(self):
        partner = self._partner(self.env.ref("base.de"))
        partner._cssk_store_verification(
            _result(legal_form="101", natural_person=True))
        self.assertFalse(partner.l10n_cssk_person_type_id)
