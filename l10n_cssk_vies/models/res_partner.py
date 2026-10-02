# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import time

import requests

from odoo import _, api, fields, models
from odoo.fields import Domain

_logger = logging.getLogger(__name__)

# European Commission VIES REST service. The POST form, given a requester
# member state + VAT, returns the official ``requestIdentifier`` (consultation
# number) that is the legal proof of a qualified intra-Community check.
VIES_REST_URL = (
    "https://ec.europa.eu/taxation_customs/vies/rest-api/check-vat-number"
)

# VIES service-side conditions that mean "try again later", NOT "VAT invalid".
_VIES_TRANSIENT_ERRORS = {
    "MS_UNAVAILABLE",
    "MS_MAX_CONCURRENT_REQ",
    "GLOBAL_MAX_CONCURRENT_REQ",
    "SERVICE_UNAVAILABLE",
    "TIMEOUT",
    "BUSY",
}


class ResPartner(models.Model):
    _inherit = "res.partner"

    # The proof below is computed from the check log for the CURRENT company:
    # the consultation number VIES issues belongs to the requester, and two
    # companies sharing a partner used to overwrite each other's.
    vies_check_ids = fields.One2many(
        "cssk.vies.check", "partner_id", string="VIES Checks", readonly=True,
    )
    vies_consultation_number = fields.Char(
        string="VIES Consultation No.",
        compute="_compute_vies_proof",
        help="Official EU VIES request identifier returned for a valid "
        "qualified check — the legal proof that this VAT was confirmed.",
    )
    vies_check_date = fields.Datetime(
        string="VIES Checked On",
        compute="_compute_vies_proof",
        help="When this company last validated the partner's VAT directly "
        "against VIES.",
    )
    vies_fault_date = fields.Datetime(
        string="VIES Last Fault",
        compute="_compute_vies_proof",
        help="When the last direct VIES check for this partner faulted "
        "(service unreachable / busy). Lets the scheduled refresh rotate "
        "faulting partners out of its batch window instead of retrying them "
        "forever.",
    )
    vies_request_date = fields.Date(
        string="VIES Request Date",
        compute="_compute_vies_proof",
        help="Date VIES reports for the consultation (the service's own date).",
    )
    vies_trader_name = fields.Char(
        string="VIES Registered Name", compute="_compute_vies_proof")
    vies_address = fields.Char(
        string="VIES Registered Address", compute="_compute_vies_proof")
    vies_name_match = fields.Char(
        string="VIES Name Match",
        compute="_compute_vies_proof",
        help="Whether the registered trader name matches this partner "
        "(VALID / INVALID / NOT_PROCESSED).",
    )

    @api.depends("vies_check_ids")
    @api.depends_context("company")
    def _compute_vies_proof(self):
        """The latest check this company made, else a migrated legacy one.

        A migrated check carries no company (the requester was never stored),
        so it stands in until the company checks for itself.
        """
        company = self.env.company
        for partner in self:
            checks = partner.sudo().vies_check_ids
            own = checks.filtered(lambda c: c.company_id == company)
            pool = own or checks.filtered(lambda c: not c.company_id)
            answered = pool.filtered(lambda c: c.result != "fault")[:1]
            fault = pool.filtered(lambda c: c.result == "fault")[:1]
            valid = answered if answered.result == "valid" else answered.browse()
            partner.vies_check_date = answered.check_date
            partner.vies_request_date = answered.request_date
            partner.vies_fault_date = fault.check_date
            partner.vies_consultation_number = valid.consultation_number
            partner.vies_trader_name = valid.trader_name
            partner.vies_address = valid.address
            partner.vies_name_match = valid.name_match

    def _vies_log(self, result, data=None, fault_reason=None):
        """Record one check by the current company. Created as superuser: the
        log is evidence, so users read it but never write it."""
        self.ensure_one()
        data = data or {}
        vals = {
            "partner_id": self.id,
            "company_id": self.env.company.id,
            "requester_vat": self.env.company.vat or False,
            "vat": self.vat or False,
            "result": result,
            "request_date": self._parse_vies_date(data.get("requestDate")),
            "fault_reason": fault_reason or False,
            "user_id": self.env.user.id,
        }
        if result == "valid":
            # The registered name/address come back in ``name``/``address``
            # (only on an approximate check); ``traderName`` is the echoed
            # match field and is often the "---" placeholder.
            name = data.get("name") or ""
            if name == "---":
                name = ""
            vals.update({
                "consultation_number": data.get("requestIdentifier") or False,
                "trader_name": name or False,
                "address": (data.get("address") or "").strip() or False,
                "name_match": data.get("traderNameMatch") or False,
            })
        check = self.env["cssk.vies.check"].sudo().create(vals)
        self.invalidate_recordset(["vies_check_ids"])
        return check

    # ------------------------------------------------------------------
    # Routing: core has a single VIES call site (_check_vies_iap), invoked
    # from _compute_vies_valid. Redirect it to the direct service when the
    # company opted out of IAP. During that compute we must NOT write sibling
    # fields, so proof storage is suppressed (store=False) on this path.
    # ------------------------------------------------------------------
    def _check_vies_iap(self):
        if self.env.company.vies_use_direct:
            return self._check_vies_direct(store=False)
        return super()._check_vies_iap()

    @api.model
    def _vies_query_direct(self, vat, requester_vat=None, trader_name=None):
        """Low-level qualified VIES REST call for an arbitrary VAT string.

        Returns the parsed response ``dict`` (with ``valid`` /
        ``requestIdentifier`` / ``name`` / ``address`` / ``traderNameMatch``),
        or ``None`` on a network or decoding fault. Supplying ``requester_vat``
        triggers the qualified check that yields the official consultation
        number; supplying ``trader_name`` runs the approximate match, which
        also makes VIES disclose the registered name and address.
        """
        country_code, number = self._split_vat(vat or "")
        if not country_code or not number:
            return {"valid": False}

        payload = {"countryCode": country_code, "vatNumber": number}
        req_cc, req_num = self._split_vat(requester_vat or "")
        if req_cc and req_num:
            payload["requesterMemberStateCode"] = req_cc
            payload["requesterNumber"] = req_num
        if trader_name:
            payload["traderName"] = trader_name

        try:
            resp = requests.post(VIES_REST_URL, json=payload, timeout=20)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException:
            _logger.exception("Direct VIES check failed for %s", vat)
            return None
        except ValueError:
            _logger.error("Direct VIES returned non-JSON for %s", vat)
            return None

    def _check_vies_direct(self, store=True):
        """Validate this partner's VAT against the EU VIES REST service.

        Returns a core-compatible status string ("valid" / "invalid" /
        "fault"). When ``store`` is set, the outcome — a fault included — is
        logged for the current company.
        """
        self.ensure_one()
        data = self._vies_query_direct(
            self.vat, self.env.company.vat, trader_name=self.name
        )
        if data is None:
            if store:
                self._vies_log("fault", fault_reason="no answer from VIES")
            return "fault"
        return self._apply_vies_direct_result(data, store=store)

    def _apply_vies_direct_result(self, data, store=True):
        """Map a VIES REST response to a status, optionally logging proof."""
        self.ensure_one()
        user_error = (data.get("userError") or "").upper()
        valid = bool(data.get("valid"))

        # A transient service fault is not an answer: it is logged as a fault
        # and never replaces the last real proof.
        if not valid and user_error in _VIES_TRANSIENT_ERRORS:
            if store:
                self._vies_log("fault", data, fault_reason=user_error)
            return "fault"

        if store:
            self._vies_log("valid" if valid else "invalid", data)
        return "valid" if valid else "invalid"

    @api.model
    def _parse_vies_date(self, raw):
        # VIES dates look like "2026-06-11T17:36:15.872Z" — keep the date part.
        if not raw or not isinstance(raw, str):
            return False
        try:
            return fields.Date.to_date(raw[:10])
        except (ValueError, TypeError):
            return False

    # ------------------------------------------------------------------
    # On-demand + scheduled refresh (store proof; run outside any compute).
    # ------------------------------------------------------------------
    def action_vies_check_direct(self):
        """Manually run a direct VIES check now, regardless of the IAP toggle.

        Reports the outcome. Without this the button is indistinguishable from
        a dead control: re-checking a partner who was already valid changes
        nothing on screen, so the only evidence anything happened is a new
        line in the chatter. Notifying over the bus rather than returning a
        client action keeps the ``True`` return, and with it the form reload
        that refreshes the stored proof.
        """
        valid = self.browse()
        invalid = self.browse()
        faulted = self.browse()
        for partner in self:
            status = partner._check_vies_direct(store=True)
            partner._update_vies_status(status)
            if status == "valid":
                valid |= partner
            elif status == "invalid":
                invalid |= partner
            else:
                faulted |= partner

        def _names(partners):
            return ", ".join(partners.mapped("display_name"))

        if faulted:
            self.env.user._bus_send("simple_notification", {
                "type": "warning",
                "title": _("VIES did not answer"),
                "message": _(
                    "No answer for %(names)s. The service is often briefly "
                    "unavailable; nothing was changed on the partner.",
                    names=_names(faulted),
                ),
            })
        if invalid:
            self.env.user._bus_send("simple_notification", {
                "type": "danger",
                "title": _("Not valid in VIES"),
                "message": _("VIES does not recognise the VAT number of %(names)s.",
                             names=_names(invalid)),
            })
        if valid:
            numbers = ", ".join(
                n for n in valid.mapped("vies_consultation_number") if n
            )
            self.env.user._bus_send("simple_notification", {
                "type": "success",
                "title": _("Valid in VIES"),
                "message": (
                    _("%(names)s — consultation no. %(numbers)s",
                      names=_names(valid), numbers=numbers)
                    if numbers
                    else _("%(names)s is valid.", names=_names(valid))
                ),
            })
        return True

    @api.model
    def _vies_eu_vat_prefixes(self):
        """VAT prefixes VIES can actually validate.

        Derived from the EU country group; Greece uses the historical 'EL'
        prefix instead of its ISO code 'GR', and Northern Ireland kept the
        'XI' prefix in the EU VAT area after Brexit.
        """
        eu = self.env.ref("base.europe", raise_if_not_found=False)
        codes = {c for c in (eu.country_ids.mapped("code") if eu else []) if c}
        codes.discard("GR")
        codes |= {"EL", "XI"}
        return sorted(codes)

    @api.model
    def _cron_check_vies_direct(self, stale_days=7, limit=200, throttle=0.5):
        """Refresh partners with an EU VAT for companies using direct VIES."""
        companies = self.env["res.company"].sudo().search(
            [("vies_use_direct", "=", True)]
        )
        if not companies:
            return
        cutoff = fields.Datetime.subtract(fields.Datetime.now(), days=stale_days)
        # Only VATs VIES can know: otherwise partners with non-EU VAT formats
        # fault forever, permanently occupy the ``limit`` window and starve
        # the EU partners that actually need a refresh.
        eu_vat_domain = Domain.OR(
            [("vat", "=ilike", prefix + "%")]
            for prefix in self._vies_eu_vat_prefixes()
        )
        Check = self.env["cssk.vies.check"].sudo()
        for company in companies:
            # Anything this company checked within the window — faults
            # included, so a faulting partner rotates out instead of being
            # retried forever and starving everyone behind it.
            recent = Check.search([
                ("company_id", "=", company.id),
                ("check_date", ">=", cutoff),
            ]).partner_id
            partners = (
                self.with_company(company)
                .sudo()
                .search(
                    eu_vat_domain
                    & Domain([("parent_id", "=", False),
                              ("id", "not in", recent.ids)]),
                    limit=limit,
                )
            )
            for partner in partners:
                partner = partner.with_company(company)
                status = partner._check_vies_direct(store=True)
                partner._update_vies_status(status)
                # Commit each partner (progress survives a cron kill) and
                # stop cleanly when the cron's time budget runs out.
                if not self.env["ir.cron"]._commit_progress(1):
                    return
                # VIES rate-limits aggressively — pace the batch.
                if throttle:
                    time.sleep(throttle)
