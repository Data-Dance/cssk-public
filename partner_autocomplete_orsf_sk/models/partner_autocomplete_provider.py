# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Partner autocomplete backed by ORSF (https://orsf.sk).

ORSF aggregates the Slovak state registers — RPO, ORSR, ŽRSR, RÚZ and the
Finančná správa VAT-payer list — behind one JSON API, published under CC-BY 4.0.
Three endpoints are used, all of them open to anonymous callers:

``GET /lookup/{ico}``
    Identity, address and tax ids, and nothing else. ~1 KB against the ~100 KB
    of the full record, and rate-limited at **600/min** rather than 30 — so it
    is what the type-ahead dropdown asks.
``GET /companies/{ico}``
    The full record. Only the enrichment step needs it, for the register
    coordinates (§3a) and the VAT-registration paragraph that ``/lookup`` omits.
``GET /search``
    The fulltext and exact-id indexes behind name and VAT lookups.

An optional Bearer token raises the quota and unlocks the full address of a
sole trader, which ORSF gates behind ``addressLocked`` for GDPR.
"""

import logging
import re
from datetime import datetime, timedelta

import requests
from odoo import api, fields, models
from odoo.fields import Command
from requests.exceptions import RequestException

_logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.orsf.sk/v1"
# Sign-in lives on the site, not on the API host: api.orsf.sk answers 404 for
# it. The cookie it sets is then presented to api.orsf.sk.
DEFAULT_AUTH_URL = "https://orsf.sk"
SESSION_COOKIE = "__Secure-orsf.session_token"
# Only an optimisation: an expired session is caught by the 401 retry anyway.
SESSION_TTL_HOURS = 12
DEFAULT_TIMEOUT = 15
SUGGESTION_LIMIT = 5
# POST /lookup/batch takes at most 100 IČOs and allows 60 calls a minute, so a
# whole partner base refreshes in a couple of requests. The full company record
# allows 30 a minute, one IČO at a time.
BATCH_SIZE = 100

# The register values that go through the configurable mapping, each with the
# field it points at by default.
#
# `kind` says how the raw register value is turned into something the target
# field accepts. `status` and `vat_registration` need real parsing — the
# register says "aktívna" and "§4" where the SK selections hold "active" and
# "4" — so mapping them at a Selection only works because of these.
#
# `default_field` is what `_orsf_apply_default_mappings` points the mapping at
# when that field exists. Every one of them lives in a sibling module that this
# one does not depend on, which is why the mapping is the mechanism rather than
# a hardcoded write: without the sibling there is no field, and the deployment
# can aim the value at one of its own instead.
MAPPINGS = (
    # param suffix,        record key,          kind,               default field
    ("ico", "nationalId", "char", "company_registry"),
    ("dic", "taxId", "char", "l10n_sk_dic"),
    ("nace", "nace", "char", "l10n_sk_nace"),
    ("legal_form", "legalForm", "char", "l10n_sk_legal_form"),
    ("register", "register", "char", "l10n_sk_register_name"),
    ("register_office", "registerOffice", "char", "l10n_sk_register_office"),
    ("register_number", "registerNumber", "char", "l10n_sk_register_number"),
    ("status", "statusCode", "register_status", "l10n_sk_register_status"),
    ("size", "velkostLabel", "char", "l10n_sk_size_category"),
    ("established_date", "establishedOn", "date", "l10n_sk_established_on"),
    ("dissolved_date", "dissolvedOn", "date", "l10n_sk_dissolved_on"),
    ("vat_registration", None, "vat_category", "l10n_sk_vat_registration_category"),
    ("vat_payer_since_date", None, "date", "l10n_sk_vat_payer_since"),
)
LOOKUP_PATH = "/lookup"
# How many DIČ-index hits a VAT lookup will confirm against the register.
# The index answers with one hit in practice; the cap is there so a change of
# shape upstream cannot turn one keystroke into a burst against a 30 req/min
# budget.
VAT_VERIFY_LIMIT = 3

# The register's own words for "this subject is still alive", in both the
# Slovak payload and the English label set.
ACTIVE_STATUSES = ("aktívna", "active")


class PartnerAutocompleteProviderRegistry(models.AbstractModel):
    _inherit = "partner.autocomplete.provider.registry"

    @api.model
    def _get_available_providers(self):
        return super()._get_available_providers() + [
            (
                self.env["partner.autocomplete.provider.orsf_sk"]._name,
                "ORSF.SK",
            )
        ]


class PartnerAutocompleteProviderOrsfSk(models.AbstractModel):
    _inherit = "partner.autocomplete.provider"
    _name = "partner.autocomplete.provider.orsf_sk"
    _description = "Partner Autocomplete Provider (ORSF SK)"

    # -- configuration -----------------------------------------------------

    @api.model
    def _orsf_param(self, key):
        return self.env["ir.config_parameter"].sudo().get_param(key)

    @api.model
    def _orsf_base_url(self):
        url = (self._orsf_param("orsf_sk.base_url") or "").strip()
        # Only an admin can write this parameter, but that is no reason to let
        # a typo (or a compromised one) aim the server's own HTTP client at
        # file:// or at something on the internal network.
        if not url.startswith(("http://", "https://")):
            if url:
                _logger.warning(
                    "orsf_sk.base_url is not an http(s) URL (%r); using %s",
                    url,
                    DEFAULT_BASE_URL,
                )
            return DEFAULT_BASE_URL
        return url.rstrip("/")

    @api.model
    def _orsf_headers(self):
        """Request headers, carrying the Bearer token when one is configured.

        ORSF's own documentation page says it issues no tokens; the OpenAPI
        description of ``/lookup/{ico}`` says a Bearer token raises the quota
        and unlocks a sole trader's full address, and the service echoes
        ``Vary: Authorization``. The page is behind.
        """
        headers = {"Accept": "application/json"}
        token = (self._orsf_param("orsf_sk.api_token") or "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @api.model
    def _orsf_auth_url(self):
        url = (self._orsf_param("orsf_sk.auth_base_url") or "").strip()
        if not url.startswith(("http://", "https://")):
            return DEFAULT_AUTH_URL
        return url.rstrip("/")

    @api.model
    def _orsf_sign_in(self):
        """Exchange the configured credentials for a session token.

        ORSF issues no API key for its gated endpoints — the only auth it
        offers is a *better-auth* session cookie, and it never displays that
        cookie anywhere, so the alternative to signing in here is an
        administrator copying it out of DevTools by hand and re-copying it
        whenever it lapses.

        The password is never logged, never returned and never leaves this
        method.
        """
        params = self.env["ir.config_parameter"].sudo()
        email = (params.get_param("orsf_sk.login_email") or "").strip()
        password = params.get_param("orsf_sk.login_password") or ""
        if not email or not password:
            return ""

        url = f"{self._orsf_auth_url()}/api/auth/sign-in/email"
        try:
            response = requests.post(
                url,
                json={"email": email, "password": password},
                timeout=self._orsf_timeout(),
                headers={"Accept": "application/json"},
            )
        except RequestException as err:
            _logger.warning("ORSF sign-in to %s failed: %s", url, err)
            return ""

        if response.status_code != 200:
            # Deliberately does not echo the body: a sign-in error can repeat
            # back what was submitted.
            _logger.warning(
                "ORSF rejected the sign-in for %s (HTTP %s). Check "
                "orsf_sk.login_email / orsf_sk.login_password.",
                email,
                response.status_code,
            )
            return ""

        token = response.cookies.get(SESSION_COOKIE) or ""
        if not token:
            # better-auth also returns the session in the body on some setups.
            try:
                token = (response.json() or {}).get("token") or ""
            except ValueError:
                token = ""
        if not token:
            _logger.warning(
                "ORSF sign-in succeeded but returned no %s cookie.",
                SESSION_COOKIE,
            )
            return ""

        params.set_param("orsf_sk.session_token_cache", token)
        params.set_param(
            "orsf_sk.session_token_expiry",
            fields.Datetime.to_string(
                fields.Datetime.now() + timedelta(hours=SESSION_TTL_HOURS)
            ),
        )
        _logger.info("ORSF session established for %s.", email)
        return token

    @api.model
    def _orsf_session_token(self, refresh=False):
        """The cached session token, signing in when it is missing or stale."""
        params = self.env["ir.config_parameter"].sudo()
        if not refresh:
            token = params.get_param("orsf_sk.session_token_cache") or ""
            expiry = params.get_param("orsf_sk.session_token_expiry") or ""
            if token and expiry:
                try:
                    if fields.Datetime.from_string(expiry) > fields.Datetime.now():
                        return token
                except (TypeError, ValueError):
                    pass
        return self._orsf_sign_in()

    @api.model
    def _orsf_cookies(self):
        """The session cookie the person and graph endpoints require.

        Nothing in this module calls those endpoints;
        ``partner_autocomplete_orsf_sk_related_parties`` does, through
        ``_orsf_get(..., authenticated=True)``. Every other request goes out
        anonymously — see :meth:`_orsf_probe` for why that matters.
        """
        token = self._orsf_session_token()
        return {SESSION_COOKIE: token} if token else None

    @api.model
    def _orsf_timeout(self):
        try:
            return float(self._orsf_param("orsf_sk.timeout") or DEFAULT_TIMEOUT)
        except (TypeError, ValueError):
            return DEFAULT_TIMEOUT

    # -- transport ---------------------------------------------------------

    @api.model
    def _orsf_get(self, path, params=None, *, authenticated=False, _retried=False):
        """GET one ORSF endpoint and return the decoded body, or ``None``.

        Nothing here raises: the caller is a keystroke handler in the partner
        form, so a register outage has to degrade to "no suggestions" rather
        than to a traceback in the user's face. 404 is a normal answer (the
        register holds no such subject) and is not logged as a failure.

        Collapsing every non-answer to ``None`` is right for a type-ahead and
        wrong for anything DECIDING on the register — see :meth:`_orsf_probe`,
        which this delegates to.
        """
        return self._orsf_probe(
            path, params=params, authenticated=authenticated, _retried=_retried
        )[1]

    @api.model
    def _orsf_probe(self, path, params=None, *, authenticated=False, _retried=False):
        """GET one ORSF endpoint and say *why* it did not answer.

        Returns ``(outcome, body)``:

        ``("ok", {...})``
            The register answered.
        ``("absent", None)``
            404 — the register holds no such subject. That is a **fact about
            the world**, not a failure.
        ``("unavailable", None)``
            Outage, timeout, rate limit, refused credentials, unparseable
            body. We do not know whether the subject exists.

        The last two must never lead to the same decision. A gate that treats
        "we could not reach the register" as "this company does not exist"
        turns an ORSF outage into a wall of rejected customers; one that
        treats it as "verified" opens the gate every time the register
        hiccups. ``_orsf_get`` cannot express the difference, so callers that
        decide something use this instead.

        ``authenticated=True`` presents the signed-in session, and only then.
        Everything this module calls answers anonymously, at 600 requests a
        minute per IP on ``/lookup``, while ORSF's published tiers are slower
        — FREE is 60/min, PRO 300/min. Sending the cookie on every request
        would let one gated feature quietly move a database's whole
        type-ahead onto the account, and sign in on a keystroke whenever the
        cached session had lapsed. So the session goes only where it is
        required: persons and the ownership graph.
        """
        url = f"{self._orsf_base_url()}{path}"
        cookies = None
        if authenticated:
            cookies = self._orsf_cookies()
            if not cookies:
                _logger.warning(
                    "ORSF %s needs a signed-in session and none could be "
                    "obtained. Check orsf_sk.login_email / orsf_sk.login_password.",
                    url,
                )
                return "unavailable", None
        try:
            response = requests.get(
                url,
                params=params,
                timeout=self._orsf_timeout(),
                headers=self._orsf_headers(),
                cookies=cookies,
            )
        except RequestException as err:
            _logger.info("ORSF request to %s failed: %s", url, err)
            return "unavailable", None
        if response.status_code == 404:
            return "absent", None
        if response.status_code == 401:
            # A gated endpoint whose session has lapsed. Sign in again and try
            # once more; `_retried` is what stops that becoming a loop when the
            # credentials themselves are wrong. An anonymous request that meets
            # a 401 is not helped by a session it was never meant to carry, so
            # it does not trigger a sign-in.
            if (
                authenticated
                and not _retried
                and self._orsf_session_token(refresh=True)
            ):
                return self._orsf_probe(
                    path, params=params, authenticated=True, _retried=True
                )
            _logger.warning(
                "ORSF refused %s: %s. Check orsf_sk.login_email / "
                "orsf_sk.login_password / orsf_sk.api_token.",
                url,
                response.text[:200],
            )
            return "unavailable", None
        if response.status_code == 429:
            _logger.info(
                "ORSF rate limit reached on %s (retry after %ss)",
                url,
                response.headers.get("Retry-After", "?"),
            )
            return "unavailable", None
        if response.status_code != 200:
            _logger.info(
                "ORSF returned HTTP %s for %s: %s",
                response.status_code,
                url,
                response.text[:200],
            )
            return "unavailable", None
        try:
            body = response.json()
        except ValueError:
            _logger.info("ORSF returned a non-JSON body for %s", url)
            return "unavailable", None
        # Every endpoint used here answers with an object. Checking once means
        # no caller has to defend against `.get` on a list or a string if the
        # API's shape ever moves under us.
        if not isinstance(body, dict):
            _logger.info("ORSF returned a %s, not an object, for %s", type(body).__name__, url)
            return "unavailable", None
        return "ok", body

    @api.model
    def _orsf_lookup_probe(self, ico):
        """:meth:`_orsf_lookup` with the outcome kept — ``(outcome, body)``."""
        return self._orsf_probe(f"{LOOKUP_PATH}/{ico}")

    @api.model
    def _orsf_lookup(self, ico):
        """Identity-only record for one IČO — the cheap endpoint.

        ``/lookup`` nests the address one level down and spells the VAT id
        ``icDph``; ``_orsf_suggestion`` and ``_orsf_record_vat`` read both
        shapes, so the two endpoints stay interchangeable for display.
        """
        return self._orsf_get(f"{LOOKUP_PATH}/{ico}")

    @api.model
    def _orsf_refresh(self, ico):
        """Ask ORSF to re-fetch one company from the source registers.

        ORSF's copy can be incomplete — a company whose ORSR entry it never
        parsed has ``register``/``registerOffice``/``registerNumber`` all null
        while still carrying its RPO and FS data, which looks exactly like a
        mapping bug on our side.

        The endpoint is **not in ORSF's OpenAPI document** but is live and
        anonymous, rate-limited at 5/min per IP with a 60 s per-IČO cooldown.
        It is also **asynchronous**: the fresh data appears about a minute
        later, so there is nothing to be gained by re-reading immediately.

        Returns ``(accepted, message)``.
        """
        url = f"{self._orsf_base_url()}/companies/{ico}/refresh"
        try:
            response = requests.post(
                url,
                timeout=self._orsf_timeout(),
                headers=self._orsf_headers(),
            )
        except RequestException as err:
            _logger.info("ORSF refresh of %s failed: %s", ico, err)
            return False, str(err)
        try:
            body = response.json()
        except ValueError:
            body = {}
        # A cooldown hit comes back as HTTP 200 carrying an error object, so
        # the status code alone does not say whether it was accepted.
        if isinstance(body, dict) and body.get("error"):
            return False, body.get("message") or body["error"]
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}"
        return True, ""

    @api.model
    def _orsf_lookup_batch(self, icos):
        """Identity for many IČOs at once — ``POST /lookup/batch``.

        The endpoint takes 100 per call and allows 60 calls a minute, against
        the full record's 30 requests a minute one at a time. Refreshing a
        partner base through the full record exhausts the budget after about
        twenty contacts and then silently returns nothing, which is what makes
        this worth a separate path.

        It carries **less** than the full record: no ``vatRegistration``, no
        register office or číslo zápisu, no activities, filings or history. The
        caller is expected to know it is trading depth for reach.

        Returns ``{ico: record}``, omitting the ones ORSF does not have.
        """
        found = {}
        icos = [i for i in dict.fromkeys(icos) if i]
        for start in range(0, len(icos), BATCH_SIZE):
            chunk = icos[start:start + BATCH_SIZE]
            url = f"{self._orsf_base_url()}{LOOKUP_PATH}/batch"
            try:
                response = requests.post(
                    url,
                    json={"icos": chunk},
                    timeout=self._orsf_timeout(),
                    headers=self._orsf_headers(),
                )
            except RequestException as err:
                _logger.info("ORSF batch lookup failed: %s", err)
                continue
            if response.status_code != 200:
                _logger.info(
                    "ORSF batch lookup returned HTTP %s: %s",
                    response.status_code,
                    response.text[:200],
                )
                continue
            try:
                body = response.json()
            except ValueError:
                continue
            for item in (body or {}).get("results") or []:
                # A miss comes back as {"ico": …, "found": false}.
                if isinstance(item, dict) and item.get("ico") and item.get("found") is not False:
                    found[str(item["ico"])] = item
        return found

    @api.model
    def _orsf_hits(self, body):
        """The ``hits`` array of a /search response, defensively."""
        hits = (body or {}).get("hits")
        if not isinstance(hits, list):
            return []
        return [hit for hit in hits if isinstance(hit, dict)]

    # -- value helpers -----------------------------------------------------

    @api.model
    def _orsf_normalise_ico(self, value):
        """Return a 6-8 digit IČO, or "" when the input is not one.

        Leading zeros are significant (``00151700``), so the digits are kept as
        written rather than run through ``int()``.
        """
        digits = re.sub(r"\D", "", str(value or ""))
        return digits if 6 <= len(digits) <= 8 else ""

    @api.model
    def _orsf_date(self, value):
        """ORSF dates arrive as ``2003-02-05T00:00:00.000Z`` or ``2003-02-05``."""
        if not value:
            return False
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
        except ValueError:
            pass
        try:
            return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
        except ValueError:
            _logger.info("ORSF returned an unparseable date: %r", value)
            return False

    @api.model
    def _orsf_record_vat(self, record):
        """The live IČ DPH on a company record or a search hit, upper-cased.

        ``/companies/{ico}`` spells the key ``icdph`` (and ``vatId``) while a
        search hit spells it ``icDph``; all three are cleared once the register
        withdraws the registration, which is what makes this the "live" value.
        """
        return (
            record.get("vatId") or record.get("icDph") or record.get("icdph") or ""
        ).upper()

    @api.model
    def _orsf_format_psc(self, value):
        """``85101`` -> ``851 01``, the way a PSČ is written on a SK document."""
        digits = re.sub(r"\D", "", str(value or ""))
        if len(digits) != 5 or not self.env.company.orsf_sk_format_psc:
            return str(value or "")
        return f"{digits[:3]} {digits[3:]}"

    @api.model
    def _enrich_dynamic_mapping(self, result, mapping):
        """Copy register values into whichever res.partner fields are configured.

        ``mapping`` holds ``(config parameter, value, kind)`` with *kind* one of
        ``char`` / ``date``. ARES keys its date conversion off a ``_date``
        suffix on the parameter name; naming the kind explicitly means a
        parameter can be renamed without silently changing how it is parsed.
        """
        fields_model = self.env["ir.model.fields"].sudo()
        for parameter, value, kind in mapping:
            field_id = self._orsf_param(parameter)
            if not field_id or value in (None, "", False):
                continue
            try:
                field = fields_model.browse(int(field_id)).exists()
            except (TypeError, ValueError):
                _logger.info("%s does not hold a field id: %r", parameter, field_id)
                continue
            if not field:
                continue
            value = self._orsf_mapping_value(value, kind)
            if value in (None, "", False):
                continue
            result[field.name] = value
        return result

    # -- payload mapping ---------------------------------------------------

    @api.model
    def _orsf_mapping_value(self, value, kind):
        """Turn a raw register value into something the target field accepts.

        The two parsing kinds live in sibling modules. When the sibling is
        absent the raw string is written instead, which is right for a mapping
        aimed at a plain Char field of the deployment's own.
        """
        if kind == "date":
            return self._orsf_date(value)
        partner = self.env["res.partner"]
        if kind == "register_status" and hasattr(
            partner, "_l10n_sk_parse_register_status"
        ):
            return partner._l10n_sk_parse_register_status(value, value)
        if kind == "vat_category" and hasattr(
            partner, "_l10n_sk_parse_vat_registration_category"
        ):
            return partner._l10n_sk_parse_vat_registration_category(value)
        return value

    @api.model
    def _orsf_company_vals(self, record):
        """Map one ``GET /companies/{ico}`` record onto res.partner values."""
        result = {}
        company = self.env.company
        address = record.get("address")
        address = address if isinstance(address, dict) else {}

        if record.get("name"):
            result["name"] = record["name"]
        street = record.get("street") or address.get("street")
        if street:
            result["street"] = street
        city = record.get("city") or address.get("city")
        if city:
            result["city"] = city
        zip_code = (
            record.get("postalCode")
            or record.get("psc")
            or address.get("postalCode")
            or address.get("psc")
        )
        if zip_code:
            result["zip"] = self._orsf_format_psc(zip_code)

        country_code = record.get("countryCode") or address.get("country") or "SK"
        country = self.env["res.country"].search(
            [("code", "=ilike", country_code)], limit=1
        )
        if country:
            result["country_id"] = {
                "id": country.id,
                "display_name": country.display_name,
            }

        # Only a *live* registration goes into `vat`. ORSF keeps the historical
        # vatRegistration row after a deregistration but clears icdph/vatId on
        # the company record itself — and an IČ DPH the register has withdrawn
        # is exactly the number that makes VIES reject an invoice.
        # /companies spells it `icdph`, /lookup spells it `icDph`.
        vat_id = self._orsf_record_vat(record)
        if vat_id:
            result["vat"] = vat_id

        kind = record.get("kind")
        if company.orsf_sk_set_company_type:
            if kind == "company":
                result["company_type"] = "company"
            elif kind == "sole_trader":
                result["company_type"] = "person"

        ico = record.get("nationalId") or record.get("ico")
        if ico:
            result["partner_gid"] = str(ico)
            if company.orsf_sk_set_company_registry:
                result["company_registry"] = str(ico)
        result["partner_autocomplete_provider"] = self._name

        vat_registration = record.get("vatRegistration")
        vat_registration = vat_registration if isinstance(vat_registration, dict) else {}

        self._enrich_dynamic_mapping(result, self._orsf_mapping_values(record))
        self._orsf_optional_fields(result, record, vat_registration)
        return result

    @api.model
    def _orsf_mapping_values(self, record):
        """Pair every mapped register value with its raw content and kind."""
        vat_registration = record.get("vatRegistration")
        vat_registration = vat_registration if isinstance(vat_registration, dict) else {}
        special = {
            "ico": record.get("nationalId") or record.get("ico"),
            "size": record.get("velkostLabel") or record.get("sizeCode"),
            "dic": record.get("taxId") or record.get("dic"),
            "status": record.get("statusCode") or record.get("status"),
            "vat_registration": (
                vat_registration.get("registrationCategory")
                or vat_registration.get("druhReg")
            ),
            "vat_payer_since_date": vat_registration.get("vatPayerSince"),
        }
        return [
            (
                f"orsf_sk.mapping.{suffix}",
                special[suffix] if suffix in special else record.get(key),
                kind,
            )
            for suffix, key, kind, _default in MAPPINGS
        ]

    @api.model
    def _orsf_apply_default_mappings(self, overwrite=False):
        """Point each mapping at its standard field, where that field exists.

        Run on install and from the settings button, because a sibling module
        can be installed after this one — at which point its fields appear but
        nothing has told the mappings about them.

        Returns the number of mappings set.
        """
        params = self.env["ir.config_parameter"].sudo()
        partner_fields = self.env["res.partner"]._fields
        fields_model = self.env["ir.model.fields"].sudo()
        applied = 0
        for suffix, _key, _kind, default_field in MAPPINGS:
            if default_field not in partner_fields:
                continue
            key = f"orsf_sk.mapping.{suffix}"
            if params.get_param(key) and not overwrite:
                continue
            field = fields_model.search(
                [("model", "=", "res.partner"), ("name", "=", default_field)],
                limit=1,
            )
            if field:
                params.set_param(key, str(field.id))
                applied += 1
        return applied

    @api.model
    def _orsf_optional_fields(self, result, record, vat_registration):
        """Fill what the configurable mapping cannot express.

        Everything with a one-to-one field — IČO, DIČ, register coordinates,
        status, dates, the VAT paragraph — travels through ``MAPPINGS``
        instead, so a deployment can retarget any of it. What is left here is
        the shape the mapping has no way to describe: the three one2many lists,
        and the timestamp recording that we asked at all.

        Feature detection rather than a manifest dependency, so this stays a
        Tools module with no accounting or localisation weight — the same move
        ``partner_autocomplete`` itself makes for ``base_address_extended``.
        """
        partner_fields = self.env["res.partner"]._fields

        if "l10n_sk_register_checked_on" in partner_fields:
            # Not a mapped value: it records *when we asked*, which is what
            # separates "the register holds nothing" from "we never looked".
            result["l10n_sk_register_checked_on"] = fields.Datetime.now()
            self._orsf_register_lists(result, record, partner_fields)
        return result

    @api.model
    def _orsf_register_lists(self, result, record, partner_fields):
        """Replace the register's list data — activities, filings, history.

        ``Command.clear()`` first in each: these are a mirror of what the
        register says today, not an accumulating log, and re-enriching a
        partner must not double every row. The dispatcher's StaticList patch
        is what makes CLEAR work at all in the form.
        """
        if "l10n_sk_activity_ids" in partner_fields and "activities" in record:
            rows = []
            for item in record.get("activities") or []:
                if not isinstance(item, dict) or not item.get("text"):
                    continue
                rows.append(Command.create({
                    "name": item["text"],
                    "valid_from": self._orsf_date(item.get("validFrom")) or False,
                    "valid_to": self._orsf_date(item.get("validTo")) or False,
                    "suspended_from": self._orsf_date(item.get("suspendedFrom")) or False,
                    "suspended_to": self._orsf_date(item.get("suspendedTo")) or False,
                    "source": item.get("source") or "ORSF",
                }))
            result["l10n_sk_activity_ids"] = [Command.clear()] + rows

        if "l10n_sk_filing_ids" in partner_fields and "filings" in record:
            rows, seen = [], set()
            for item in record.get("filings") or []:
                if not isinstance(item, dict) or not item.get("period"):
                    continue
                key = (str(item["period"]), item.get("type") or "")
                if key in seen:
                    continue
                seen.add(key)
                # The dates live on the nested `zavierka` payload, which is
                # absent on a filing ORSF has listed but not yet parsed.
                payload = item.get("payload")
                z = (payload or {}).get("zavierka") if isinstance(payload, dict) else None
                z = z if isinstance(z, dict) else {}
                rows.append(Command.create({
                    "period": str(item["period"]),
                    "filing_type": item.get("type") or False,
                    "filed_on": self._orsf_date(z.get("datumPodania")) or False,
                    "approved_on": self._orsf_date(z.get("datumSchvalenia")) or False,
                    "prepared_on": self._orsf_date(z.get("datumZostavenia")) or False,
                    "consolidated": bool(z.get("konsolidovana")),
                    "source": item.get("source") or "RUZ",
                }))
            result["l10n_sk_filing_ids"] = [Command.clear()] + rows

        if "l10n_sk_history_ids" in partner_fields and (
            "previousNames" in record or "previousAddresses" in record
        ):
            rows = []
            for item in record.get("previousNames") or []:
                if not isinstance(item, dict):
                    continue
                value = item.get("value") or item.get("name")
                if not value:
                    continue
                rows.append(Command.create({
                    "kind": "name",
                    "value": value,
                    "valid_from": self._orsf_date(item.get("validFrom")) or False,
                    "valid_to": self._orsf_date(item.get("validTo")) or False,
                }))
            for item in record.get("previousAddresses") or []:
                if not isinstance(item, dict):
                    continue
                value = self._orsf_format_previous_address(item)
                if not value:
                    continue
                rows.append(Command.create({
                    "kind": "address",
                    "value": value,
                    "valid_from": self._orsf_date(item.get("validFrom")) or False,
                    "valid_to": self._orsf_date(item.get("validTo")) or False,
                }))
            result["l10n_sk_history_ids"] = [Command.clear()] + rows
        return result

    @api.model
    def _orsf_format_previous_address(self, item):
        """Flatten a historic address into one readable line.

        ORSF nests these differently from the current address: the
        municipality and country are objects carrying a ``value``, and the
        street number is separate from the street.
        """
        def _val(node):
            if isinstance(node, dict):
                return node.get("value") or ""
            return node or ""

        street = " ".join(
            part for part in (item.get("street"), item.get("buildingNumber")) if part
        )
        postal = item.get("postalCodes")
        postal = _val(postal[0]) if isinstance(postal, list) and postal else ""
        city = _val(item.get("municipality"))
        country = _val(item.get("country"))
        return ", ".join(
            part for part in (street, " ".join(p for p in (postal, city) if p), country)
            if part
        )

    @api.model
    def _orsf_suggestion(self, record):
        """Build one dropdown entry from a search hit or a company record."""
        ico = str(record.get("nationalId") or record.get("ico") or "")
        name = record.get("name") or ""
        status = record.get("status")
        address = record.get("address")
        address = address if isinstance(address, dict) else {}
        label = f"{name} ({ico})" if ico else name
        # A dissolved or suspended subject is a legitimate hit — the user may be
        # booking a document from before it died — but picking one unknowingly
        # is how a defunct IČO lands on a live invoice, so the register's own
        # status word rides along in the label.
        if status and status not in ACTIVE_STATUSES:
            label = f"{label} — {status}"
        return {
            "country_id": False,
            "ignored": False,
            "logo": False,
            "name": label,
            "legal_name": name,
            "partner_gid": ico,
            "duns": ico,
            "state_id": False,
            # `city` is what partner_autocomplete renders as the grey second
            # half of the dropdown line. /companies puts it at the top level,
            # /lookup nests it under `address`.
            "city": record.get("city") or address.get("city") or "",
            "vat": self._orsf_record_vat(record),
            "website": False,
        }

    # -- provider API ------------------------------------------------------

    @api.model
    def enrich_company(self, company_domain, partner_gid, vat):
        ico = self._orsf_normalise_ico(partner_gid)
        if not ico:
            return {}
        record = self._orsf_get(f"/companies/{ico}")
        if not record or not record.get("name"):
            return {}
        return self._orsf_company_vals(record)

    @api.model
    def autocomplete(self, query):
        query = (query or "").strip()
        if len(query) < 3:
            return []

        # A bare 6-8 digit query is an IČO: go straight to the register rather
        # than through the fulltext index, which ranks lexical neighbours first.
        # The dropdown only needs identity, so this is the cheap endpoint —
        # 600 req/min and ~1 KB, against 30 and ~100 KB for the full record.
        if query.replace(" ", "").isdigit():
            ico = self._orsf_normalise_ico(query)
            if ico:
                record = self._orsf_lookup(ico)
                return [self._orsf_suggestion(record)] if record else []

        body = self._orsf_get("/search", {"q": query[:100], "limit": SUGGESTION_LIMIT})
        return [
            self._orsf_suggestion(hit)
            for hit in self._orsf_hits(body)
            if hit.get("nationalId") or hit.get("ico")
        ]

    @api.model
    def read_by_vat(self, vat):
        """Look a partner up by IČ DPH.

        Only reachable with a syntactically valid VAT number — that check lives
        in ``partner_autocomplete``'s jsvat bundle.
        """
        vat = re.sub(r"\s", "", (vat or "")).upper()
        if not vat:
            return []

        # A Slovak IČ DPH is "SK" + the DIČ, and ORSF indexes the DIČ exactly
        # (`mode: dic`) while the IČ DPH only reaches the fuzzy fulltext index.
        # Ask the exact index first.
        if vat.startswith("SK") and vat[2:].isdigit():
            body = self._orsf_get("/search", {"q": vat[2:], "limit": SUGGESTION_LIMIT})
            for hit in self._orsf_hits(body)[:VAT_VERIFY_LIMIT]:
                ico = self._orsf_normalise_ico(hit.get("nationalId") or hit.get("ico"))
                if not ico:
                    continue
                # A DIČ hit is not an answer yet: holding a tax id is not the
                # same as holding a VAT registration, and a `mode: dic` hit
                # reports icDph null even for a company that does hold one.
                # Only the register settles it — so confirm before offering
                # this subject as the holder of the typed IČ DPH.
                record = self._orsf_lookup(ico)
                if not record:
                    continue
                if self._orsf_record_vat(record) == vat:
                    return [self._orsf_suggestion(record)]

        body = self._orsf_get("/search", {"q": vat, "limit": SUGGESTION_LIMIT})
        # The fulltext index is fuzzy: a query for one IČ DPH comes back with
        # its lexical neighbours too. Only an exact match answers the question
        # "who holds this VAT number".
        return [
            self._orsf_suggestion(hit)
            for hit in self._orsf_hits(body)
            if self._orsf_record_vat(hit) == vat
        ]
