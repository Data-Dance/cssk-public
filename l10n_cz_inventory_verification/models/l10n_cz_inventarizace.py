# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class L10nCzInventarizace(models.Model):
    _name = "l10n.cz.inventarizace"
    _description = "Inventarizace (§ 29 zákona č. 563/1991 Sb.)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_as_of desc, id desc"

    name = fields.Char(default="New", readonly=True, copy=False, index="trigram")
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")

    # § 29 odst. 1: periodická (to the moment the účetní závěrka is drawn up)
    # or, for the assets named in § 29 odst. 2, průběžná.
    inventarizace_type = fields.Selection(
        [
            ("periodicka", "Periodická inventarizace"),
            ("prubezna", "Průběžná inventarizace"),
        ],
        string="Druh inventarizace",
        required=True,
        default="periodicka",
        tracking=True,
        help="§ 29 odst. 1: periodická inventarizace se provádí k okamžiku, ke "
             "kterému se sestavuje účetní závěrka. Průběžnou inventarizaci "
             "lze podle § 29 odst. 2 provádět pouze u zásob účtovaných podle "
             "druhů, míst uložení nebo hmotně odpovědných osob a u "
             "dlouhodobého hmotného movitého majetku v soustavném pohybu.",
    )
    # § 30 odst. 7 písm. f). The other moments of that paragraph (rozhodný
    # den, zahájení, ukončení) belong to each inventura, so they sit on the
    # soupis: § 30 odst. 2 lets one inventarizace consist of several inventury.
    date_as_of = fields.Date(
        string="Okamžik, ke kterému se sestavuje účetní závěrka",
        required=True,
        tracking=True,
        help="§ 30 odst. 7 písm. f) — rozvahový den (§ 19 odst. 1); "
             "the balance-sheet date.",
    )
    date_start = fields.Datetime(
        string="Zahájení první inventury", compute="_compute_span", store=True
    )
    date_end = fields.Datetime(
        string="Ukončení poslední inventury", compute="_compute_span", store=True
    )
    timing_warning = fields.Char(
        string="Timing warning", compute="_compute_timing_warning"
    )

    soupis_ids = fields.One2many(
        "l10n.cz.inventurni.soupis", "inventarizace_id", string="Inventurní soupisy"
    )
    soupis_count = fields.Integer(
        string="Počet inventurních soupisů", compute="_compute_totals"
    )

    # The closing record. Zákon č. 563/1991 Sb. prescribes no such document
    # for businesses: it is an internal record that evidences the exercise
    # (§ 29 odst. 3) and carries the comparison § 30 odst. 2 asks for.
    comparison_note = fields.Text(
        string="Výsledky porovnání skutečného stavu se stavem v účetnictví",
        help="§ 30 odst. 2; inventarizační rozdíly (manko, schodek, přebytek) "
             "podle § 30 odst. 10 a jejich vyúčtování podle § 30 odst. 11.",
    )
    valuation_note = fields.Text(
        string="Posouzení ocenění majetku a závazků",
        help="§ 29 odst. 1 — zda nejsou dány důvody pro účtování o položkách "
             "podle § 25 odst. 3 (předvídatelná rizika, možné ztráty, snížení "
             "hodnoty); u podnikatelů opravné položky a rezervy podle § 55 "
             "odst. 1 a § 57 odst. 5 vyhlášky č. 500/2002 Sb.",
    )
    approved_by_id = fields.Many2one(
        "res.users",
        string="Osoba odpovědná za provedení inventarizace",
        help="Not a statutory particular: the person who answers for the "
             "exercise as a whole and signs the internal closing record.",
    )

    book_amount = fields.Monetary(
        compute="_compute_totals", string="Stav v účetnictví"
    )
    actual_amount = fields.Monetary(compute="_compute_totals", string="Skutečný stav")
    difference = fields.Monetary(compute="_compute_totals", string="Difference")

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_progress", "In progress"),
            ("done", "Done"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )

    @api.depends("soupis_ids.book_amount", "soupis_ids.actual_amount")
    def _compute_totals(self):
        for inv in self:
            inv.soupis_count = len(inv.soupis_ids)
            inv.book_amount = sum(inv.soupis_ids.mapped("book_amount"))
            inv.actual_amount = sum(inv.soupis_ids.mapped("actual_amount"))
            inv.difference = inv.actual_amount - inv.book_amount

    @api.depends("soupis_ids.datetime_start", "soupis_ids.datetime_end")
    def _compute_span(self):
        for inv in self:
            starts = [d for d in inv.soupis_ids.mapped("datetime_start") if d]
            ends = [d for d in inv.soupis_ids.mapped("datetime_end") if d]
            inv.date_start = min(starts) if starts else False
            inv.date_end = max(ends) if ends else False

    @api.depends("inventarizace_type", "date_as_of", "date_start", "date_end")
    def _compute_timing_warning(self):
        """§ 30 odst. 6: a periodická inventarizace may start its inventura
        four months before the rozvahový den at the earliest and ends it two
        months after at the latest.

        A warning, not a constraint: an inventura held outside the window
        still happened, and refusing to record its true moments would only
        invite recording false ones.
        """
        for inv in self:
            messages = []
            if inv.inventarizace_type == "periodicka" and inv.date_as_of:
                start = inv.date_start and fields.Datetime.context_timestamp(
                    inv, inv.date_start).date()
                end = inv.date_end and fields.Datetime.context_timestamp(
                    inv, inv.date_end).date()
                if start and start < inv.date_as_of - relativedelta(months=4):
                    messages.append(inv.env._(
                        "An inventura starts more than four months before "
                        "the rozvahový den (§ 30 odst. 6 písm. a))."
                    ))
                if end and end > inv.date_as_of + relativedelta(months=2):
                    messages.append(inv.env._(
                        "An inventura ends more than two months after the "
                        "rozvahový den (§ 30 odst. 6 písm. b))."
                    ))
            inv.timing_warning = " ".join(messages) or False

    @api.constrains("date_as_of", "inventarizace_type")
    def _check_rozhodny_den(self):
        self.soupis_ids._check_rozhodny_den()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("l10n.cz.inventarizace")
                    or "New"
                )
        return super().create(vals_list)

    def action_start(self):
        self.write({"state": "in_progress"})

    def action_done(self):
        for inv in self:
            if not inv.soupis_ids:
                raise UserError(
                    self.env._(
                        "An inventarizace without an inventurní soupis is "
                        "not complete."
                    )
                )
            problems = []
            for soupis in inv.soupis_ids:
                missing = soupis._missing_particulars()
                if missing:
                    problems.append("%s: %s" % (soupis.name, ", ".join(missing)))
            if problems:
                # § 30 odst. 7: the soupis "musí obsahovat" these.
                raise UserError(
                    self.env._(
                        "Particulars prescribed by § 30 odst. 7 are missing:\n%s",
                        "\n".join(problems),
                    )
                )
        self.write({"state": "done"})

    def action_draft(self):
        self.write({"state": "draft"})

    def action_refresh_book_amounts(self):
        """Re-read the ledger for every dokladová inventura of the exercise.

        The stav v účetnictví follows the account and the comparison day on
        its own, but not entries posted afterwards — this picks those up.
        """
        self.soupis_ids.action_refresh_book_amount()

    def action_print_soupisy(self):
        """Print every inventurní soupis of the exercise in one PDF.

        A soupis is edited inside the inventarizace, never on a screen of its
        own, so the report bound to the soupis model has no Print menu to
        appear in.
        """
        self.ensure_one()
        if not self.soupis_ids:
            raise UserError(
                self.env._("The inventarizace has no inventurní soupis yet.")
            )
        return self.env.ref(
            "l10n_cz_inventory_verification.action_report_inventurni_soupis"
        ).report_action(self.soupis_ids)


