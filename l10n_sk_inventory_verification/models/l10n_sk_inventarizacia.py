# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class L10nSkInventarizacia(models.Model):
    _name = "l10n.sk.inventarizacia"
    _description = "Inventarizácia (§ 29 zákona 431/2002)"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "l10n_cssk.inventory.difference.mixin",
    ]
    _order = "date_as_of desc, id desc"
    _cssk_sheets_field = "supis_ids"

    name = fields.Char(default="New", readonly=True, copy=False, index="trigram")
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")

    # § 30 ods. 5 to 7: the inventarizačné rozdiely and their vyúčtovanie.
    difference_line_ids = fields.One2many(
        "l10n.sk.inventarizacny.rozdiel",
        "inventory_id",
        string="Vyúčtovanie inventarizačných rozdielov",
    )

    # § 30 ods. 2 písm. b) prescribes three distinct dates, not one.
    date_start = fields.Date(
        string="Deň začatia inventúry", required=True, tracking=True
    )
    date_as_of = fields.Date(
        string="Deň, ku ktorému bola inventúra vykonaná",
        required=True,
        tracking=True,
        help="Spravidla deň, ku ktorému sa zostavuje účtovná závierka (§ 29 ods. 2).",
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
        string="Zodpovedný za vykonanie inventarizácie",
        help="§ 30 ods. 3 písm. d) — meno, priezvisko a podpisový záznam osoby "
             "zodpovednej za vykonanie inventarizácie v účtovnej jednotke.",
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
        # Reopening takes the booked differences back: the súpisy are about
        # to change, and an entry built from the old ones would stay behind.
        self._cssk_cancel_difference_entries()
        self.write({"state": "draft"})

    def action_refresh_book_amounts(self):
        """Re-read the ledger for every dokladová inventúra of the exercise.

        The účtovný stav follows the account and the deň ku ktorému on its
        own, but not entries posted afterwards — this picks those up.
        """
        self.supis_ids.action_refresh_book_amount()

    def action_print_supisy(self):
        """Print every inventúrny súpis of the exercise in one PDF.

        A súpis is edited inside the inventarizácia, never on a screen of its
        own, so the report bound to the súpis model had no Print menu to
        appear in.
        """
        self.ensure_one()
        if not self.supis_ids:
            raise UserError(
                self.env._("Inventarizácia zatiaľ nemá žiadny inventúrny súpis.")
            )
        return self.env.ref(
            "l10n_sk_inventory_verification.action_report_inventurny_supis"
        ).report_action(self.supis_ids)


class L10nSkInventurnySupis(models.Model):
    _name = "l10n.sk.inventurny.supis"
    _description = "Inventúrny súpis (§ 30 ods. 2 zákona 431/2002)"
    _inherit = ["l10n_cssk.inventory.sheet.mixin"]
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
        help="§ 30 ods. 1: fyzická pri majetku hmotnej a nehmotnej povahy, "
             "dokladová pri záväzkoch, rozdiele majetku a záväzkov a majetku, "
             "pri ktorom nemožno vykonať fyzickú inventúru.",
    )
    account_id = fields.Many2one(
        "account.account",
        string="Účet",
        domain="[('company_ids', 'in', company_id)]",
        help="Pri dokladovej inventúre — účet, ktorého zostatok sa overuje. "
             "Pri fyzickej inventúre účet, na ktorom sa majetok vedie; "
             "navrhne sa z neho zaúčtovanie inventarizačného rozdielu.",
    )
    difference_line_ids = fields.One2many(
        "l10n.sk.inventarizacny.rozdiel",
        "sheet_id",
        string="Vyúčtovanie rozdielu",
    )
    location = fields.Char(
        string="Miesto uloženia majetku", help="§ 30 ods. 2 písm. d)."
    )
    responsible_person_id = fields.Many2one(
        "res.partner",
        string="Hmotne zodpovedná osoba",
        help="§ 30 ods. 2 písm. e) — meno, priezvisko a podpisový záznam.",
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
        compute="_compute_book_amount",
        store=True,
        readonly=False,
        help="Pri dokladovej inventúre sa načíta zo zostatku účtu ku dňu, ku "
             "ktorému bola inventúra vykonaná.",
    )
    actual_amount = fields.Monetary(
        string="Skutočný stav", compute="_compute_actual_amount", store=True
    )
    difference = fields.Monetary(compute="_compute_difference", store=True)

    # Three methods, not one. Odoo protects every field of a compute method
    # while one of them is being written, so with one method a typed účtovný
    # stav saved in the same request as the items left the skutočný stav and
    # the rozdiel at zero.
    @api.depends("line_ids.amount")
    def _compute_actual_amount(self):
        for supis in self:
            supis.actual_amount = sum(supis.line_ids.mapped("amount"))

    @api.depends("account_id", "date_as_of", "inventory_type")
    def _compute_book_amount(self):
        for supis in self:
            if supis.inventory_type == "dokladova" and supis.account_id:
                supis.book_amount = supis._account_book_balance()
            else:
                # typed in: keep what is there
                supis.book_amount = supis.book_amount

    @api.depends("actual_amount", "book_amount")
    def _compute_difference(self):
        for supis in self:
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
        """Re-read the ledger balance of a dokladová inventúra.

        Only a súpis with an account has a balance to read: a fyzická
        inventúra's účtovný stav is typed in, and must not be overwritten
        with zero.
        """
        for supis in self:
            if supis.inventory_type == "dokladova" and supis.account_id:
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
    # § 30 ods. 2 písm. c): "stav majetku s uvedením jednotiek množstva a ceny"
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


