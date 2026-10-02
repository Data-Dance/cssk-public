# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

#: The columns of the statutory peňažný denník, per opatrenie MF/27076/2007-74,
#: § 4, as ``(key, heading, category codes)``. A column collects the rows whose
#: category is one of its codes; ``None`` means "every category of that kind
#: that no other column claims", which is what keeps a hand-made category out of
#: nowhere.
DENNIK_COLUMNS = [
    ("p_tovar", "Predaj tovaru", ["P1"]),
    ("p_vyrobky", "Predaj výrobkov a služieb", ["P2"]),
    ("p_ostatne", "Ostatné príjmy", ["P3"]),
    ("pn", "Príjmy neovplyvňujúce ZD", None),
    ("v_zasoby", "Zásoby", ["V1"]),
    ("v_sluzby", "Služby", ["V2"]),
    ("v_mzdy", "Mzdy", ["V3"]),
    ("v_poistne", "Poistné a príspevky", ["V4", "V5"]),
    ("v_socfond", "Sociálny fond", ["V6"]),
    ("v_ostatne", "Ostatné výdavky", ["V9", "Z1", "Z2"]),
    ("vn", "Výdavky neovplyvňujúce ZD", None),
]


class L10nSkCashDennik(models.AbstractModel):
    """The peňažný denník in the column layout the opatrenie prescribes.

    Two things the statute asks for that a plain list of rows does not give:

    * **the grid** — pokladnica and banka each with a príjem and a výdaj column,
      priebežné položky likewise, then the income and expense breakdown
      (§ 4 ods. 1);
    * **the running balances** — the entries must reconcile to the cash and bank
      balances (§ 4 ods. 10), so the book carries them line by line and the
      reader can tie the last one to the bank statement.

    Kept as a report rather than stored fields: the layout is one country's
    presentation of rows that already exist, and a second country lays the same
    rows out differently.
    """

    _name = "report.l10n_sk_cash_journal.report_penazny_dennik"
    _description = "Peňažný denník (report)"

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        company = self.env["res.company"].browse(
            data.get("company_id") or self.env.company.id)
        date_from = fields.Date.to_date(data.get("date_from")) \
            or fields.Date.context_today(self).replace(month=1, day=1)
        date_to = fields.Date.to_date(data.get("date_to")) \
            or fields.Date.context_today(self)
        return self._sk_dennik_values(company, date_from, date_to)

    @api.model
    def _sk_dennik_values(self, company, date_from, date_to):
        """The whole book for a period: rows, column totals, closing balances."""
        rows = self.env["cssk.cash.journal.line"].search([
            ("company_id", "=", company.id),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
        ])
        claimed = {code for _key, _heading, codes in DENNIK_COLUMNS
                   if codes for code in codes}

        opening_cash = self._sk_money_balance(company, date_from, "cash")
        opening_bank = self._sk_money_balance(company, date_from, "bank")
        cash, bank = opening_cash, opening_bank

        lines = []
        totals = dict.fromkeys(
            [key for key, _heading, _codes in DENNIK_COLUMNS], 0.0)
        totals.update({
            "pokladnica_prijem": 0.0, "pokladnica_vydaj": 0.0,
            "banka_prijem": 0.0, "banka_vydaj": 0.0,
            "priebezne_prijem": 0.0, "priebezne_vydaj": 0.0,
            "dph_prijem": 0.0, "dph_vydaj": 0.0,
        })

        for row in rows:
            cells = dict.fromkeys(totals, 0.0)
            gross = row.amount + row.amount_tax
            # The money columns follow the money, not the classification: a
            # refunded sale leaves the bank even though it is an income row.
            incoming = row.money_direction == "in"

            if row.non_cash:
                pass  # a nepeňažný row moves no money and no money column
            elif row.kind == "transit":
                key = "priebezne_prijem" if incoming else "priebezne_vydaj"
                cells[key] = gross
                self._sk_add_money(cells, row, gross, incoming)
            else:
                self._sk_add_money(cells, row, gross, incoming)

            if row.amount_tax:
                cells["dph_prijem" if incoming else "dph_vydaj"] = row.amount_tax

            column = self._sk_column_for(row, claimed)
            if column:
                # Negative for a storno, so a refund reduces its own column
                # instead of being added to it.
                cells[column] = row.amount_classified

            if not row.non_cash:
                if row.payment_kind == "cash":
                    cash += gross if incoming else -gross
                elif row.payment_kind == "bank":
                    bank += gross if incoming else -gross

            for key, value in cells.items():
                totals[key] += value
            lines.append({
                "row": row,
                "cells": cells,
                "cash": cash,
                "bank": bank,
            })

        return {
            "doc_model": "cssk.cash.journal.line",
            "docs": rows,
            "company": company,
            "date_from": date_from,
            "date_to": date_to,
            "columns": DENNIK_COLUMNS,
            "lines": lines,
            "totals": totals,
            "opening_cash": opening_cash,
            "opening_bank": opening_bank,
            "closing_cash": cash,
            "closing_bank": bank,
        }

    @api.model
    def _sk_add_money(self, cells, row, gross, incoming):
        if row.payment_kind == "cash":
            cells["pokladnica_prijem" if incoming else "pokladnica_vydaj"] = gross
        elif row.payment_kind == "bank":
            cells["banka_prijem" if incoming else "banka_vydaj"] = gross

    @api.model
    def _sk_column_for(self, row, claimed):
        """Which breakdown column a row belongs in.

        A category the layout does not name still has to appear somewhere, or the
        book would not add up — so it falls into the catch-all column for its
        side, taxable or not.
        """
        if row.kind == "transit":
            return None
        code = row.category_id.code
        for key, _heading, codes in DENNIK_COLUMNS:
            if codes and code in codes:
                return key
        if row.kind == "income":
            return "p_ostatne" if row.taxable else "pn"
        return "v_ostatne" if row.taxable else "vn"

    @api.model
    def _sk_money_balance(self, company, date_from, kind):
        """Opening balance of the till or the bank, from the ledger.

        Read from the accounts rather than accumulated from denník rows, so that
        a book starting mid-year (``cssk_cash_journal_start``) still opens with
        the money the trader actually had.

        **The bank side includes the transit accounts**, and it has to. A trader
        who never imports statements leaves every receipt sitting on the
        *outstanding receipts* account, where Odoo's bank account shows nothing;
        once a statement does arrive, the outstanding and suspense legs net
        against each other and the bank account carries the money. Summing bank
        plus transit is therefore right in both states, and it is the same
        definition of "money" the engine itself uses.
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