class L10nCzInventurniSoupis(models.Model):
    _name = "l10n.cz.inventurni.soupis"
    _description = "Inventurní soupis (§ 30 odst. 7 zákona č. 563/1991 Sb.)"
    _order = "inventarizace_id, sequence, id"

    # The particulars § 30 odst. 7 says a soupis "musí obsahovat" and that a
    # person has to supply; closing the inventarizace is refused without them.
    _PRESCRIBED = (
        "counted_by_id",
        "inventory_responsible_id",
        "method",
        "datetime_start",
        "datetime_end",
    )

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    inventarizace_id = fields.Many2one(
        "l10n.cz.inventarizace", required=True, ondelete="cascade", index=True
    )
    company_id = fields.Many2one(related="inventarizace_id.company_id", store=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    date_as_of = fields.Date(related="inventarizace_id.date_as_of", store=True)

    inventory_type = fields.Selection(
        [
            ("fyzicka", "Fyzická inventura"),
            ("dokladova", "Dokladová inventura"),
        ],
        string="Druh inventury",
        required=True,
        default="fyzicka",
        help="§ 30 odst. 1: fyzická inventura u majetku, u kterého lze "
             "vizuálně zjistit jeho existenci; dokladová inventura u závazků "
             "a majetku, u kterého to nelze, včetně jiných aktiv, jiných "
             "pasiv a skutečností účtovaných v knize podrozvahových účtů.",
    )
    method = fields.Char(
        string="Způsob zjišťování skutečných stavů",
        help="§ 30 odst. 7 písm. c) — např. počítáním, měřením, vážením "
             "(§ 30 odst. 3), odsouhlasením zůstatků, podle smluv a výpisů.",
    )
    rozhodny_den = fields.Date(
        string="Rozhodný den",
        help="§ 30 odst. 7 písm. g), pokud jej účetní jednotka stanovila. "
             "Podle § 30 odst. 4 předchází rozvahovému dni; skutečný stav se "
             "pak dokončí podle přírůstků a úbytků mezi oběma dny.",
    )
    datetime_start = fields.Datetime(
        string="Okamžik zahájení inventury", help="§ 30 odst. 7 písm. h)."
    )
    datetime_end = fields.Datetime(
        string="Okamžik ukončení inventury", help="§ 30 odst. 7 písm. h)."
    )
    comparison_date = fields.Date(
        string="Ocenění ke dni",
        compute="_compute_comparison_date",
        store=True,
        help="§ 30 odst. 7 písm. d): při periodické inventarizaci rozvahový "
             "den; písm. e): při průběžné inventarizaci den ukončení "
             "inventury.",
    )
    account_id = fields.Many2one(
        "account.account",
        string="Account",
        domain="[('company_ids', 'in', company_id)]",
        help="For a dokladová inventura: the account whose balance is verified.",
    )
    location = fields.Char(
        string="Místo uložení majetku",
        help="Not prescribed by § 30 odst. 7; it helps to identify the "
             "assets unambiguously, as písm. a) requires.",
    )
    responsible_person_id = fields.Many2one(
        "res.partner",
        string="Hmotně odpovědná osoba",
        help="Not prescribed by § 30 odst. 7. Printed with a signature line "
             "when filled in.",
    )
    counted_by_id = fields.Many2one(
        "res.users",
        string="Osoba odpovědná za zjištění skutečností",
        help="§ 30 odst. 7 písm. b) — podpisový záznam osoby odpovědné za "
             "zjištění skutečností.",
    )
    inventory_responsible_id = fields.Many2one(
        "res.users",
        string="Osoba odpovědná za provedení inventury",
        help="§ 30 odst. 7 písm. b) — podpisový záznam osoby odpovědné za "
             "provedení inventury.",
    )
    note = fields.Text(string="Notes")

    line_ids = fields.One2many(
        "l10n.cz.inventurni.soupis.line", "soupis_id", string="Items"
    )

    book_amount = fields.Monetary(
        string="Stav v účetnictví",
        compute="_compute_book_amount",
        store=True,
        readonly=False,
        help="For a dokladová inventura with an account: the balance of the "
             "account as at the day of valuation.",
    )
    actual_amount = fields.Monetary(
        string="Skutečný stav", compute="_compute_actual_amount", store=True
    )
    difference = fields.Monetary(
        string="Difference", compute="_compute_difference", store=True
    )

    @api.depends(
        "inventarizace_id.inventarizace_type",
        "inventarizace_id.date_as_of",
        "datetime_end",
    )
    def _compute_comparison_date(self):
        for soupis in self:
            inv = soupis.inventarizace_id
            if inv.inventarizace_type == "prubezna" and soupis.datetime_end:
                soupis.comparison_date = fields.Datetime.context_timestamp(
                    soupis, soupis.datetime_end
                ).date()
            else:
                soupis.comparison_date = inv.date_as_of

    # Three compute methods, not one. Fields sharing a compute method are
    # protected together while one of them is being written, so a typed stav
    # v účetnictví saved in the same request as the items would leave the
    # skutečný stav and the difference at zero.
    @api.depends("line_ids.amount")
    def _compute_actual_amount(self):
        for soupis in self:
            soupis.actual_amount = sum(soupis.line_ids.mapped("amount"))

    @api.depends("account_id", "comparison_date", "inventory_type")
    def _compute_book_amount(self):
        for soupis in self:
            if soupis.inventory_type == "dokladova" and soupis.account_id:
                soupis.book_amount = soupis._account_book_balance()
            else:
                # typed in: keep what is there
                soupis.book_amount = soupis.book_amount

    @api.depends("actual_amount", "book_amount")
    def _compute_difference(self):
        for soupis in self:
            soupis.difference = soupis.actual_amount - (soupis.book_amount or 0.0)

    @api.constrains("datetime_start", "datetime_end")
    def _check_moments(self):
        for soupis in self:
            if (
                soupis.datetime_start
                and soupis.datetime_end
                and soupis.datetime_end < soupis.datetime_start
            ):
                raise ValidationError(
                    self.env._(
                        "%s: the inventura cannot end before it starts.",
                        soupis.name,
                    )
                )

    @api.constrains("rozhodny_den")
    def _check_rozhodny_den(self):
        for soupis in self:
            inv = soupis.inventarizace_id
            if (
                soupis.rozhodny_den
                and inv.inventarizace_type == "periodicka"
                and inv.date_as_of
                and soupis.rozhodny_den >= inv.date_as_of
            ):
                # § 30 odst. 4: "který předchází rozvahovému dni"
                raise ValidationError(
                    self.env._(
                        "%s: the rozhodný den must precede the rozvahový den "
                        "(§ 30 odst. 4).",
                        soupis.name,
                    )
                )

    def _missing_particulars(self):
        """Labels of the prescribed particulars this soupis still lacks."""
        self.ensure_one()
        labels = self.fields_get(self._PRESCRIBED, ["string"])
        return [labels[f]["string"] for f in self._PRESCRIBED if not self[f]]

    def _account_book_balance(self):
        """Ledger balance of the account as at the day of valuation."""
        self.ensure_one()
        if not (self.account_id and self.comparison_date):
            return 0.0
        self.env["account.move.line"].flush_model()
        groups = self.env["account.move.line"]._read_group(
            [
                ("account_id", "=", self.account_id.id),
                ("company_id", "=", self.company_id.id),
                ("date", "<=", self.comparison_date),
                ("parent_state", "=", "posted"),
            ],
            aggregates=["balance:sum"],
        )
        return groups[0][0] if groups else 0.0

    def action_refresh_book_amount(self):
        """Re-read the ledger balance of a dokladová inventura.

        Only a soupis with an account has a balance to read: a fyzická
        inventura's stav v účetnictví is typed in, and must not be
        overwritten with zero.
        """
        for soupis in self:
            if soupis.inventory_type == "dokladova" and soupis.account_id:
                soupis.book_amount = soupis._account_book_balance()


class L10nCzInventurniSoupisLine(models.Model):
    _name = "l10n.cz.inventurni.soupis.line"
    _description = "Položka inventurního soupisu"
    _order = "soupis_id, sequence, id"

    soupis_id = fields.Many2one(
        "l10n.cz.inventurni.soupis", required=True, ondelete="cascade", index=True
    )
    sequence = fields.Integer(default=10)
    currency_id = fields.Many2one(related="soupis_id.currency_id")
    # § 30 odst. 7 písm. a): described so that the asset or liability can be
    # identified unambiguously.
    name = fields.Char(string="Description", required=True)
    product_id = fields.Many2one("product.product", string="Product")
    quantity = fields.Float(string="Quantity", default=1.0)
    uom_name = fields.Char(string="Unit")
    unit_price = fields.Monetary(string="Unit price")
    # § 30 odst. 7 písm. d) and e): the ocenění.
    amount = fields.Monetary(compute="_compute_amount", store=True, string="Ocenění")
    note = fields.Char(string="Note")

    @api.depends("quantity", "unit_price")
    def _compute_amount(self):
        for line in self:
            line.amount = (line.quantity or 0.0) * (line.unit_price or 0.0)