class L10nSkInventarizacnyRozdiel(models.Model):
    _name = "l10n.sk.inventarizacny.rozdiel"
    _description = "Vyúčtovanie inventarizačného rozdielu (§ 30 ods. 5 až 7)"
    _inherit = ["l10n_cssk.inventory.difference.line"]

    inventory_id = fields.Many2one(
        "l10n.sk.inventarizacia",
        string="Inventarizácia",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sheet_id = fields.Many2one(
        "l10n.sk.inventurny.supis",
        string="Inventúrny súpis",
        required=True,
        ondelete="cascade",
        index=True,
        domain="[('inventarizacia_id', '=', inventory_id)]",
    )
    company_id = fields.Many2one(related="inventory_id.company_id", store=True)
    currency_id = fields.Many2one(related="company_id.currency_id")

    @api.constrains("inventory_id", "sheet_id")
    def _check_sheet(self):
        self._cssk_check_sheet("inventarizacia_id")

    # Opatrenie MF SR č. 23054/2002-92 (postupy účtovania v podvojnom
    # účtovníctve). Proposals only: the user may overwrite both accounts,
    # and where the postupy give no single answer, none is proposed.
    def _cssk_claim_account_code(self):
        # § 55 ods. 9 písm. a): "pohľadávka voči zodpovednej osobe na
        # náhradu škody alebo manka, súvzťažne s účtom 648"
        return "378"

    def _cssk_counterpart_code(self, kind, account):
        code = account.code or ""
        if kind == "claim":
            return "648"  # § 55 ods. 9 písm. a), § 78 ods. 4
        if not code:
            return False
        group = code[:2]
        if group == "21":
            # § 11 ods. 1 písm. b): the schodok of cash and ceniny is no
            # expense, it "sa účtuje ako pohľadávka voči hmotne zodpovednej
            # osobe" (335, § 51 ods. 3). The prebytok goes to "príslušné
            # účty výnosov"; 668 is the residual financial one (§ 80 ods. 8).
            return {"shortage": "335", "surplus": "668"}.get(kind, False)
        if group in ("11", "13"):
            # § 43 ods. 2 písm. d), § 68 ods. 8
            return {
                "shortage": "549",
                "natural_loss": "501" if group == "11" else "504",
                "surplus": "648",
            }[kind]
        if group == "12":
            # § 43 ods. 3 písm. b): 121 → 611 … 124 → 614
            return "549" if kind == "shortage" else "61" + code[2:3]
        if group in ("01", "02"):
            # § 21 ods. 2: newly found, at reálna hodnota, against 384. A
            # manko takes the zostatková cena through the oprávky (§ 36
            # ods. 4 písm. e)), which is the asset register's entry, not one
            # line here.
            return "384" if kind == "surplus" else False
        if group == "03":
            # § 11 ods. 4, § 21 ods. 2, § 68 ods. 8: not depreciated
            return {"shortage": "549", "surplus": "648"}.get(kind, False)
        return False
