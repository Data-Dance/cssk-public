# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class CsskCashFigures(models.AbstractModel):
    """What the personal income-tax return needs out of the denník.

    Both countries ask the same two questions and phrase them differently:

    * **the flows** — SK DPFO typ B, VI. oddiel, tabuľka 1 (príjmy and výdavky
      by § 6 source); CZ Příloha č. 1, ř. 101 and ř. 102;
    * **the balances at both ends of the year** — SK tabuľka 1a (zostatková cena
      HM and NM, zásoby, pohľadávky, záväzky, finančný majetok); CZ oddíl D (the
      same plus hotovost, bank, rezervy and mzdy).

    The flows come from the denník, the balances from the general ledger. Neither
    computation is country-specific; only the row labels and which slot goes on
    which line of which form are, so those live in the country modules and this
    is the arithmetic underneath.

    An abstract model rather than a mixin on the journal row, because nothing
    here is about one row: it is the year, read two ways.
    """

    _name = "cssk.cash.figures"
    _description = "Cash Journal Figures for the Income-Tax Return"

    # ------------------------------------------------------------------
    # flows, out of the denník
    # ------------------------------------------------------------------

    @api.model
    def _cssk_flows(self, company, date_from, date_to):
        """Totals of the book for a period.

        Returns a dict with ``income``, ``expense`` (only what reaches the tax
        base — which is what the return asks for), the same two ``*_all``
        including the non-taxable rows so the book can be reconciled to the
        bank, ``vat_income`` / ``vat_expense``, ``by_code`` keyed by the
        categories' ``tax_return_code``, ``by_category``, and ``needs_review``.

        **Non-cash rows are included in the taxable totals** and excluded from
        the money ones: depreciation belongs in the tax base and never touched
        the bank, which is exactly the distinction the two pairs of keys make.
        """
        rows = self.env["cssk.cash.journal.line"].search([
            ("company_id", "=", company.id),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
        ])
        figures = {
            "income": 0.0,
            "expense": 0.0,
            "income_all": 0.0,
            "expense_all": 0.0,
            "money_income": 0.0,
            "money_expense": 0.0,
            "transit_in": 0.0,
            "transit_out": 0.0,
            "vat_income": 0.0,
            "vat_expense": 0.0,
            "by_code": {},
            "by_category": {},
            "needs_review": 0,
        }
        for row in rows:
            if row.needs_review:
                figures["needs_review"] += 1
            if row.kind == "transit":
                key = "transit_in" if row.amount_signed >= 0 else "transit_out"
                figures[key] += row.amount
                continue
            side = "income" if row.kind == "income" else "expense"
            figures["%s_all" % side] += row.amount
            if row.taxable:
                figures[side] += row.amount
            if not row.non_cash:
                figures["money_%s" % side] += row.amount
                figures["vat_%s" % side] += row.amount_tax
            code = row.category_id.tax_return_code
            if code:
                figures["by_code"][code] = \
                    figures["by_code"].get(code, 0.0) + row.amount
            if row.category_id:
                figures["by_category"][row.category_id.id] = \
                    figures["by_category"].get(row.category_id.id, 0.0) + row.amount
        return figures

    # ------------------------------------------------------------------
    # balances, out of the ledger
    # ------------------------------------------------------------------

    @api.model
    def _cssk_balance(self, company, date, prefixes):
        """Net balance on ``date`` of every account whose code starts so.

        Account codes are the only workable key here. Odoo's ``account_type``
        cannot separate what the forms ask for — tangible from intangible fixed
        assets, or stock from other current assets — while the CZ and SK charts
        are both built on účtové triedy whose prefixes say exactly that. So the
        country module names prefixes and this sums them.

        Balances are signed as the ledger holds them: an asset is positive, a
        liability negative. The caller decides which way the form wants it,
        because a form asking for "záväzky" wants a positive number.
        """
        if not prefixes:
            return 0.0
        domain = [
            ("company_id", "=", company.id),
            ("parent_state", "=", "posted"),
            ("date", "<=", date),
            ("account_id.code", "=like", prefixes[0] + "%"),
        ]
        for prefix in prefixes[1:]:
            domain = ["|"] + domain + [("account_id.code", "=like", prefix + "%")]
        # ``code`` is company-dependent in 19.0, so the company has to be in the
        # environment for the prefix match to read that company's codes.
        lines = self.env["account.move.line"].with_company(company).search(domain)
        return sum(lines.mapped("balance"))

    @api.model
    def _cssk_balances(self, company, date, slots):
        """``{slot_code: balance}`` for ``[(slot_code, prefixes, sign), …]``.

        ``sign`` is ``1`` or ``-1`` and says how the form wants the number: the
        liability slots are asked for as positive amounts.
        """
        return {
            code: sign * self._cssk_balance(company, date, prefixes)
            for code, prefixes, sign in slots
        }
