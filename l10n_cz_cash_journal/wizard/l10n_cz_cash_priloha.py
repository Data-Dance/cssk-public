# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models

#: Příloha č. 1, oddíl D — "Tabulka pro poplatníky, kteří vedou daňovou evidenci
#: podle § 7b zákona": the state of majetek and dluhy at the start and at the end
#: of the period. Each slot is ``(code, label, account code prefixes, sign)``.
#:
#: Prefixes follow the Czech účtová osnova (vyhláška č. 500/2002 Sb.): 02/03 are
#: dlouhodobý hmotný majetek with 08 its oprávky, so the pair yields zůstatková
#: cena; 01 with 07 is the intangible side, which the form does not ask for
#: separately and which therefore lands in "ostatní majetek"; trieda 1 is
#: zásoby, 211 pokladna, 221 bankovní účty, 31 pohledávky, 32 dluhy, 45 rezervy,
#: 331 závazky vůči zaměstnancům.
PRILOHA_D_SLOTS = [
    ("d1", "1. Hmotný majetek (zůstatková cena)", ["02", "03", "08"], 1),
    ("d2", "2. Peněžní prostředky v hotovosti", ["211"], 1),
    ("d3", "3. Peněžní prostředky na bankovních účtech", ["221"], 1),
    ("d4", "4. Zásoby", ["1"], 1),
    ("d5", "5. Pohledávky včetně poskytnutých úvěrů a zápůjček", ["31"], 1),
    ("d6", "6. Ostatní majetek", ["01", "07"], 1),
    ("d7", "7. Dluhy včetně přijatých úvěrů a zápůjček", ["32"], -1),
    ("d8", "8. Rezervy", ["45"], -1),
    ("d9", "9. Mzdy", ["331"], -1),
]


class L10nCzCashPriloha(models.TransientModel):
    """Příloha č. 1 figures, and the § 7b odst. 4 stock-take that goes with them.

    Czech law leaves the form of daňová evidence open, so what the system has to
    produce is set by the return and by one explicit obligation:

    * **ř. 101 / ř. 102** — příjmy and výdaje out of the deník. What § 5 and § 23
      add or take away belongs on ř. 105 / ř. 106 and in oddíl E; the non-cash
      categories (Z1, Z2) are already in the totals here, so a § 23 odst. 8
      adjustment posted as an entry is carried without being typed twice.
    * **oddíl D** — the balances at both ends of the period, from the ledger.
    * **§ 7b odst. 4** — "zjištění skutečného stavu zásob, hmotného majetku,
      pohledávek a dluhů … o tomto zjištění provede zápis". Slovakia has no such
      duty for daňová evidencia; the Czech one is a written record, so the
      closing figures are offered as the body of that zápis.
    """

    _name = "l10n.cz.cash.priloha"
    _description = "Příloha č. 1 — údaje z peněžního deníku"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company,
    )
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", readonly=True,
    )
    line_ids = fields.One2many(
        "l10n.cz.cash.priloha.line", "wizard_id", string="Řádky", readonly=True,
    )
    needs_review = fields.Integer(readonly=True)

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        today = fields.Date.context_today(self)
        values.setdefault("date_from", today.replace(month=1, day=1))
        values.setdefault("date_to", today.replace(month=12, day=31))
        return values

    def action_compute(self):
        self.ensure_one()
        figures = self.env["cssk.cash.figures"]
        flows = figures._cssk_flows(self.company_id, self.date_from, self.date_to)
        slots = [(code, prefixes, sign)
                 for code, _label, prefixes, sign in PRILOHA_D_SLOTS]
        opening = figures._cssk_balances(
            self.company_id, self.date_from - relativedelta(days=1), slots)
        closing = figures._cssk_balances(self.company_id, self.date_to, slots)

        self.line_ids.unlink()
        rows = []
        sequence = 0

        def row(section, code, label, value=None, opening_value=None,
                closing_value=None):
            nonlocal sequence
            sequence += 10
            rows.append({
                "wizard_id": self.id,
                "sequence": sequence,
                "section": section,
                "code": code,
                "label": label,
                "value": value or 0.0,
                "opening_value": opening_value or 0.0,
                "closing_value": closing_value or 0.0,
            })

        by_code = flows["by_code"]
        row("p1", "r101", "ř. 101 — Příjmy podle § 7",
            value=by_code.get("r101", flows["income"]))
        row("p1", "r102", "ř. 102 — Výdaje podle § 7",
            value=by_code.get("r102", flows["expense"]))
        row("p1", "r104", "ř. 104 — Rozdíl (ř. 101 − ř. 102)",
            value=flows["income"] - flows["expense"])

        for code, label, _prefixes, _sign in PRILOHA_D_SLOTS:
            row("d", code, label,
                opening_value=opening[code], closing_value=closing[code])

        row("kontrola", "dph_prijmy", "DPH v přijatých platbách",
            value=flows["vat_income"])
        row("kontrola", "dph_vydaje", "DPH v uhrazených platbách",
            value=flows["vat_expense"])
        row("kontrola", "prubezne", "Průběžné položky (příjem − výdej)",
            value=flows["transit_in"] - flows["transit_out"])

        self.env["l10n.cz.cash.priloha.line"].create(rows)
        self.needs_review = flows["needs_review"]
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "name": _("Příloha č. 1 — údaje z peněžního deníku"),
        }

    def action_print_zapis(self):
        """The § 7b odst. 4 zápis, with the closing figures as its body."""
        self.ensure_one()
        if not self.line_ids:
            self.action_compute()
        return self.env.ref(
            "l10n_cz_cash_journal.action_report_zapis_o_zjisteni"
        ).report_action(self)


class L10nCzCashPrilohaLine(models.TransientModel):
    _name = "l10n.cz.cash.priloha.line"
    _description = "Příloha č. 1 figure"
    _order = "sequence, id"

    wizard_id = fields.Many2one(
        "l10n.cz.cash.priloha", required=True, ondelete="cascade",
    )
    sequence = fields.Integer()
    section = fields.Selection([
        ("p1", "Příloha č. 1"),
        ("d", "Oddíl D — majetek a dluhy"),
        ("kontrola", "Kontrola"),
    ])
    code = fields.Char()
    label = fields.Char()
    currency_id = fields.Many2one(
        "res.currency", related="wizard_id.currency_id", readonly=True,
    )
    value = fields.Monetary(currency_field="currency_id")
    opening_value = fields.Monetary(
        string="Na začátku", currency_field="currency_id",
    )
    closing_value = fields.Monetary(
        string="Na konci", currency_field="currency_id",
    )
