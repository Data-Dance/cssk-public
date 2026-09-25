# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""What ``_cssk_verify_registry`` reports, and the distinction it exists for.

Every test here stubs the provider's probe. Nothing reaches the network: a
suite that depends on ORSF being up fails for reasons that have nothing to do
with the code, and would not run in CI at all.

The payloads are real — captured from ``api.orsf.sk/v1/lookup`` on 2026-09-07
for Data Dance s.r.o. (a company) and Jana Havelková-HAVELKA (a sole trader,
whose address the register locks for GDPR).
"""
import unittest
from unittest.mock import patch

from odoo.tests.common import TransactionCase

#: The provider is discovered, not depended on, so it may simply not be here.
#: Skipping is honest; asserting would fail a deployment that never intended
#: to verify Slovak companies in the first place.
PROVIDER_MODEL = "partner.autocomplete.provider.orsf_sk"

COMPANY = {
    "ico": "54093431",
    "dic": "2121576435",
    "icDph": "SK2121576435",
    "name": "Data Dance s.r.o.",
    "status": "aktívna",
    "dissolvedOn": None,
    "address": {"street": "Nová 1184/38", "city": "Veľký Biel",
                "psc": "90024", "country": "SK"},
    "isVatPayer": True,
    "addressLocked": False,
}

SOLE_TRADER = {
    "ico": "32112475",
    "dic": "1020173099",
    "icDph": None,
    "name": "Jana Havelková-HAVELKA",
    "status": "aktívna",
    "dissolvedOn": None,
    "address": {"street": None, "city": "Bratislava - mestská časť Ružinov",
                "psc": None, "country": "SK"},
    "isVatPayer": False,
    "addressLocked": True,
}

DISSOLVED = dict(COMPANY, status="zrušená", dissolvedOn="2024-03-31")


class TestVerifyNoProvider(TransactionCase):
    """Behaviour that must hold whether or not any provider is installed."""

    def test_a_country_outside_cz_sk_is_unsupported(self):
        res = self.env["res.partner"]._cssk_verify_registry("54093431", "DE")
        self.assertEqual(res["outcome"], "unsupported")

    def test_a_country_with_no_register_is_unsupported_not_rejected(self):
        """"We have no register for Poland" is a fact about us, not about the
        customer. The caller must be able to tell it apart from "this company
        does not exist" so it can let them through to a human instead of
        turning away every sale outside CZ/SK."""
        res = self.env["res.partner"]._cssk_verify_registry("1234567890", "PL")
        self.assertEqual(res["outcome"], "unsupported")
        self.assertNotEqual(res["outcome"], "absent")


class TestVerifyRegistry(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if PROVIDER_MODEL not in cls.env:
            raise unittest.SkipTest(
                f"{PROVIDER_MODEL} is not installed; nothing to verify against"
            )
        cls.Partner = cls.env["res.partner"]
        cls.Lookup = cls.env["cssk.registry.lookup"]
        cls.provider_cls = type(cls.env[PROVIDER_MODEL])

    def setUp(self):
        super().setUp()
        # The cache is a real table, and a row left by an earlier run -- or by
        # somebody actually using the site -- answers before the stub does.
        # Without this the results depend on the database's history rather
        # than on the code, which is the worst kind of green.
        self.Lookup.search([]).unlink()

    def _probe(self, outcome, body=None):
        """Stub the provider's transport with one canned outcome."""
        return patch.object(
            self.provider_cls, "_orsf_lookup_probe",
            lambda self, ico: (outcome, body),
        )

    def _forbid_register(self):
        """Assert the register is not reached at all."""
        return patch.object(
            self.provider_cls, "_orsf_lookup_probe",
            side_effect=AssertionError("the register must not be asked"),
        )

    # -- the register is never asked ---------------------------------------

    def test_a_bad_checksum_never_reaches_the_register(self):
        """Free, instant, and it is what rejects the junk a signup collects.
        Asking the register would spend a request per keystroke to be told
        the same thing."""
        with self._forbid_register():
            for value in ("12345", "Test", "TRAIVA, s.r.o.", "1"):
                res = self.Partner._cssk_verify_registry(value, "SK")
                self.assertEqual(res["outcome"], "invalid", f"{value!r}")

    # -- the distinction this module exists for ----------------------------

    def test_absent_and_unavailable_are_not_the_same(self):
        """A gate that collapses these turns an outage into a wall of
        rejections, or opens itself every time the register hiccups.

        ``use_cache=False`` on both because ``absent`` is a cached answer:
        without it the second call is served the first one's ``absent`` and
        this passes for the wrong reason.
        """
        with self._probe("absent"):
            absent = self.Partner._cssk_verify_registry(
                "54093431", "SK", use_cache=False
            )
        with self._probe("unavailable"):
            down = self.Partner._cssk_verify_registry(
                "54093431", "SK", use_cache=False
            )
        self.assertEqual(absent["outcome"], "absent")
        self.assertEqual(down["outcome"], "unavailable")

    def test_an_outage_does_not_overwrite_a_cached_answer(self):
        """The corollary: a register that goes down after answering must not
        erase what it already told us."""
        with self._probe("ok", COMPANY):
            self.Partner._cssk_verify_registry("54093431", "SK")
        with self._probe("unavailable"):
            during = self.Partner._cssk_verify_registry("54093431", "SK")
        # Served from cache, so the outage is invisible to the caller.
        self.assertEqual(during["outcome"], "verified")
        self.assertTrue(during["cached"])
        row = self.Lookup.search([("registry", "=", "54093431")])
        self.assertEqual(row.outcome, "verified")

    # -- a verified company -------------------------------------------------

    def test_verified_carries_what_the_register_said(self):
        with self._probe("ok", COMPANY):
            res = self.Partner._cssk_verify_registry("54093431", "SK")
        self.assertEqual(res["outcome"], "verified")
        self.assertEqual(res["name"], "Data Dance s.r.o.")
        self.assertEqual(res["city"], "Veľký Biel")
        self.assertEqual(res["zip"], "90024")
        self.assertEqual(res["tax_id"], "2121576435")
        self.assertEqual(res["vat"], "SK2121576435")
        self.assertEqual(res["source"], "ORSF")
        self.assertTrue(res["active"])

    def test_an_unpadded_number_verifies_the_same_company(self):
        with self._probe("ok", COMPANY):
            res = self.Partner._cssk_verify_registry("  54 093 431 ", "SK")
        self.assertEqual(res["outcome"], "verified")
        self.assertEqual(res["registry"], "54093431")

    def test_a_dissolved_company_verifies_but_is_not_active(self):
        """It exists. That is not the same as being able to trade with it,
        and the provisioning gate reads this field."""
        with self._probe("ok", DISSOLVED):
            res = self.Partner._cssk_verify_registry("54093431", "SK")
        self.assertEqual(res["outcome"], "verified")
        self.assertFalse(res["active"])

    def test_a_sole_traders_locked_address_is_not_an_error(self):
        """ORSF withholds street and PSČ for a natural person. Every identity
        field still comes back, which is what a gate needs; the customer types
        the two missing lines."""
        with self._probe("ok", SOLE_TRADER):
            res = self.Partner._cssk_verify_registry("32112475", "SK")
        self.assertEqual(res["outcome"], "verified")
        self.assertEqual(res["name"], "Jana Havelková-HAVELKA")
        self.assertTrue(res["active"])
        self.assertEqual(res["city"], "Bratislava - mestská časť Ružinov")
        self.assertFalse(res["street"])
        self.assertFalse(res["zip"])
        # Not a VAT payer: no IČ DPH invented from the DIČ.
        self.assertFalse(res["vat"])
        self.assertEqual(res["tax_id"], "1020173099")

    # -- caching ------------------------------------------------------------

    def test_a_verified_answer_is_cached(self):
        with self._probe("ok", COMPANY):
            first = self.Partner._cssk_verify_registry("54093431", "SK")
        self.assertFalse(first["cached"])
        # The register is now forbidden: a second call must not reach it.
        with self._forbid_register():
            second = self.Partner._cssk_verify_registry("54093431", "SK")
        self.assertTrue(second["cached"])
        self.assertEqual(second["name"], first["name"])
        self.assertEqual(second["outcome"], "verified")

    def test_an_absent_answer_is_cached_too(self):
        """This is what blunts a scan of the number space from a public form."""
        with self._probe("absent"):
            self.Partner._cssk_verify_registry("54093431", "SK")
        row = self.Lookup.search([("registry", "=", "54093431")])
        self.assertEqual(row.outcome, "absent")

    def test_an_outage_is_never_cached(self):
        """Caching a failure would extend one outage into a long one."""
        with self._probe("unavailable"):
            self.Partner._cssk_verify_registry("54093431", "SK")
        self.assertFalse(self.Lookup.search([("registry", "=", "54093431")]))

    def test_use_cache_false_asks_again(self):
        with self._probe("ok", COMPANY):
            self.Partner._cssk_verify_registry("54093431", "SK")
        with self._probe("ok", DISSOLVED):
            fresh = self.Partner._cssk_verify_registry(
                "54093431", "SK", use_cache=False
            )
        self.assertFalse(fresh["cached"])
        self.assertFalse(fresh["active"])

    def test_a_re_ask_replaces_the_cached_row(self):
        """One row per company: the cache must not grow a history."""
        with self._probe("ok", COMPANY):
            self.Partner._cssk_verify_registry("54093431", "SK")
        with self._probe("ok", DISSOLVED):
            self.Partner._cssk_verify_registry("54093431", "SK", use_cache=False)
        rows = self.Lookup.search([("registry", "=", "54093431")])
        self.assertEqual(len(rows), 1)
        self.assertFalse(rows.active_subject)

    def test_an_expired_row_is_not_served(self):
        from datetime import timedelta

        from odoo import fields

        with self._probe("ok", COMPANY):
            self.Partner._cssk_verify_registry("54093431", "SK")
        row = self.Lookup.search([("registry", "=", "54093431")])
        row.fetched_at = fields.Datetime.now() - timedelta(days=30)
        with self._probe("ok", DISSOLVED):
            res = self.Partner._cssk_verify_registry("54093431", "SK")
        self.assertFalse(res["cached"])
        self.assertFalse(res["active"])


