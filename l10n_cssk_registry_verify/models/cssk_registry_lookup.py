# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Cached register answers.

A public signup form puts the register one keystroke away from the internet.
Without a cache, a script iterating IČOs is a script hammering ORSF from our
address — which costs us the rate limit first and the anonymous access second.

Only answers are cached. ``unavailable`` is never stored: caching a failure
turns one outage into a long one, and the next caller should get a fresh
attempt rather than an inherited "no".
"""
from datetime import timedelta

from odoo import api, fields, models

#: Hours a confirmed company stays cached. Register identity changes rarely,
#: and the fields used here (name, seat, tax ids, status) change more rarely
#: still. Deliberately not days: a dissolution has to become visible in a
#: timeframe a human would call "today", because the provisioning gate reads
#: ``active`` from here.
TTL_VERIFIED_HOURS = 24
#: Hours an "no such subject" answer stays cached. Much shorter, because a
#: company that does not exist yet is exactly the one a new customer is about
#: to register — a freshly incorporated s.r.o. must not be told "no" all day.
#: Long enough, still, to blunt a scan of the number space.
TTL_ABSENT_HOURS = 1

PARAM_TTL_VERIFIED = "l10n_cssk_registry_verify.ttl_verified_hours"
PARAM_TTL_ABSENT = "l10n_cssk_registry_verify.ttl_absent_hours"


class CsskRegistryLookup(models.Model):
    _name = "cssk.registry.lookup"
    _description = "Cached company-registry lookup"
    _order = "fetched_at desc"
    _rec_name = "registry"

    registry = fields.Char(required=True, index=True, help="Canonical IČO.")
    country_code = fields.Char(required=True, index=True)
    outcome = fields.Selection(
        [("verified", "Verified"), ("absent", "Not in the register")],
        required=True,
        help="Only answers are cached; a failure to reach the register is not.",
    )
    source = fields.Char(help="Which register answered (ORSF, ARES).")
    fetched_at = fields.Datetime(required=True, default=fields.Datetime.now)

    # What the register said. Empty on an ``absent`` row.
    registry_name = fields.Char()
    street = fields.Char()
    city = fields.Char()
    zip = fields.Char()
    tax_id = fields.Char(help="DIČ.")
    vat = fields.Char(help="IČ DPH, only while the VAT registration is live.")
    active_subject = fields.Boolean(
        help="The register still shows the subject as active (not dissolved)."
    )

    _registry_country_uniq = models.Constraint(
        "UNIQUE (registry, country_code)",
        "One cached answer per company registry and country.",
    )

    @api.model
    def _ttl(self, outcome):
        param = self.env["ir.config_parameter"].sudo()
        if outcome == "absent":
            raw, default = param.get_param(PARAM_TTL_ABSENT), TTL_ABSENT_HOURS
        else:
            raw, default = param.get_param(PARAM_TTL_VERIFIED), TTL_VERIFIED_HOURS
        try:
            hours = float(raw) if raw else default
        except (TypeError, ValueError):
            hours = default
        # A negative TTL would mean "already expired", which reads as a way to
        # disable the cache; 0 means exactly that and is honoured.
        return timedelta(hours=max(hours, 0.0))

    @api.model
    def _fresh(self, registry, country_code):
        """The cached answer for this registry, or an empty recordset."""
        row = self.sudo().search(
            [("registry", "=", registry), ("country_code", "=", country_code)],
            limit=1,
        )
        if not row:
            return row
        if fields.Datetime.now() - row.fetched_at >= self._ttl(row.outcome):
            return self.browse()
        return row

    @api.model
    def _remember(self, registry, country_code, result):
        """Store an answer, replacing any previous one for the same company."""
        if result.get("outcome") not in ("verified", "absent"):
            return self.browse()
        vals = {
            "registry": registry,
            "country_code": country_code,
            "outcome": result["outcome"],
            "source": result.get("source") or "",
            "fetched_at": fields.Datetime.now(),
            "registry_name": result.get("name") or "",
            "street": result.get("street") or "",
            "city": result.get("city") or "",
            "zip": result.get("zip") or "",
            "tax_id": result.get("tax_id") or "",
            "vat": result.get("vat") or "",
            "active_subject": bool(result.get("active")),
        }
        existing = self.sudo().search(
            [("registry", "=", registry), ("country_code", "=", country_code)],
            limit=1,
        )
        if existing:
            existing.write(vals)
            return existing
        return self.sudo().create(vals)

    def _as_result(self):
        """Render a cached row back into the shape ``_cssk_verify_registry``
        returns, so a caller cannot tell a cache hit from a live answer except
        by the ``cached`` flag."""
        self.ensure_one()
        return {
            "outcome": self.outcome,
            "registry": self.registry,
            "country_code": self.country_code,
            "source": self.source or "",
            "name": self.registry_name or "",
            "street": self.street or "",
            "city": self.city or "",
            "zip": self.zip or "",
            "tax_id": self.tax_id or "",
            "vat": self.vat or "",
            "active": self.active_subject,
            "cached": True,
        }
