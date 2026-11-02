# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import re

from odoo import api, fields, models
from odoo.tools import float_compare, html2plaintext

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

    def _l10n_cssk_find_vs_counterpart_amls(self):
        """Open journal items whose document carries this line's variable
        symbol (leading-zero tolerant). Shared by the reconciliation bridges
        (``_ee`` for Enterprise, ``_oca`` for OCA's widget). Empty recordset on no or ambiguous
        match — ambiguity bails out rather than guessing (a VS is only
        unique per issuer, not globally)."""
        self.ensure_one()
        Aml = self.env["account.move.line"]
        vs = (self.variable_symbol or "").lstrip("0")
        if not vs:
            return Aml
        candidates = Aml.search([
            ("company_id", "=", self.company_id.id),
            ("reconciled", "=", False),
            ("parent_state", "=", "posted"),
            ("account_id.reconcile", "=", True),
            (
                "account_id.account_type",
                "not in",
                ("asset_cash", "liability_credit_card"),
            ),
            ("balance", ">" if self.amount > 0 else "<", 0),
            # candidate superset by trailing digits; the exact leading-zero
            # tolerant comparison is the Python filter below
            ("move_id.l10n_cssk_variable_symbol", "=like", "%" + vs),
        ])
        candidates = candidates.filtered(
            lambda aml: (
                aml.move_id.l10n_cssk_variable_symbol or ""
            ).lstrip("0")
            == vs
            and aml.account_id != self.journal_id.suspense_account_id
            and aml.account_id != self.journal_id.default_account_id
            # a VS is unique per issuer only: once the bank line knows who
            # paid (by account number), another partner's document is not it
            and (
                not self.partner_id
                or aml.partner_id.commercial_partner_id
                == self.partner_id.commercial_partner_id
            )
        )
        if not candidates:
            return Aml
        moves = candidates.move_id
        if len(moves) == 1:
            return candidates
        # several documents share the symbol: only accept a single document
        # whose open amount equals the transaction (company currency only —
        # FX journals are left to the stock matcher / manual handling). Two
        # that both fit are as ambiguous as the symbol was: the first one
        # found is not the one paid, merely the lower id.
        if (
            self.foreign_currency_id
            or self.currency_id != self.company_id.currency_id
        ):
            return Aml
        fitting = Aml
        for move in moves:
            move_amls = candidates.filtered(lambda aml: aml.move_id == move)
            total = sum(move_amls.mapped("amount_residual"))
            if (
                float_compare(
                    abs(total),
                    abs(self.amount),
                    precision_rounding=self.currency_id.rounding,
                )
                == 0
            ):
                fitting |= move_amls
        return fitting if len(fitting.move_id) == 1 else Aml