class TestNameVerdict(TransactionCase):
    """The bands, and the fact that they were measured rather than chosen.

    The real distribution against ORSF is bimodal — 44 of 45 companies scored
    exactly 1.000 and one scored 0.716 — so 0.90 is a wide margin, not a fine
    line. Anything that moves the ratio invalidates these numbers.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env["res.partner"]

    def _verdict(self, typed, official):
        return self.Partner._cssk_registry_name_verdict(typed, official)

    def test_formatting_differences_are_the_same_company(self):
        for typed, official in (
            ("Data Dance s.r.o.", "Data Dance s.r.o."),
            ("DEMI Šport plus, s.r.o.", "DEMI šport plus, s.r.o."),
            ("AGEM COMPUTERS, spol. s r.o.", "AGEM COMPUTERS, spol.s r.o."),
            ("Europe Express s. r. o.", "Europe Express, s. r. o."),
            ("Vitaminátor s.r.o.", "VITAMINÁTOR s.r.o."),
        ):
            verdict, score = self._verdict(typed, official)
            self.assertEqual(verdict, "match", f"{typed!r} vs {official!r}")
            self.assertEqual(score, 1.0)

    def test_a_branch_suffix_goes_to_a_human(self):
        """The one real mid-band case on the calibration set."""
        verdict, score = self._verdict(
            "Nakladatelství FORUM s.r.o.",
            "Nakladatelství FORUM s.r.o., organizačná zložka",
        )
        self.assertEqual(verdict, "review")
        self.assertGreater(score, 0.60)
        self.assertLess(score, 0.90)

    def test_a_different_legal_form_is_not_the_same_company(self):
        """Legal forms are canonicalised, never stripped: "Alfa s.r.o." and
        "Alfa a.s." are two companies, and merging them would put one
        supplier's bill against the other."""
        verdict, _score = self._verdict("Alfa s.r.o.", "Alfa a.s.")
        self.assertNotEqual(verdict, "match")

    def test_an_unrelated_name_is_a_mismatch(self):
        verdict, _score = self._verdict("Totally Other s.r.o.", "Data Dance s.r.o.")
        self.assertEqual(verdict, "mismatch")

    def test_nothing_to_compare_is_not_a_mismatch(self):
        """An empty name must never read as "wrong company" — that would
        reject everyone whose browser did not run the prefill."""
        for typed, official in (("", "Data Dance s.r.o."), ("Data Dance s.r.o.", "")):
            verdict, score = self._verdict(typed, official)
            self.assertEqual(verdict, "unknown")
            self.assertEqual(score, 0.0)


