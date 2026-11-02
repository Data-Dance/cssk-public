# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

import requests

from odoo import models

_logger = logging.getLogger(__name__)

_BASE = "https://iz.opendata.financnasprava.sk/api/data"
_IBAN_URL = f"{_BASE}/ds_dph_iban/search"   # registered bank accounts, by IČ DPH
_RAN_URL = f"{_BASE}/ds_iz_ran/search"      # tax-reliability index, by IČO

# SK "index daňovej spoľahlivosti" -> normalised rating.
_RAN_MAP = {
    "vysoko spoľahlivý": "highly_reliable",
    "spoľahlivý": "reliable",
    "menej spoľahlivý": "less_reliable",
}


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _cssk_sk_api_key(self):
        return self.env["ir.config_parameter"].sudo().get_param("fa_api_key")

    def _cssk_sk_query(self, url, column, value):
        """Return the ``data`` list from an FS open-data search, or None."""
        key = self._cssk_sk_api_key()
        if not key or not value:
            return None
        try:
            resp = requests.get(
                url,
                headers={"accept": "application/json", "key": key},
                params={"page": "1", "column": column, "search": value},
                timeout=20,
            )
            resp.raise_for_status()
            return resp.json().get("data", [])
        except (requests.exceptions.RequestException, ValueError):
            _logger.exception("FS open-data query failed: %s %s=%s", url, column, value)
            return None

    def _cssk_get_registered_accounts(self):
        self.ensure_one()
        if (self.country_id.code or self.vat[:2] if self.vat else "") != "SK":
            return super()._cssk_get_registered_accounts()
        data = self._cssk_sk_query(_IBAN_URL, "ic_dph", self.vat)
        if data is None:
            return None
        return [
            self._cssk_sanitize_iban(row.get("iban"))
            for row in data
            if row.get("iban")
        ]

    def _cssk_get_tax_reliability(self):
        self.ensure_one()
        if (self.country_id.code or "") != "SK":
            return super()._cssk_get_tax_reliability()
        data = self._cssk_sk_query(_RAN_URL, "ico", self.company_registry)
        if not data:
            return None if data is None else "unknown"
        return _RAN_MAP.get((data[0].get("ids") or "").strip(), "unknown")

    @staticmethod
    def _cssk_sanitize_iban(iban):
        return (iban or "").replace(" ", "").upper()
