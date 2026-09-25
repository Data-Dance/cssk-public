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

    vies_consultation_number = fields.Char(
        string="VIES Consultation No.",
        tracking=True,
        copy=False,
        help="Official EU VIES request identifier returned for a valid "
        "qualified check — the legal proof that this VAT was confirmed.",
    )
    vies_check_date = fields.Datetime(
        string="VIES Checked On",
        copy=False,
        help="When this partner's VAT was last validated directly against VIES.",
    )
    vies_fault_date = fields.Datetime(
        string="VIES Last Fault",
        copy=False,
        help="When the last scheduled direct VIES check for this partner "
        "faulted (service unreachable / busy). Lets the scheduled refresh "
        "rotate faulting partners out of its batch window instead of "
        "retrying them forever.",
    )
    vies_request_date = fields.Date(
        string="VIES Request Date",
        copy=False,
        help="Date VIES reports for the consultation (the service's own date).",
    )
    vies_trader_name = fields.Char(string="VIES Registered Name", copy=False)
    vies_address = fields.Char(string="VIES Registered Address", copy=False)
    vies_name_match = fields.Char(
        string="VIES Name Match",
        copy=False,
        help="Whether the registered trader name matches this partner "
        "(VALID / INVALID / NOT_PROCESSED).",
    )

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
        "fault"). When ``store`` is set, the consultation number and the rest
        of the proof are written onto the partner.
        """
        self.ensure_one()
        data = self._vies_query_direct(
            self.vat, self.env.company.vat, trader_name=self.name
        )
        if data is None:
            return "fault"
        return self._apply_vies_direct_result(data, store=store)

    def _apply_vies_direct_result(self, data, store=True):
        """Map a VIES REST response to a status, optionally storing proof."""
        self.ensure_one()
        user_error = (data.get("userError") or "").upper()
        valid = bool(data.get("valid"))

        # A transient service fault must never overwrite proof or flip validity.
        if not valid and user_error in _VIES_TRANSIENT_ERRORS:
            return "fault"

        if store:
            vals = {
                "vies_check_date": fields.Datetime.now(),
                "vies_request_date": self._parse_vies_date(data.get("requestDate")),
            }
            if valid:
                # The registered name/address come back in ``name``/``address``
                # (only on an approximate check); ``traderName`` is the echoed
                # match field and is often the "---" placeholder.
                name = data.get("name") or ""
                if name == "---":
                    name = ""
                vals.update(
                    {
                        "vies_consultation_number": data.get("requestIdentifier")
                        or "",
                        "vies_trader_name": name,
                        "vies_address": (data.get("address") or "").strip(),
                        "vies_name_match": data.get("traderNameMatch") or "",
                    }
                )
            else:
                # Confirmed not registered — clear any stale proof.
                vals.update(
                    {
                        "vies_consultation_number": "",
                        "vies_trader_name": "",
                        "vies_address": "",
                        "vies_name_match": "",
                    }
                )
            self.write(vals)

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
        base_domain = Domain(
            [
                ("parent_id", "=", False),
                "|",
                ("vies_check_date", "=", False),
                ("vies_check_date", "<", cutoff),
                # Faulting partners were stamped on their last attempt and
                # rotate out of the window until the cutoff passes again.
                "|",
                ("vies_fault_date", "=", False),
                ("vies_fault_date", "<", cutoff),
            ]
        )
        for company in companies:
            partners = (
                self.with_company(company)
                .sudo()
                .search(eu_vat_domain & base_domain, limit=limit)
            )
            for partner in partners:
                partner = partner.with_company(company)
                status = partner._check_vies_direct(store=True)
                if status == "fault":
                    # Stamp the fault so this partner leaves the window even
                    # though no successful check date could be written.
                    partner.vies_fault_date = fields.Datetime.now()
                partner._update_vies_status(status)
                # Commit each partner (progress survives a cron kill) and
                # stop cleanly when the cron's time budget runs out.
                if not self.env["ir.cron"]._commit_progress(1):
                    return
                # VIES rate-limits aggressively — pace the batch.
                if throttle:
                    time.sleep(throttle)
