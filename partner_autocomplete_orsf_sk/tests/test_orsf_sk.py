# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Tests for the ORSF SK autocomplete provider.

Every test stubs ``_orsf_get``: the suite must not depend on a live register
(nor spend its 30 requests/minute budget), and the payloads below are trimmed
copies of real ``GET /companies/{ico}`` and ``GET /search`` responses.
"""

from datetime import date
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

PROVIDER = "partner.autocomplete.provider.orsf_sk"
PROVIDER_PATH = (
    "odoo.addons.partner_autocomplete_orsf_sk.models.partner_autocomplete_provider"
    ".PartnerAutocompleteProviderOrsfSk"
)
GET = f"{PROVIDER_PATH}._orsf_get"

COMPANY = {
    "countryCode": "SK",
    "ico": "31333532",
    "dic": "2020317068",
    "icdph": "SK2020317068",
    "name": "ESET, spol. s r.o.",
    "legalForm": "spoločnosť s ručením obmedzeným",
    "status": "aktívna",
    "nace": "62090",
    "establishedOn": "1992-09-17T00:00:00.000Z",
    "street": "Einsteinova 24",
    "city": "Bratislava - mestská časť Petržalka",
    "psc": "85101",
    "dissolvedOn": None,
    "register": "Obchodný register",
    "registerOffice": "Mestský súd Bratislava III",
    "registerNumber": "Sro/3586/B",
    "velkostLabel": "1 000–1 999 zamestnancov",
    "kind": "company",
    "nationalId": "31333532",
    "taxId": "2020317068",
    "vatId": "SK2020317068",
    "postalCode": "85101",
    "statusCode": "active",
    "vatRegistration": {
        "druhReg": "§4",
        "vatPayerSince": "2000-10-11T00:00:00.000Z",
        "registrationCategory": "§4",
    },
}

# The same subject after its VAT registration was withdrawn: ORSF keeps the
# historical vatRegistration row but clears icdph/vatId.
DEREGISTERED = dict(
    COMPANY,
    icdph=None,
    vatId=None,
    vatRegistration={"druhReg": "§4", "vatPayerSince": "2000-10-11T00:00:00.000Z"},
)

# GET /lookup/{ico} — the identity-only endpoint, verbatim from the live API.
LOOKUP = {
    "ico": "31333532",
    "dic": "2020317068",
    "icDph": "SK2020317068",
    "name": "ESET, spol. s r.o.",
    "legalForm": "spoločnosť s ručením obmedzeným",
    "status": "aktívna",
    "establishedOn": "1992-09-17",
    "dissolvedOn": None,
    "address": {
        "street": "Einsteinova 24",
        "city": "Bratislava - mestská časť Petržalka",
        "psc": "85101",
        "country": "SK",
    },
    "isVatPayer": True,
    "register": "Obchodný register",
    "nace": "62090",
    "sources": ["RPO", "ORSR", "FS_DPH"],
    "addressLocked": False,
}

SEARCH_HITS = {
    "query": "Eset",
    "hits": [
        {
            "ico": "31333532",
            "name": "ESET, spol. s r.o.",
            "icDph": "SK2020317068",
            "status": "aktívna",
            "city": "Bratislava - mestská časť Petržalka",
        },
        {
            "ico": "31338372",
            "name": "ESET-IN s.r.o.",
            "icDph": None,
            "status": "zrušená",
            "city": "Bratislava - mestská časť Dúbravka",
        },
    ],
}


@tagged("post_install", "-at_install")
class TestOrsfSkProvider(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env[PROVIDER]
        cls.param = cls.env["ir.config_parameter"].sudo()

    # -- registry ----------------------------------------------------------

    def test_provider_is_registered(self):
        providers = dict(
            self.env["partner.autocomplete.provider.registry"]._get_available_providers()
        )
        self.assertEqual(providers.get(PROVIDER), "ORSF.SK")

    # -- normalisation helpers --------------------------------------------

    def test_normalise_ico_keeps_leading_zeros(self):
        self.assertEqual(self.provider._orsf_normalise_ico("00151700"), "00151700")
        self.assertEqual(self.provider._orsf_normalise_ico(" 313 335 32 "), "31333532")
        # A DIČ is 10 digits and an IČ DPH 12 characters — neither is an IČO.
        self.assertEqual(self.provider._orsf_normalise_ico("2020317068"), "")
        self.assertEqual(self.provider._orsf_normalise_ico("SK2020317068"), "")
        self.assertEqual(self.provider._orsf_normalise_ico(None), "")

    def test_dates_parse_in_both_shapes(self):
        self.assertEqual(
            self.provider._orsf_date("1992-09-17T00:00:00.000Z"), date(1992, 9, 17)
        )
        self.assertEqual(self.provider._orsf_date("1992-09-17"), date(1992, 9, 17))
        self.assertFalse(self.provider._orsf_date(None))
        self.assertFalse(self.provider._orsf_date("not a date"))

    def test_psc_formatting_follows_the_flag(self):
        self.assertEqual(self.provider._orsf_format_psc("85101"), "851 01")
        self.env.company.orsf_sk_format_psc = False
        self.assertEqual(self.provider._orsf_format_psc("85101"), "85101")

    def test_behaviour_flags_can_actually_be_switched_off(self):
        """They live on res.company because a config_parameter cannot do this.

        ``ir.config_parameter.set_param`` *unlinks* the row for a falsy value
        and ``res.config.settings`` reads an absent key back through the field
        default — so a default-True config_parameter Boolean re-ticks itself.
        """
        settings = self.env["res.config.settings"].create({})
        self.assertTrue(settings.orsf_sk_set_company_registry)
        settings.orsf_sk_set_company_registry = False
        settings.execute()
        self.assertFalse(self.env.company.orsf_sk_set_company_registry)
        self.assertFalse(
            self.env["res.config.settings"].create({}).orsf_sk_set_company_registry
        )

    # -- credentials -------------------------------------------------------

    def test_no_credentials_means_no_session_and_no_request(self):
        self.param.set_param("orsf_sk.login_email", "")
        self.param.set_param("orsf_sk.login_password", "")
        with patch("requests.post") as post:
            self.assertEqual(self.provider._orsf_sign_in(), "")
            post.assert_not_called()
        self.assertIsNone(self.provider._orsf_cookies())

    def test_sign_in_caches_the_token_and_does_not_repeat(self):
        self.param.set_param("orsf_sk.login_email", "bot@example.org")
        self.param.set_param("orsf_sk.login_password", "s3cret")
        response = type("R", (), {
            "status_code": 200,
            "cookies": {"__Secure-orsf.session_token": "tok-1"},
            "json": lambda self: {},
        })()
        with patch("requests.post", return_value=response) as post:
            self.assertEqual(self.provider._orsf_sign_in(), "tok-1")
            # The password is sent, but only to the sign-in URL and only once.
            self.assertEqual(post.call_args.kwargs["json"],
                             {"email": "bot@example.org", "password": "s3cret"})
            self.assertTrue(post.call_args.args[0].endswith("/api/auth/sign-in/email"))
        self.assertEqual(
            self.provider._orsf_cookies(), {"__Secure-orsf.session_token": "tok-1"}
        )
        # Second read comes from cache: no further sign-in.
        with patch("requests.post") as post:
            self.provider._orsf_cookies()
            post.assert_not_called()

    def _cache_session(self, token="tok-cached"):
        self.param.set_param("orsf_sk.login_email", "bot@example.org")
        self.param.set_param("orsf_sk.login_password", "s3cret")
        self.param.set_param("orsf_sk.session_token_cache", token)
        self.param.set_param("orsf_sk.session_token_expiry", "2999-01-01 00:00:00")

    @staticmethod
    def _http(status=200, body=None):
        return type("R", (), {
            "status_code": status,
            "json": lambda self: body if body is not None else {},
            "text": "",
            "headers": {},
        })()

    def test_anonymous_requests_never_carry_the_session(self):
        """Configuring credentials for the graph must not move type-ahead onto
        the account, whose published per-minute limit is lower than anonymous."""
        self._cache_session()
        with patch("requests.get", return_value=self._http(body={"results": []})) as get:
            self.provider._orsf_get("/search", {"q": "ESET"})
            self.provider._orsf_probe("/lookup/31333532")
        for call in get.call_args_list:
            self.assertIsNone(call.kwargs.get("cookies"))
        with patch("requests.post", return_value=self._http(body={"results": []})) as post:
            self.provider._orsf_lookup_batch(["31333532"])
            self.provider._orsf_refresh("31333532")
        for call in post.call_args_list:
            self.assertNotIn("cookies", call.kwargs)

    def test_authenticated_requests_carry_the_session(self):
        self._cache_session("tok-graph")
        with patch("requests.get", return_value=self._http(body={"nodes": []})) as get:
            self.provider._orsf_get("/companies/31333532/graph", authenticated=True)
        self.assertEqual(
            get.call_args.kwargs["cookies"],
            {"__Secure-orsf.session_token": "tok-graph"},
        )

    def test_an_anonymous_401_does_not_sign_in(self):
        self._cache_session()
        with patch("requests.get", return_value=self._http(status=401)), \
                patch("requests.post") as post:
            self.assertIsNone(self.provider._orsf_get("/search", {"q": "x"}))
        post.assert_not_called()

    def test_an_authenticated_401_signs_in_once_and_retries(self):
        self._cache_session("tok-stale")
        signed_in = type("R", (), {
            "status_code": 200,
            "cookies": {"__Secure-orsf.session_token": "tok-fresh"},
            "json": lambda self: {},
        })()
        answers = [self._http(status=401), self._http(body={"nodes": []})]
        with patch("requests.get", side_effect=answers) as get, \
                patch("requests.post", return_value=signed_in) as post:
            body = self.provider._orsf_get("/companies/1/graph", authenticated=True)
        self.assertEqual(body, {"nodes": []})
        self.assertEqual(post.call_count, 1)
        self.assertEqual(
            get.call_args_list[1].kwargs["cookies"],
            {"__Secure-orsf.session_token": "tok-fresh"},
        )

    def test_authenticated_without_credentials_makes_no_request(self):
        self.param.set_param("orsf_sk.login_email", "")
        self.param.set_param("orsf_sk.login_password", "")
        self.param.set_param("orsf_sk.session_token_cache", "")
        with patch("requests.get") as get:
            self.assertEqual(
                self.provider._orsf_probe("/companies/1/graph", authenticated=True),
                ("unavailable", None),
            )
        get.assert_not_called()

    def test_a_refused_sign_in_yields_no_session(self):
        self.param.set_param("orsf_sk.login_email", "bot@example.org")
        self.param.set_param("orsf_sk.login_password", "wrong")
        self.param.set_param("orsf_sk.session_token_cache", "")
        self.param.set_param("orsf_sk.session_token_expiry", "")
        response = type("R", (), {
            "status_code": 401, "cookies": {}, "text": "unauthorized",
            "json": lambda self: {},
        })()
        with patch("requests.post", return_value=response):
            self.assertEqual(self.provider._orsf_sign_in(), "")

    def test_base_url_must_be_http(self):
        self.param.set_param("orsf_sk.base_url", "file:///etc/passwd")
        self.assertEqual(self.provider._orsf_base_url(), "https://api.orsf.sk/v1")
        self.param.set_param("orsf_sk.base_url", "https://orsf.example/v1/")
        self.assertEqual(self.provider._orsf_base_url(), "https://orsf.example/v1")

    # -- enrich ------------------------------------------------------------

    def test_enrich_company_maps_the_core_fields(self):
        with patch(GET, return_value=COMPANY):
            vals = self.provider.enrich_company(None, "31333532", None)
        self.assertEqual(vals["name"], "ESET, spol. s r.o.")
        self.assertEqual(vals["street"], "Einsteinova 24")
        self.assertEqual(vals["city"], "Bratislava - mestská časť Petržalka")
        self.assertEqual(vals["zip"], "851 01")
        self.assertEqual(vals["vat"], "SK2020317068")
        self.assertEqual(vals["company_registry"], "31333532")
        self.assertEqual(vals["partner_gid"], "31333532")
        self.assertEqual(vals["company_type"], "company")
        self.assertEqual(vals["partner_autocomplete_provider"], PROVIDER)
        self.assertEqual(
            vals["country_id"]["id"], self.env.ref("base.sk").id
        )

    def test_sibling_module_fields_are_filled_when_present(self):
        """Feature detection, not a manifest dependency — so only assert on
        the fields this database actually has."""
        # The values travel through the mappings, so make sure they point at
        # their standard fields rather than relying on ambient configuration.
        self.provider._orsf_apply_default_mappings(overwrite=True)
        partner_fields = self.env["res.partner"]._fields
        with patch(GET, return_value=COMPANY):
            vals = self.provider.enrich_company(None, "31333532", None)
        if "l10n_sk_dic" in partner_fields:
            self.assertEqual(vals["l10n_sk_dic"], "2020317068")
        if "l10n_sk_vat_registration_category" in partner_fields:
            self.assertEqual(vals["l10n_sk_vat_registration_category"], "4")
        if "l10n_sk_register_name" in partner_fields:
            self.assertEqual(vals["l10n_sk_register_office"], "Mestský súd Bratislava III")
            self.assertEqual(vals["l10n_sk_register_number"], "Sro/3586/B")
            self.assertEqual(vals["l10n_sk_register_status"], "active")

    def test_enrich_company_does_not_write_a_withdrawn_vat(self):
        """A lapsed IČ DPH on an invoice is what VIES rejects."""
        with patch(GET, return_value=DEREGISTERED):
            vals = self.provider.enrich_company(None, "31333532", None)
        self.assertNotIn("vat", vals)
        self.assertEqual(vals["company_registry"], "31333532")

    def test_enrich_company_is_empty_for_a_non_ico(self):
        with patch(GET) as get:
            self.assertEqual(self.provider.enrich_company(None, "SK2020317068", None), {})
            get.assert_not_called()

    def test_enrich_company_is_empty_when_the_register_has_nothing(self):
        with patch(GET, return_value=None):
            self.assertEqual(self.provider.enrich_company(None, "12345678", None), {})

    def test_sole_trader_becomes_an_individual(self):
        with patch(GET, return_value=dict(COMPANY, kind="sole_trader")):
            vals = self.provider.enrich_company(None, "31333532", None)
        self.assertEqual(vals["company_type"], "person")

        self.env.company.orsf_sk_set_company_type = False
        with patch(GET, return_value=dict(COMPANY, kind="sole_trader")):
            vals = self.provider.enrich_company(None, "31333532", None)
        self.assertNotIn("company_type", vals)

    # -- dynamic mapping ---------------------------------------------------

    def test_every_mapped_value_is_offered_in_settings(self):
        """The provider table and the settings form must not drift apart."""
        from odoo.addons.partner_autocomplete_orsf_sk.models import (
            partner_autocomplete_provider as prov,
        )
        offered = {
            name.replace("config_orsf_sk_mapping_", "")
            for name in self.env["res.config.settings"]._fields
            if name.startswith("config_orsf_sk_mapping_")
        }
        self.assertEqual(offered, {m[0] for m in prov.MAPPINGS})

    def test_defaults_point_each_mapping_at_its_standard_field(self):
        from odoo.addons.partner_autocomplete_orsf_sk.models import (
            partner_autocomplete_provider as prov,
        )
        for suffix, _k, _kind, _default in prov.MAPPINGS:
            self.param.set_param(f"orsf_sk.mapping.{suffix}", "")
        self.provider._orsf_apply_default_mappings()
        partner_fields = self.env["res.partner"]._fields
        for suffix, _k, _kind, default_field in prov.MAPPINGS:
            value = self.param.get_param(f"orsf_sk.mapping.{suffix}")
            if default_field in partner_fields:
                field = self.env["ir.model.fields"].sudo().browse(int(value))
                self.assertEqual(field.name, default_field, suffix)
            else:
                # No sibling module, so nothing to point at — and nothing set.
                self.assertFalse(value, suffix)

    def test_defaults_do_not_overwrite_a_deliberate_choice(self):
        ref = self.env["ir.model.fields"].sudo().search(
            [("model", "=", "res.partner"), ("name", "=", "ref")], limit=1
        )
        self.param.set_param("orsf_sk.mapping.nace", str(ref.id))
        self.provider._orsf_apply_default_mappings()
        self.assertEqual(self.param.get_param("orsf_sk.mapping.nace"), str(ref.id))
        # ...unless asked to.
        self.provider._orsf_apply_default_mappings(overwrite=True)
        if "l10n_sk_nace" in self.env["res.partner"]._fields:
            self.assertNotEqual(self.param.get_param("orsf_sk.mapping.nace"), str(ref.id))

    def test_status_and_vat_paragraph_are_parsed_not_written_raw(self):
        """The register says "aktívna" and "§4"; the SK selections hold
        "active" and "4". Mapping them at a Selection only works because the
        mapping parses them."""
        if "l10n_sk_register_status" not in self.env["res.partner"]._fields:
            self.skipTest("l10n_sk_trade_registry not installed")
        self.provider._orsf_apply_default_mappings(overwrite=True)
        with patch(GET, return_value=COMPANY):
            vals = self.provider.enrich_company(None, "31333532", None)
        self.assertEqual(vals["l10n_sk_register_status"], "active")
        self.assertEqual(vals["l10n_sk_vat_registration_category"], "4")

    def test_dynamic_mapping_writes_char_and_date_values(self):
        fields_model = self.env["ir.model.fields"].sudo()
        ref_field = fields_model.search(
            [("model", "=", "res.partner"), ("name", "=", "ref")], limit=1
        )
        self.assertTrue(ref_field, "expected res.partner.ref")
        # Base res.partner carries no Date field, and the incorporation date is
        # exactly the sort of value a deployment adds one for — so the test
        # adds one too, the way a customer would.
        date_field = fields_model.create(
            {
                "name": "x_orsf_established_on",
                # Deliberately not "Dátum vzniku": that is
                # l10n_sk_established_on's label, and a duplicate makes Odoo
                # log a same-label warning on every run of this suite.
                "field_description": "ORSF mapping test date",
                "model_id": self.env["ir.model"]._get_id("res.partner"),
                "ttype": "date",
                "state": "manual",
            }
        )
        self.param.set_param("orsf_sk.mapping.legal_form", str(ref_field.id))
        self.param.set_param("orsf_sk.mapping.established_date", str(date_field.id))

        with patch(GET, return_value=COMPANY):
            vals = self.provider.enrich_company(None, "31333532", None)
        self.assertEqual(vals["ref"], "spoločnosť s ručením obmedzeným")
        self.assertEqual(vals["x_orsf_established_on"], date(1992, 9, 17))

    def test_dynamic_mapping_survives_a_stale_field_id(self):
        self.param.set_param("orsf_sk.mapping.nace", "not-an-id")
        self.param.set_param("orsf_sk.mapping.size", "999999999")
        with patch(GET, return_value=COMPANY):
            vals = self.provider.enrich_company(None, "31333532", None)
        self.assertEqual(vals["name"], "ESET, spol. s r.o.")

    # -- autocomplete ------------------------------------------------------

    def test_autocomplete_ignores_short_queries(self):
        with patch(GET) as get:
            self.assertEqual(self.provider.autocomplete("es"), [])
            get.assert_not_called()

    def test_autocomplete_by_ico_uses_the_cheap_lookup_endpoint(self):
        """600 req/min and ~1 KB, against 30 and ~100 KB for the full record."""
        with patch(GET, return_value=LOOKUP) as get:
            results = self.provider.autocomplete("31333532")
        get.assert_called_once_with("/lookup/31333532")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["duns"], "31333532")
        self.assertEqual(results[0]["name"], "ESET, spol. s r.o. (31333532)")
        # /lookup nests the address; the dropdown's second line still fills.
        self.assertEqual(results[0]["city"], "Bratislava - mestská časť Petržalka")
        self.assertEqual(results[0]["vat"], "SK2020317068")

    def test_autocomplete_by_name_labels_a_dead_subject(self):
        with patch(GET, return_value=SEARCH_HITS) as get:
            results = self.provider.autocomplete("Eset")
        get.assert_called_once_with("/search", {"q": "Eset", "limit": 5})
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["name"], "ESET, spol. s r.o. (31333532)")
        # The register says this one is gone; the user must see that before
        # putting its IČO on a document.
        self.assertEqual(results[1]["name"], "ESET-IN s.r.o. (31338372) — zrušená")
        self.assertEqual(results[1]["city"], "Bratislava - mestská časť Dúbravka")

    def test_autocomplete_survives_an_outage(self):
        with patch(GET, return_value=None):
            self.assertEqual(self.provider.autocomplete("Eset"), [])

    def test_autocomplete_survives_a_changed_payload_shape(self):
        for body in ({}, {"hits": "nope"}, {"hits": [None, "x", {}]}):
            with patch(GET, return_value=body):
                self.assertEqual(self.provider.autocomplete("Eset"), [], body)

    # -- read_by_vat -------------------------------------------------------

    def test_read_by_vat_confirms_a_dic_hit_against_the_company_record(self):
        """A DIČ hit is not yet an answer about a VAT number."""
        dic_hits = {"hits": [{"ico": "31333532", "name": "ESET, spol. s r.o."}]}
        with patch(GET, side_effect=[dic_hits, LOOKUP]) as get:
            results = self.provider.read_by_vat("SK2020317068")
        self.assertEqual(
            [call.args for call in get.call_args_list],
            [("/search", {"q": "2020317068", "limit": 5}), ("/lookup/31333532",)],
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["duns"], "31333532")
        self.assertEqual(results[0]["vat"], "SK2020317068")

    def test_read_by_vat_rejects_a_dic_hit_that_holds_no_vat(self):
        """Holding a DIČ is not holding an IČ DPH.

        A company can be registered for tax and never have been a VAT payer;
        ORSF's `mode: dic` hit cannot tell the two apart, so the answer has to
        come from the company record.
        """
        dic_hits = {"hits": [{"ico": "31338372", "name": "ESET-IN s.r.o."}]}
        dead_lookup = dict(LOOKUP, icDph=None)
        with patch(GET, side_effect=[dic_hits, dead_lookup, {"hits": []}]):
            results = self.provider.read_by_vat("SK2020317068")
        self.assertEqual(results, [])

    def test_read_by_vat_drops_fuzzy_neighbours(self):
        """The fulltext index answers a VAT query with lexical neighbours."""
        with patch(GET, side_effect=[{"hits": []}, SEARCH_HITS]):
            results = self.provider.read_by_vat("SK 2020317068")
        # Only the hit whose IČ DPH is exactly the queried one survives.
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["duns"], "31333532")

    def test_read_by_vat_is_empty_without_a_vat(self):
        with patch(GET) as get:
            self.assertEqual(self.provider.read_by_vat(""), [])
            get.assert_not_called()


@tagged("post_install", "-at_install")
class TestOrsfBulkRefresh(TransactionCase):
    """POST /lookup/batch — 100 IČOs a call, against 30 full records a minute."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env[PROVIDER]
        cls.a = cls.env["res.partner"].create(
            {"name": "Stary nazov a", "company_registry": "31333532"}
        )
        cls.b = cls.env["res.partner"].create(
            {"name": "Stary nazov b", "company_registry": "00695599"}
        )
        cls.no_ico = cls.env["res.partner"].create({"name": "Bez ICO"})

    def test_batch_splits_at_a_hundred_and_drops_misses(self):
        icos = [str(700000 + i) for i in range(150)]
        page1 = {"results": [{"ico": i, "name": f"C{i}"} for i in icos[:100]]}
        # ORSF reports a miss as {"ico": …, "found": false}.
        page2 = {"results": [{"ico": i, "found": False} for i in icos[100:]]}
        responses = [
            type("R", (), {"status_code": 200, "json": lambda self, p=p: p})()
            for p in (page1, page2)
        ]
        with patch("requests.post", side_effect=responses) as post:
            found = self.provider._orsf_lookup_batch(icos)
        self.assertEqual(post.call_count, 2)
        self.assertEqual(len(post.call_args_list[0].kwargs["json"]["icos"]), 100)
        self.assertEqual(len(post.call_args_list[1].kwargs["json"]["icos"]), 50)
        self.assertEqual(len(found), 100)

    def test_bulk_refresh_writes_identity_and_reports(self):
        records = {
            "31333532": dict(LOOKUP, name="ESET, spol. s r.o."),
            "00695599": dict(LOOKUP, ico="00695599", name="ELCOM s.r.o.",
                             icDph="SK2020517895"),
        }
        with patch(
            f"{PROVIDER_PATH}._orsf_lookup_batch", return_value=records
        ) as batch, patch.object(
            type(self.env.user), "_bus_send"
        ) as bus:
            (self.a | self.b | self.no_ico).action_orsf_bulk_refresh()
        # One call, and the partner with no IČO never reaches the register.
        self.assertEqual(sorted(batch.call_args.args[0]), ["00695599", "31333532"])
        self.assertEqual(self.a.name, "ESET, spol. s r.o.")
        self.assertEqual(self.b.name, "ELCOM s.r.o.")
        self.assertEqual(self.no_ico.name, "Bez ICO")
        self.assertIn("without a usable IČO", bus.call_args.args[1]["message"])

    def test_a_lookup_record_never_clears_lists_it_does_not_carry(self):
        """/lookup has no activities or filings; a bulk refresh must not wipe
        what the full record previously stored."""
        vals = self.provider._orsf_company_vals(LOOKUP)
        self.assertNotIn("l10n_sk_activity_ids", vals)
        self.assertNotIn("l10n_sk_filing_ids", vals)
        self.assertNotIn("l10n_sk_history_ids", vals)
        # ...while the full record does replace them.
        full = self.provider._orsf_company_vals(dict(COMPANY, activities=[], filings=[]))
        if "l10n_sk_activity_ids" in self.env["res.partner"]._fields:
            self.assertIn("l10n_sk_activity_ids", full)

    def test_lookup_vat_key_is_read_despite_the_different_spelling(self):
        """/companies spells it icdph, /lookup spells it icDph."""
        self.assertEqual(
            self.provider._orsf_company_vals(LOOKUP)["vat"], "SK2020317068"
        )
