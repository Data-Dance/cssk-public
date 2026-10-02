# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

#: The columns of the Czech peněžní deník, as ``(key, heading, category codes)``.
#:
#: **Nothing prescribes these.** § 7b ZDP asks for "členění potřebné pro zjištění
#: základu daně" and stops there, so the layout follows what POHODA and Money S3
#: put on the screen — which is what the accountant reading it will expect.
#: ``None`` is the catch-all for that side, so a category invented later still
#: lands somewhere and the book keeps adding up.
DENIK_COLUMNS = [
    ("p_zbozi", "Prodej zboží", ["P1"]),
    ("p_vyrobky", "Prodej výrobků a služeb", ["P2"]),
    ("p_ostatni", "Ostatní zdanitelný příjem", ["P3"]),
    ("pn", "Nedaňový příjem", None),
    ("v_material", "Materiál", ["V1"]),
    ("v_zbozi", "Zboží", ["V2"]),
    ("v_drobny", "Drobný majetek", ["V3"]),
    ("v_mzdy", "Mzdy", ["V4"]),
    ("v_odvody", "Odvody za zaměstnance", ["V5"]),
    ("v_rezie", "Provozní režie a služby", ["V6"]),
    ("v_ostatni", "Ostatní daňový výdaj", ["V9", "Z1", "Z2"]),
    ("vn", "Nedaňový výdaj", None),
]


class L10nCzCashDenik(models.AbstractModel):
    """The peněžní deník, Czech layout.

    Same rows as the Slovak book, laid out the way Czech products lay them out:
    a materiál column apart from zboží, odvody za zaměstnance apart from mzdy,
    and pojistné podnikatele on the nedaňový side where Czech law puts it.
    """

    _name = "report.l10n_cz_cash_journal.report_penezni_denik"
    _description = "Peněžní deník (report)"

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        company = self.env["res.company"].browse(
            data.get("company_id") or self.env.company.id)
        date_from = fields.Date.to_date(data.get("date_from")) \
            or fields.Date.context_today(self).replace(month=1, day=1)
        date_to = fields.Date.to_date(data.get("date_to")) \
            or fields.Date.context_today(self)
        return self._cz_denik_values(company, date_from, date_to)

    @api.model
    def _cz_denik_values(self, company, date_from, date_to):
        """The book for a period: rows, column totals and running balances."""
        rows = self.env["cssk.cash.journal.line"].search([
            ("company_id", "=", company.id),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
        ])
        opening_cash = self._cz_money_balance(company, date_from, "cash")
        opening_bank = self._cz_money_balance(company, date_from, "bank")
        cash, bank = opening_cash, opening_bank

        totals = dict.fromkeys(
            [key for key, _heading, _codes in DENIK_COLUMNS], 0.0)
        totals.update({
            "pokladna_prijem": 0.0, "pokladna_vydej": 0.0,
            "banka_prijem": 0.0, "banka_vydej": 0.0,
            "prubezne_prijem": 0.0, "prubezne_vydej": 0.0,
            "dph_prijem": 0.0, "dph_vydej": 0.0,
        })

        lines = []
        for row in rows:
            cells = dict.fromkeys(totals, 0.0)
            gross = row.amount + row.amount_tax
            # The money columns follow the money, not the classification.
            incoming = row.money_direction == "in"

            if not row.non_cash:
                if row.kind == "transit":
                    cells["prubezne_prijem" if incoming
                          else "prubezne_vydej"] = gross
                if row.payment_kind == "cash":
                    cells["pokladna_prijem" if incoming
                          else "pokladna_vydej"] = gross
                    cash += gross if incoming else -gross
                elif row.payment_kind == "bank":
                    cells["banka_prijem" if incoming
                          else "banka_vydej"] = gross
                    bank += gross if incoming else -gross

            if row.amount_tax:
                cells["dph_prijem" if incoming else "dph_vydej"] = row.amount_tax

            column = self._cz_column_for(row)
            if column:
                # Negative for a storno (dobropis), as POHODA shows it.
                cells[column] = row.amount_classified

            for key, value in cells.items():
                totals[key] += value
            lines.append({"row": row, "cells": cells, "cash": cash, "bank": bank})

        return {
            "doc_model": "cssk.cash.journal.line",
            "docs": rows,
            "company": company,
            "date_from": date_from,
            "date_to": date_to,
            "columns": DENIK_COLUMNS,
            "lines": lines,
            "totals": totals,
            "opening_cash": opening_cash,
            "opening_bank": opening_bank,
            "closing_cash": cash,
            "closing_bank": bank,
        }

    @api.model
    def _cz_column_for(self, row):
        if row.kind == "transit":
            return None
        code = row.category_id.code
        for key, _heading, codes in DENIK_COLUMNS:
            if codes and code in codes:
                return key
        if row.kind == "income":
            return "p_ostatni" if row.taxable else "pn"
        return "v_ostatni" if row.taxable else "vn"

    @api.model
    def _cz_money_balance(self, company, date_from, kind):
        """Opening balance of the till or the bank.

        The bank side includes the transit accounts, for the same reason as in
        the Slovak book: until a statement is imported the money sits on the
        outstanding receipts account, and once it is, the outstanding and
        suspense legs net out.
        """
        journals = self.env["account.journal"].search([
            ("company_id", "=", company.id),
            ("type", "=", kind),
        ])
        accounts = journals.default_account_id
        if kind == "bank":
            accounts |= self.env["cssk.cash.journal.line"] \
                ._cssk_transit_accounts(company)
        if not accounts:
            return 0.0
        lines = self.env["account.move.line"].search([
            ("company_id", "=", company.id),
            ("parent_state", "=", "posted"),
            ("date", "<", date_from),
            ("account_id", "in", accounts.ids),
        ])
        return sum(lines.mapped("balance"))
