# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class L10nSkInventarizacia(models.Model):
    _name = "l10n.sk.inventarizacia"
    _description = "Inventarizácia (§ 29 zákona 431/2002)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_as_of desc, id desc"

    name = fields.Char(default="New", readonly=True, copy=False, index="trigram")
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")

    # § 30 ods. 2 prescribes three distinct dates, not one.
    date_start = fields.Date(
        string="Deň začatia inventúry", required=True, tracking=True
    )
    date_as_of = fields.Date(
        string="Deň, ku ktorému bola inventúra vykonaná",
        required=True,
        tracking=True,
        help="Spravidla deň, ku ktorému sa zostavuje účtovná závierka (§ 29 ods. 1).",
    )
    date_end = fields.Date(
        string="Deň skončenia inventúry", required=True, tracking=True
    )

    supis_ids = fields.One2many(
        "l10n.sk.inventurny.supis", "inventarizacia_id", string="Inventúrne súpisy"
    )
    supis_count = fields.Integer(compute="_compute_totals")

    # § 30 ods. 3 — the inventarizačný zápis.
    comparison_note = fields.Text(
        string="Výsledky porovnania skutočného a účtovného stavu",
        help="§ 30 ods. 3 písm. b).",
    )
    valuation_note = fields.Text(
        string="Posúdenie reálnosti ocenenia",
        help="§ 30 ods. 3 písm. c) — v nadväznosti na § 26 (opravné položky, "
             "zníženie hodnoty).",
    )
    approved_by_id = fields.Many2one(
        "res.users",
        string="Zápis vyhotovil",
        help="Podpisový záznam osoby zodpovednej za vyhotovenie zápisu.",
    )

    book_amount = fields.Monetary(compute="_compute_totals", string="Účtovný stav")
    actual_amount = fields.Monetary(compute="_compute_totals", string="Skutočný stav")
    difference = fields.Monetary(compute="_compute_totals", string="Rozdiel")

    state = fields.Selection(
        [
            ("draft", "Návrh"),
            ("in_progress", "Prebieha"),
            ("done", "Ukončená"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )

    @api.depends("supis_ids.book_amount", "supis_ids.actual_amount")
    def _compute_totals(self):
        for inv in self:
            inv.supis_count = len(inv.supis_ids)
            inv.book_amount = sum(inv.supis_ids.mapped("book_amount"))
            inv.actual_amount = sum(inv.supis_ids.mapped("actual_amount"))
            inv.difference = inv.actual_amount - inv.book_amount

    @api.constrains("date_start", "date_as_of", "date_end")
    def _check_dates(self):
        for inv in self:
            if inv.date_end < inv.date_start:
                raise UserError(
                    self.env._("Deň skončenia nemôže predchádzať dňu začatia.")
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("l10n.sk.inventarizacia")
                    or "New"
                )
        return super().create(vals_list)

    def action_start(self):
        self.write({"state": "in_progress"})

    def action_done(self):
        for inv in self:
            if not inv.supis_ids:
                raise UserError(
                    self.env._("Inventarizácia bez inventúrneho súpisu nie je úplná.")
                )
            missing = inv.supis_ids.filtered(lambda s: not s.counted_by_id)
            if missing:
                # § 30 ods. 2 písm. i): the signature of the person responsible
                # for establishing the actual state is a prescribed particular.
                raise UserError(
                    self.env._(
                        "Chýba osoba zodpovedná za zistenie skutočného stavu na "
                        "súpisoch: %s",
                        ", ".join(missing.mapped("name")),
                    )
                )
        self.write({"state": "done"})

    def action_draft(self):
        self.write({"state": "draft"})


class L10nSkInventurnySupis(models.Model):
    _name = "l10n.sk.inventurny.supis"
    _description = "Inventúrny súpis (§ 30 ods. 2 zákona 431/2002)"
    _order = "inventarizacia_id, sequence, id"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    inventarizacia_id = fields.Many2one(
        "l10n.sk.inventarizacia", required=True, ondelete="cascade", index=True
    )
    company_id = fields.Many2one(related="inventarizacia_id.company_id", store=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    date_as_of = fields.Date(related="inventarizacia_id.date_as_of", store=True)

    inventory_type = fields.Selection(
        [
            ("fyzicka", "Fyzická inventúra"),
            ("dokladova", "Dokladová inventúra"),
        ],
        required=True,
        default="fyzicka",
        help="§ 29 ods. 2: fyzická pri majetku hmotnej povahy, dokladová pri "
             "záväzkoch a majetku, pri ktorom nemožno vykonať fyzickú inventúru.",
    )
    account_id = fields.Many2one(
        "account.account",
        string="Účet",
        domain="[('company_ids', 'in', company_id)]",
        help="Pri dokladovej inventúre — účet, ktorého zostatok sa overuje.",
    )
    location = fields.Char(
        string="Miesto uloženia majetku", help="§ 30 ods. 2 písm. f)."
    )
    responsible_person_id = fields.Many2one(
        "res.partner",
        string="Hmotne zodpovedná osoba",
        help="§ 30 ods. 2 písm. g) — meno a podpisový záznam.",
    )
    counted_by_id = fields.Many2one(
        "res.users",
        string="Skutočný stav zistil",
        help="§ 30 ods. 2 písm. i) — podpisový záznam osoby zodpovednej za "
             "zistenie skutočného stavu.",
    )
    note = fields.Text(string="Poznámky", help="§ 30 ods. 2 písm. j).")

    line_ids = fields.One2many(
        "l10n.sk.inventurny.supis.line", "supis_id", string="Položky"
    )

    book_amount = fields.Monetary(
        string="Účtovný stav",
        compute="_compute_amounts",
        store=True,
        readonly=False,
        help="Pri dokladovej inventúre sa načíta zo zostatku účtu ku dňu, ku "
             "ktorému bola inventúra vykonaná.",
    )
    actual_amount = fields.Monetary(
        string="Skutočný stav", compute="_compute_amounts", store=True
    )
    difference = fields.Monetary(compute="_compute_amounts", store=True)

    @api.depends("line_ids.amount", "account_id", "date_as_of", "inventory_type")
    def _compute_amounts(self):
        for supis in self:
            supis.actual_amount = sum(supis.line_ids.mapped("amount"))
            if supis.inventory_type == "dokladova" and supis.account_id:
                supis.book_amount = supis._account_book_balance()
            supis.difference = supis.actual_amount - (supis.book_amount or 0.0)

    def _account_book_balance(self):
        """Ledger balance of the account as at the deň ku ktorému."""
        self.ensure_one()
        if not (self.account_id and self.date_as_of):
            return 0.0
        self.env["account.move.line"].flush_model()
        groups = self.env["account.move.line"]._read_group(
            [
                ("account_id", "=", self.account_id.id),
                ("company_id", "=", self.company_id.id),
                ("date", "<=", self.date_as_of),
                ("parent_state", "=", "posted"),
            ],
            aggregates=["balance:sum"],
        )
        return groups[0][0] if groups else 0.0

    def action_refresh_book_amount(self):
        for supis in self:
            supis.book_amount = supis._account_book_balance()


class L10nSkInventurnySupisLine(models.Model):
    _name = "l10n.sk.inventurny.supis.line"
    _description = "Položka inventúrneho súpisu"
    _order = "supis_id, sequence, id"

    supis_id = fields.Many2one(
        "l10n.sk.inventurny.supis", required=True, ondelete="cascade", index=True
    )
    sequence = fields.Integer(default=10)
    currency_id = fields.Many2one(related="supis_id.currency_id")
    name = fields.Char(string="Popis", required=True)
    product_id = fields.Many2one("product.product", string="Produkt")
    # § 30 ods. 2 písm. e): "stav majetku s uvedením jednotiek množstva a ceny"
    # — quantity, unit AND price, all three.
    quantity = fields.Float(string="Množstvo", default=1.0)
    uom_name = fields.Char(string="Jednotka")
    unit_price = fields.Monetary(string="Cena za jednotku")
    amount = fields.Monetary(compute="_compute_amount", store=True, string="Hodnota")
    note = fields.Char(string="Poznámka")

    @api.depends("quantity", "unit_price")
    def _compute_amount(self):
        for line in self:
            line.amount = (line.quantity or 0.0) * (line.unit_price or 0.0)
