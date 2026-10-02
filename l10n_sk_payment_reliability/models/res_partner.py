# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

import requests

from odoo import _, models

_logger = logging.getLogger(__name__)

_BASE = "https://iz.opendata.financnasprava.sk/api/data"
_IBAN_URL = f"{_BASE}/ds_dph_iban/search"   # registered bank accounts, by IČ DPH
_RAN_URL = f"{_BASE}/ds_iz_ran/search"      # tax-reliability index, by IČO
_LISTS_URL = "https://iz.opendata.financnasprava.sk/api/lists"

#: "Zoznam platiteľov DPH, u ktorých nastali dôvody na zrušenie registrácie"
#: (§ 81 ods. 4 písm. b) ZDPH). The slug is NOT verified against the live API
#: (it needs a key); ``_cssk_sk_searchable`` checks it at run time, so a wrong
#: slug or column reports "unavailable" instead of a clean record.
_DEREG_SLUG = "ds_dphz"
_DEREG_COLUMN = "ic_dph"

#: slug -> searchable columns, successes only: a failed lookup must be asked
#: again next time rather than remembered as "unavailable" until a restart.
_SEARCHABLE_CACHE = {}

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

    def _cssk_sk_searchable(self, slug):
        """The columns FS lets us search ``slug`` by, or ``None``.

        Asked of ``/lists/<slug>`` before trusting a search there: if FS were
        to answer a search on a column it does not index with an empty list,
        that would read exactly like "not on the list".
        """
        if slug in _SEARCHABLE_CACHE:
            return _SEARCHABLE_CACHE[slug]
        key = self._cssk_sk_api_key()
        if not key:
            return None
        try:
            resp = requests.get(
                f"{_LISTS_URL}/{slug}",
                headers={"accept": "application/json", "key": key},
                timeout=20,
            )
            resp.raise_for_status()
            searchable = tuple(resp.json().get("searchable") or ())
        except (requests.exceptions.RequestException, ValueError):
            _logger.exception("FS open-data list %s is not available", slug)
            return None
        _SEARCHABLE_CACHE[slug] = searchable
        return searchable

    def _cssk_get_vat_deregistration(self):
        self.ensure_one()
        if (self.country_id.code or (self.vat or "")[:2].upper()) != "SK" or not self.vat:
            return super()._cssk_get_vat_deregistration()
        searchable = self._cssk_sk_searchable(_DEREG_SLUG)
        if not searchable or _DEREG_COLUMN not in searchable:
            if searchable is not None:
                _logger.error(
                    "FS list %s cannot be searched by %s (searchable: %s); "
                    "the VAT-deregistration check is unavailable",
                    _DEREG_SLUG, _DEREG_COLUMN, ", ".join(searchable),
                )
            return None
        data = self._cssk_sk_query(
            f"{_BASE}/{_DEREG_SLUG}/search", _DEREG_COLUMN, self.vat)
        if data is None:
            return None
        if not data:
            return False
        row = data[0]
        since = next(
            (str(row[k]) for k in sorted(row) if "dat" in k.lower() and row[k]),
            None,
        )
        return _("listed since %s", since) if since else _("listed")

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
