# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models

#: Tabuľka 1a of DPFO typ B, VI. oddiel: the balances a taxpayer keeping daňová
#: evidencia reports at the start and at the end of the period. Each slot is
#: ``(code, label, account code prefixes, sign)``.
#:
#: **Prefixes, not account types.** ``account_type`` cannot separate what the
#: form asks for — it has one bucket for fixed assets where the form wants
#: tangible apart from intangible, and one for current assets where the form
#: wants zásoby apart from everything else. The Slovak chart (opatrenie
#: MF/23054/2002-92) is built on účtové triedy that say exactly this: trieda 01
#: is nehmotný majetok, 02/03 hmotný, 07/08 their oprávky, trieda 1 zásoby,
#: 31 pohľadávky, 32 záväzky, 21/22 peniaze.
#:
#: The oprávky (07x, 08x) are included with the assets they belong to, so the
#: slot yields **zostatková cena** — which is what the form asks for — rather
#: than acquisition cost.
DPFO_1A_SLOTS = [
    ("r1", "Nehmotný majetok — zostatková cena", ["01", "07"], 1),
    ("r2", "Hmotný majetok — zostatková cena", ["02", "03", "08"], 1),
    ("r3", "Zásoby", ["1"], 1),
    ("r4", "Pohľadávky", ["31"], 1),
    ("r5", "Záväzky", ["32"], -1),
    ("r6", "Finančný majetok", ["21", "22", "25", "26"], 1),
]


class L10nSkCashDpfo(models.TransientModel):
    """The DPFO typ B figures a peňažný denník has to produce.

    Slovak law does not prescribe the form of daňová evidencia, so what the
    system must be able to output is defined by the **tax return** instead:

    * **tabuľka 1** — príjmy and výdavky, which come from the denník. Rows 1–9
      split them by § 6 source; a category says which row it feeds through
      ``tax_return_code``, and the total lands in **r.10**, which is what
      rows 39 and 40 of the return take.
    * **tabuľka 1a** — the balances at the start and the end of the period,
      which come from the ledger (``DPFO_1A_SLOTS``). This is the de facto
      "prehľad o majetku a záväzkoch" that daňová evidencia has no separate
      statutory form for.
    * **tabuľka 1b** — zásoby and pohľadávky only, for a taxpayer on paušálne
      výdavky (§ 6 ods. 10 ZDP), who still keeps those two records
      (§ 6 ods. 11 písm. a, d).

    A transient model rather than a report: the figures are read, checked
    against the denník and typed into the eForm. The XML of the return itself is
    a different module's business.
    """

    _name = "l10n.sk.cash.dpfo"
    _description = "DPFO typ B — figures from the peňažný denník"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company,
    )
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", readonly=True,
    )

    regime = fields.Selection(
        related="company_id.cssk_bookkeeping_regime", readonly=True,
    )
    line_ids = fields.One2many(
        "l10n.sk.cash.dpfo.line", "wizard_id", string="Rows", readonly=True,
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
        """Fill the rows, then show them on the same form."""
        self.ensure_one()
        figures = self.env["cssk.cash.figures"]
        flows = figures._cssk_flows(self.company_id, self.date_from, self.date_to)
        # "Na začiatku obdobia" means the state before the period's first day,
        # i.e. the closing balance of the day before it.
        slots = [(code, prefixes, sign)
                 for code, _label, prefixes, sign in DPFO_1A_SLOTS]
        opening = figures._cssk_balances(
            self.company_id, self.date_from - relativedelta(days=1), slots)
        closing = figures._cssk_balances(self.company_id, self.date_to, slots)

        self.line_ids.unlink()
        rows = []
        sequence = 0

        def row(table, code, label, value=None, opening_value=None,
                closing_value=None):
            nonlocal sequence
            sequence += 10
            rows.append({
                "wizard_id": self.id,
                "sequence": sequence,
                "table": table,
                "code": code,
                "label": label,
                "value": value or 0.0,
                "opening_value": opening_value or 0.0,
                "closing_value": closing_value or 0.0,
            })

        # -- tabuľka 1: the flows, by § 6 source then the total ---------
        by_code = flows["by_code"]
        for code, label in (
            ("t1r1", "r. 1 — príjmy z poľnohospodárskej výroby (§ 6 ods. 1 a)"),
            ("t1r2", "r. 2 — príjmy zo živnosti (§ 6 ods. 1 b)"),
            ("t1r3", "r. 3 — príjmy z podnikania podľa osobitných predpisov (§ 6 ods. 1 c)"),
            ("t1r5", "r. 5 — príjmy z použitia diela a umeleckého výkonu (§ 6 ods. 2 a)"),
            ("t1r6", "r. 6 — príjmy z inej samostatnej zárobkovej činnosti (§ 6 ods. 2 b)"),
            ("t1r11", "r. 11 — príjmy z prenájmu (§ 6 ods. 3)"),
        ):
            if code in by_code or code == "t1r2":
                row("t1", code, label, value=by_code.get(code, 0.0))
        row("t1", "t1r10_prijmy", "r. 10 stĺpec 1 — príjmy spolu",
            value=flows["income"])
        row("t1", "t1r10_vydavky", "r. 10 stĺpec 2 — výdavky spolu",
            value=flows["expense"])
        row("t1", "zaklad", "Základ dane (r. 10 stĺpec 1 − stĺpec 2)",
            value=flows["income"] - flows["expense"])

        # -- tabuľka 1a / 1b: the balances -----------------------------
        table = "t1b" if self.regime == "pausal" else "t1a"
        for code, label, _prefixes, _sign in DPFO_1A_SLOTS:
            if table == "t1b" and code not in ("r3", "r4"):
                continue
            row(table, code, label,
                opening_value=opening[code], closing_value=closing[code])

        # -- what the book itself says ---------------------------------
        row("kontrola", "dph_prijmy", "DPH v prijatých platbách",
            value=flows["vat_income"])
        row("kontrola", "dph_vydavky", "DPH v uhradených platbách",
            value=flows["vat_expense"])
        row("kontrola", "priebezne", "Priebežné položky (príjem − výdaj)",
            value=flows["transit_in"] - flows["transit_out"])

        self.env["l10n.sk.cash.dpfo.line"].create(rows)
        self.needs_review = flows["needs_review"]
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "name": _("DPFO typ B — údaje z peňažného denníka"),
        }


class L10nSkCashDpfoLine(models.TransientModel):
    _name = "l10n.sk.cash.dpfo.line"
    _description = "DPFO typ B figure"
    _order = "sequence, id"

    wizard_id = fields.Many2one(
        "l10n.sk.cash.dpfo", required=True, ondelete="cascade",
    )
    sequence = fields.Integer()
    table = fields.Selection([
        ("t1", "Tabuľka 1"),
        ("t1a", "Tabuľka 1a — daňová evidencia"),
        ("t1b", "Tabuľka 1b — paušálne výdavky"),
        ("kontrola", "Kontrola"),
    ])
    code = fields.Char()
    label = fields.Char()
    currency_id = fields.Many2one(
        "res.currency", related="wizard_id.currency_id", readonly=True,
    )
    value = fields.Monetary(currency_field="currency_id")
    opening_value = fields.Monetary(
        string="Na začiatku", currency_field="currency_id",
    )
    closing_value = fields.Monetary(
        string="Na konci", currency_field="currency_id",
    )
