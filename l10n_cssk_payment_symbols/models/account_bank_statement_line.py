# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import re

from odoo import api, fields, models
from odoo.tools import html2plaintext

# Token forms seen in bank labels: "VS:1234567890", "VS 123", "VS=123",
# "/VS/123" (structured remittance), "VS123".
_TOKEN_RES = {
    "variable_symbol": re.compile(
        r"(?:\bVS[:=]?\s*|/VS/?)(\d{1,10})", re.IGNORECASE
    ),
    "constant_symbol": re.compile(
        r"(?:\bKS[:=]?\s*|/KS/?)(\d{1,4})", re.IGNORECASE
    ),
    "specific_symbol": re.compile(
        r"(?:\bSS[:=]?\s*|/SS/?)(\d{1,10})", re.IGNORECASE
    ),
}

# Keys probed (recursively) in the bank connector's transaction_details JSON.
# "variable_code" first — the key upstream odoo/odoo#275611 extracts.
_DETAIL_KEYS = {
    "variable_symbol": (
        "variable_code",
        "variable_symbol",
        "variableSymbol",
        "vs",
    ),
    "constant_symbol": (
        "constant_code",
        "constant_symbol",
        "constantSymbol",
        "ks",
    ),
    "specific_symbol": (
        "specific_code",
        "specific_symbol",
        "specificSymbol",
        "ss",
    ),
}

_MAX_DIGITS = {"variable_symbol": 10, "constant_symbol": 4, "specific_symbol": 10}


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    # Field names and create()-time population are deliberately compatible
    # with upstream odoo/odoo#275611 (l10n_cz adds variable_symbol the same
    # way on master) so both implementations coexist as no-ops of each other.
    variable_symbol = fields.Char(string="Variable Symbol", copy=False)
    constant_symbol = fields.Char(string="Constant Symbol", copy=False)
    specific_symbol = fields.Char(string="Specific Symbol", copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._l10n_cssk_apply_symbols_in_vals(vals)
        return super().create(vals_list)

    @api.model
    def _l10n_cssk_apply_symbols_in_vals(self, vals):
        """Fill the symbol fields in a create() vals dict from, in order:
        explicit values, the connector's transaction_details JSON, and
        VS:-style tokens in the label. The variable symbol is additionally
        prefixed into payment_ref ("<vs> - <label>") so stock matching
        heuristics see it — never twice (guards against upstream #275611
        or a re-import having prefixed already)."""
        details = vals.get("transaction_details")
        payment_ref = vals.get("payment_ref") or ""
        # The label first, then the other texts a bank format carries. OCA's
        # CAMT import puts Ustrd in payment_ref and the structured reference or
        # EndToEndId in ref, and a SEPA payment from a Czech or Slovak bank
        # often has its symbols ONLY there ("/VS53101/SS/KS", Fio
        # "?/VS53155/SS/KS") while Ustrd is free text.
        texts = [
            payment_ref,
            vals.get("ref") or "",
            html2plaintext(vals.get("narration") or ""),
        ]
        for field_name, keys in _DETAIL_KEYS.items():
            value = vals.get(field_name)
            if not value and details:
                value = self._l10n_cssk_find_detail_value(details, keys)
            for text in texts:
                if value:
                    break
                match = text and _TOKEN_RES[field_name].search(text)
                value = match.group(1) if match else False
            if value:
                value = re.sub(r"\D", "", str(value))[
                    : _MAX_DIGITS[field_name]
                ]
            # "SS0" is a bank's way of saying there is none.
            if value and not value.strip("0"):
                value = False
            if value:
                vals[field_name] = value
        variable_symbol = vals.get("variable_symbol")
        if variable_symbol and variable_symbol not in payment_ref:
            vals["payment_ref"] = (
                f"{variable_symbol} - {payment_ref}"
                if payment_ref
                else variable_symbol
            )
        return vals

    @api.model
    def _l10n_cssk_find_detail_value(self, data, keys):
        """Recursively look up the first non-empty ``keys`` entry in the
        (possibly JSON-string) transaction_details structure."""
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except ValueError:
                return False
        if isinstance(data, dict):
            for key in keys:
                if data.get(key):
                    return data[key]
            for value in data.values():
                found = self._l10n_cssk_find_detail_value(value, keys)
                if found:
                    return found
        elif isinstance(data, list):
            for item in data:
                found = self._l10n_cssk_find_detail_value(item, keys)
                if found:
                    return found
        return False
