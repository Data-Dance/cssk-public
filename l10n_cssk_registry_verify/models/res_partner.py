# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Ask the state register whether a company exists, and report what happened.

The single entry point is :meth:`ResPartner._cssk_verify_registry`. It is a
model method rather than a record one because the question is about a number,
not about a partner: signup asks it before any partner exists.
"""
import logging

from odoo import api, fields, models

from odoo.addons.l10n_cssk_core.models.res_partner import REGISTRY_COUNTRIES
from odoo.addons.l10n_cssk_core.tools import (
    company_name_similarity,
    is_valid_ico,
    normalize_registry,
)

_logger = logging.getLogger(__name__)


def _prefixed_vat(value):
    """A VAT number, or "" — never a bare national number.

    Belt and braces against the failure this exists to prevent. On Odoo 19 any
    non-empty ``vat`` satisfies a ``vat_required`` fiscal position, with no
    format check anywhere in core, so a bare IČO written here would waive VAT
    on EU sales. Both registers answer with a prefixed value or nothing, so
    this should never fire — which is exactly why it is cheap to keep: if a
    provider's shape moves, the result is a missing VAT number and a
    correctly-charged invoice, rather than a silent under-collection.
    """
    value = (value or "").strip().upper().replace(" ", "")
    if len(value) > 2 and value[:2].isalpha() and value[2:].isalnum():
        return value
    return ""

#: At or above this, the typed name and the register's are the same company.
#: Calibrated, not guessed: on 45 real Slovak companies the distribution is
#: bimodal -- 44 scored exactly 1.000 and one scored 0.716. There is nothing
#: in between, so 0.90 is a wide margin rather than a fine line.
NAME_MATCH_ACCEPT = 0.90
#: Below this the names are not the same company and the caller should say so.
#: Between the two, a human looks: the one real case in that band was
#: "Nakladatelství FORUM s.r.o." against the register's ", organizačná zložka"
#: -- a genuine company whose registered name carries a branch suffix the user
#: omitted, which is exactly what review is for.
NAME_MATCH_REVIEW = 0.60

PARAM_ACCEPT = "l10n_cssk_registry_verify.name_match_accept"
PARAM_REVIEW = "l10n_cssk_registry_verify.name_match_review"

#: Country code -> the autocomplete provider model that answers for it.
#:
#: Looked up in the registry at call time and NOT declared as a dependency:
#: installing this module must not drag in the autocomplete stack, and a
#: deployment that has only the Slovak provider should still work for Slovakia
#: rather than fail to install.
PROVIDERS = {
    "SK": ("partner.autocomplete.provider.orsf_sk", "ORSF", "_orsf_lookup_probe"),
    "CZ": ("partner.autocomplete.provider.ares_cz", "ARES", "_ares_lookup_probe"),
}


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _cssk_registry_provider(self, country_code):
        """The provider model for a country, or ``None``."""
        entry = PROVIDERS.get(country_code)
        if not entry:
            return None
        model_name, source, probe = entry
        if model_name not in self.env:
            return None
        return self.env[model_name], source, probe

    @api.model
    def _cssk_verify_company(self, ico, country_code, typed_name=None, use_cache=True):
        """:meth:`_cssk_verify_registry` plus the name comparison.

        Adds ``name_verdict`` and ``name_score``. Both are ``unknown`` / 0.0
        unless the company verified AND a name was supplied to compare — a
        name cannot be judged against a register that did not answer, and
        pretending otherwise would let an outage read as a mismatch.
        """
        result = self._cssk_verify_registry(
            ico, country_code, use_cache=use_cache
        )
        verdict, score = "unknown", 0.0
        if result["outcome"] == "verified":
            verdict, score = self._cssk_registry_name_verdict(
                typed_name, result["name"]
            )
        result["name_verdict"] = verdict
        result["name_score"] = score
        return result

    @api.model
    def _cssk_verify_registry(self, ico, country_code, use_cache=True):
        """Does this company exist in the state register?

        Returns a dict; ``outcome`` is ``invalid``, ``unsupported``,
        ``absent``, ``verified`` or ``unavailable``. See the module docstring
        for what each means and, more importantly, for why ``absent`` and
        ``unavailable`` must not be collapsed by the caller.

        This method decides nothing. It reports.
        """
        country_code = (country_code or "").upper()
        registry = normalize_registry(ico)
        blank = {
            "outcome": "invalid",
            "registry": registry,
            "country_code": country_code,
            "source": "",
            "name": "",
            "street": "",
            "city": "",
            "zip": "",
            "tax_id": "",
            "vat": "",
            "active": False,
            "cached": False,
        }

        # Checksum first, and never ask the register about a number that
        # cannot be one. It is free, it is instant, and on the production base
        # it is what rejects "Test", "12345" and a pasted company name -- the
        # register would answer 400 for those anyway, at the cost of a request
        # per keystroke from a public form.
        if country_code not in REGISTRY_COUNTRIES or not is_valid_ico(registry):
            if country_code not in REGISTRY_COUNTRIES:
                blank["outcome"] = "unsupported"
            return blank

        provider = self._cssk_registry_provider(country_code)
        if not provider:
            return dict(blank, outcome="unsupported")
        model, source, probe = provider

        if use_cache:
            cached = self.env["cssk.registry.lookup"]._fresh(registry, country_code)
            if cached:
                return cached._as_result()

        outcome, body = getattr(model, probe)(registry)
        if outcome != "ok":
            # "absent" and "unavailable" both arrive here and both stay
            # themselves. Flattening them is the mistake this module exists
            # to prevent.
            result = dict(blank, outcome=outcome, source=source)
            # ``absent`` is an answer and is cached -- that is what blunts a
            # scan of the number space from a public form. ``unavailable`` is
            # not, and ``_remember`` is where that policy lives, so this call
            # stays unconditional rather than splitting the rule across two
            # files.
            self.env["cssk.registry.lookup"]._remember(
                registry, country_code, result
            )
            return result

        parse = (
            self._cssk_registry_parse_ares
            if source == "ARES"
            else self._cssk_registry_parse
        )
        result = dict(
            blank, outcome="verified", source=source, cached=False, **parse(body)
        )
        self.env["cssk.registry.lookup"]._remember(registry, country_code, result)
        return result

    @api.model
    def _cssk_name_thresholds(self):
        param = self.env["ir.config_parameter"].sudo()

        def _read(key, default):
            try:
                return float(param.get_param(key) or default)
            except (TypeError, ValueError):
                return default

        accept = _read(PARAM_ACCEPT, NAME_MATCH_ACCEPT)
        review = _read(PARAM_REVIEW, NAME_MATCH_REVIEW)
        # A review floor above the accept bar would leave no band at all and
        # silently turn every mismatch into a rejection.
        return accept, min(review, accept)

    @api.model
    def _cssk_registry_name_verdict(self, typed_name, official_name):
        """Compare a typed company name with the register's.

        Returns ``(verdict, score)`` where verdict is:

        ``match``
            The same company. Use the register's spelling, not the typed one.
        ``review``
            Close but not the same. A human decides — do not reject, this is
            where a real company with a branch suffix or a trading name lands.
        ``mismatch``
            Not the same company. The typed name can be contradicted outright.
        ``unknown``
            Nothing to compare, because one side is empty.

        Whoever wired the register in should prefer *not asking the user to
        type the name at all* — prefill it — in which case this only ever
        fires for a name the user overrode.
        """
        if not typed_name or not official_name:
            return "unknown", 0.0
        accept, review = self._cssk_name_thresholds()
        score = company_name_similarity(typed_name, official_name)
        if score >= accept:
            return "match", score
        if score >= review:
            return "review", score
        return "mismatch", score

    @api.model
    def _cssk_registry_parse_ares(self, body):
        """Map one ARES record onto the result's fields.

        ARES has no status field: a live company simply has no ``datumZaniku``
        (date of dissolution). Reading its absence as "active" is therefore
        correct, not an assumption — but it is the reason this cannot share
        ORSF's parser, which reads an explicit ``status``.

        In Czechia the VAT number IS the DIČ (``CZ`` + IČO). But it is only a
        VAT number **while the company is actually registered for VAT**, and
        that distinction has teeth on Odoo 19: ``_get_first_matching_fpos``
        demotes ``vat_required`` to a plain filter over
        ``bool(partner.vat and partner.vat != '/')``, so the mere PRESENCE of
        a string in ``vat`` is enough to route an EU partner to a
        reverse-charge fiscal position and waive the VAT. A stale number left
        on a deregistered payer is therefore an under-collected-VAT event, not
        a cosmetic error.

        ARES answers ``dic: null`` for a company that was never registered —
        verified against IČO 21924660, which returns null alongside
        ``stavZdrojeDph: NEEXISTUJICI``. The registration state is checked as
        well because "never registered" and "no longer registered" are
        different facts and only the first is visible in ``dic``.
        """
        seat = body.get("sidlo") or {}
        street = (seat.get("textovaAdresa") or "").split(",")[0].strip()
        dic = body.get("dic") or ""
        vat_live = (body.get("seznamRegistraci") or {}).get("stavZdrojeDph") == "AKTIVNI"
        return {
            "name": body.get("obchodniJmeno") or "",
            "street": street,
            "city": seat.get("nazevObce") or "",
            "zip": (seat.get("psc") and str(seat["psc"])) or "",
            "tax_id": dic,
            # The DIČ stays on `tax_id` regardless -- it is their tax
            # identifier either way -- but it only becomes a VAT number while
            # the VAT registration is live.
            "vat": _prefixed_vat(dic) if vat_live else "",
            "active": not body.get("datumZaniku"),
        }

    @api.model
    def _cssk_registry_parse(self, body):
        """Map one ORSF ``/lookup`` payload onto the result's fields.

        ``address`` is present but partly null for a sole trader: ORSF locks
        street and PSČ behind ``addressLocked`` for GDPR, answering with the
        city alone. That is not an error and must not read as one -- the
        identity fields, which are what a gate actually needs, all come back.
        The caller collects the missing lines from the person instead.
        """
        address = body.get("address") or {}
        # The register says "aktívna"/"active"; a dissolved subject also
        # carries dissolvedOn. Trust either signal, so a wording change on one
        # side cannot silently mark a dead company alive.
        status = (body.get("status") or body.get("statusCode") or "").strip().lower()
        active = status in ("aktívna", "aktivna", "active") and not body.get("dissolvedOn")
        return {
            "name": body.get("name") or "",
            "street": address.get("street") or "",
            "city": address.get("city") or "",
            "zip": address.get("psc") or "",
            "tax_id": body.get("dic") or "",
            # icDph only while the VAT registration is live, which is why it
            # is preferred over deriving one from the DIČ.
            "vat": _prefixed_vat(body.get("icDph")),
            "active": active,
        }

    # ------------------------------------------------------------------
    # Storing what the register said
    #
    # These live on res.partner because they are facts about the COMPANY,
    # not about any one thing it signed up for. A partner verified during
    # signup is still verified when they buy a module from the shop, and a
    # colleague entering the same company in the back office should see the
    # answer rather than ask the register again.
    # ------------------------------------------------------------------

    cssk_registry_outcome = fields.Selection(
        [
            ("verified", "Verified"),
            ("absent", "Not in the register"),
            ("unavailable", "Register unreachable"),
            ("unsupported", "No register for this country"),
            ("invalid", "Not a valid company number"),
        ],
        string="Register check",
        readonly=True,
        copy=False,
    )
    cssk_registry_name = fields.Char(
        string="Name in the register", readonly=True, copy=False
    )
    cssk_registry_active = fields.Boolean(
        string="Active in the register", readonly=True, copy=False,
        help="The register showed the company as active, not dissolved.",
    )
    cssk_name_verdict = fields.Selection(
        [
            ("match", "Matches the register"),
            ("review", "Close, needs a look"),
            ("mismatch", "Does not match"),
            ("unknown", "Not compared"),
        ],
        string="Name check",
        default="unknown",
        readonly=True,
        copy=False,
    )
    cssk_name_score = fields.Float(readonly=True, copy=False, digits=(3, 3))
    cssk_registry_checked_on = fields.Datetime(readonly=True, copy=False)
    cssk_verified_manually = fields.Boolean(
        string="Verified by a person",
        copy=False,
        help="Someone confirmed this company by other means. The escape hatch "
        "for countries whose register we cannot read — without it a customer "
        "outside CZ/SK could never be treated as verified at all, however "
        "obviously real they are.",
    )

    cssk_registry_trusted = fields.Boolean(
        compute="_compute_cssk_registry_trusted",
        store=True,
        string="Company confirmed",
        help="Either the register confirmed an active company whose name "
        "matches, or a person vouched for it.",
    )

    @api.depends(
        "cssk_registry_outcome",
        "cssk_registry_active",
        "cssk_name_verdict",
        "cssk_verified_manually",
    )
    def _compute_cssk_registry_trusted(self):
        """One boolean anything downstream can gate on.

        Stored so it can be searched: a caller that has to re-derive this from
        four fields is a caller that will eventually get one of them wrong.
        """
        for partner in self:
            partner.cssk_registry_trusted = bool(
                partner.cssk_verified_manually
                or (
                    partner.cssk_registry_outcome == "verified"
                    and partner.cssk_registry_active
                    and partner.cssk_name_verdict != "mismatch"
                )
            )

    def _cssk_store_verification(self, result):
        """Record a ``_cssk_verify_company`` result on this partner."""
        self.ensure_one()
        self.sudo().write({
            "cssk_registry_outcome": result.get("outcome") or False,
            "cssk_registry_name": result.get("name") or False,
            "cssk_registry_active": bool(result.get("active")),
            "cssk_name_verdict": result.get("name_verdict") or "unknown",
            "cssk_name_score": result.get("name_score") or 0.0,
            "cssk_registry_checked_on": fields.Datetime.now(),
        })