#: Real ARES payloads, captured 2026-09-08. TRAIVA is VAT-registered; Romana
#: Nahorniaková is not, and ARES answers `dic: null` for her.
ARES_VAT_PAYER = {
    "ico": "25380141",
    "obchodniJmeno": "TRAIVA, s.r.o.",
    "dic": "CZ25380141",
    "sidlo": {"textovaAdresa": "Pohraniční 2911/13b, Vítkovice, 70300 Ostrava",
              "nazevObce": "Ostrava", "psc": 70300},
    "seznamRegistraci": {"stavZdrojeDph": "AKTIVNI"},
}
ARES_NOT_REGISTERED = {
    "ico": "21924660",
    "obchodniJmeno": "Romana Nahorniaková",
    "dic": None,
    "sidlo": {"textovaAdresa": "Máchova 402/55, 74101 Nový Jičín",
              "nazevObce": "Nový Jičín", "psc": 74101},
    "seznamRegistraci": {"stavZdrojeDph": "NEEXISTUJICI"},
}
#: The dangerous shape: a number still present after deregistration.
ARES_DEREGISTERED = dict(
    ARES_VAT_PAYER, seznamRegistraci={"stavZdrojeDph": "ZANIKLY"}
)


class TestVatIsNeverABareNumber(TransactionCase):
    """`vat` decides whether VAT is charged, so what goes in it is not cosmetic.

    Odoo 19's `_get_first_matching_fpos` demoted `vat_required` to a filter
    over `bool(partner.vat and partner.vat != '/')` — no format check anywhere.
    So any non-empty string routes an EU partner to a reverse-charge position
    and waives the VAT. A bare IČO, or a stale number on a deregistered payer,
    is an under-collected-VAT event.
    """

    def setUp(self):
        super().setUp()
        self.Partner = self.env["res.partner"]

    def test_a_registered_payer_gets_a_prefixed_vat(self):
        parsed = self.Partner._cssk_registry_parse_ares(ARES_VAT_PAYER)
        self.assertEqual(parsed["vat"], "CZ25380141")
        self.assertEqual(parsed["tax_id"], "CZ25380141")

    def test_a_company_that_never_registered_gets_no_vat(self):
        """Empty is correct: it falls through to the consumer position and
        VAT is charged."""
        parsed = self.Partner._cssk_registry_parse_ares(ARES_NOT_REGISTERED)
        self.assertFalse(parsed["vat"])

    def test_a_deregistered_payer_gets_no_vat_even_though_dic_remains(self):
        """"Never registered" and "no longer registered" are different facts,
        and only the first is visible in `dic`."""
        parsed = self.Partner._cssk_registry_parse_ares(ARES_DEREGISTERED)
        self.assertFalse(parsed["vat"])
        # Still their tax identifier, just not a VAT number.
        self.assertEqual(parsed["tax_id"], "CZ25380141")

    def test_an_unprefixed_number_is_never_written_as_vat(self):
        """The guard that would have caught the production incident: a bare
        IČO in `vat` is what waived VAT on order S00197."""
        bare = dict(ARES_VAT_PAYER, dic="25380141")
        self.assertFalse(self.Partner._cssk_registry_parse_ares(bare)["vat"])

    def test_the_slovak_side_holds_the_same_line(self):
        parsed = self.Partner._cssk_registry_parse(COMPANY)
        self.assertEqual(parsed["vat"], "SK2121576435")
        # A sole trader who is not a VAT payer: icDph is null.
        self.assertFalse(self.Partner._cssk_registry_parse(SOLE_TRADER)["vat"])

    def test_a_slovak_dic_is_never_promoted_to_a_vat_number(self):
        """The SK trap: DIČ and IČ DPH are different identifiers, and a
        subject can hold a DIČ without being a VAT payer at all."""
        parsed = self.Partner._cssk_registry_parse(SOLE_TRADER)
        self.assertEqual(parsed["tax_id"], "1020173099")
        self.assertFalse(parsed["vat"])
