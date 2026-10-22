# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Bulk refresh of a partner base against the register.

The dispatcher's *Update* action reads the **full** company record per partner,
which is right for one contact and wrong for five hundred: that endpoint allows
30 requests a minute, so a bulk run dies after about twenty and then quietly
returns nothing for the rest — indistinguishable from the data not existing.

This action uses ``POST /lookup/batch`` instead: 100 IČOs a call, 60 calls a
minute. It refreshes identity — name, address, IČ DPH, DIČ, status — and
nothing deeper, because that endpoint carries nothing deeper. Use *Update* on
the handful of partners whose register coordinates, VAT paragraph or activity
list actually matter.
"""

import logging

from odoo import _, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def action_orsf_bulk_refresh(self):
        """Refresh identity for every selected partner in a couple of calls."""
        provider = self.env.get("partner.autocomplete.provider.orsf_sk")
        if provider is None:
            return True

        by_ico = {}
        skipped = self.browse()
        for partner in self:
            ico = provider._orsf_normalise_ico(
                partner.company_registry or partner.partner_gid
            )
            if ico:
                # Two partners can legitimately carry the same IČO — a company
                # and a duplicate of it — so this maps one IČO to many.
                by_ico.setdefault(ico, self.browse())
                by_ico[ico] |= partner
            else:
                skipped |= partner

        records = provider._orsf_lookup_batch(list(by_ico)) if by_ico else {}

        updated = self.browse()
        for ico, partners in by_ico.items():
            record = records.get(ico)
            if not record or not record.get("name"):
                continue
            vals = provider._orsf_company_vals(record)
            for partner in partners:
                try:
                    partner.write(partner._process_partner_data(dict(vals)))
                    updated |= partner
                except Exception as err:  # noqa: BLE001 - one bad row must not
                    # abort the rest of a bulk run.
                    _logger.warning(
                        "ORSF bulk refresh failed for %s: %s",
                        partner.display_name,
                        err,
                    )

        missing = len(by_ico) - len(records)
        self._orsf_report_bulk_refresh(len(updated), missing, len(skipped))
        return True

    def _orsf_report_bulk_refresh(self, updated, missing, skipped):
        """Say what happened. A silent bulk action is indistinguishable from a
        broken one, which is exactly how the rate-limited version looked."""
        parts = [_("%s updated", updated)]
        if missing:
            parts.append(_("%s not in the register", missing))
        if skipped:
            parts.append(_("%s without a usable IČO", skipped))
        self.env.user._bus_send("simple_notification", {
            "type": "success" if updated else "warning",
            "title": _("ORSF bulk refresh"),
            "message": ", ".join(parts) + _(
                ". Identity only — run Update on a partner to refresh its "
                "register coordinates, VAT paragraph and activities."
            ),
        })
