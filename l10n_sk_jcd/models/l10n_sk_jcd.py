# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError

# Import-VAT tax by regime and rate, as shipped by the l10n_sk chart.
#
#   paid      -> vs_cust_*      daň zaplatená colnému orgánu; base carries NO DPH
#                               tag, tax deducts on r22 (19) / r22a (5) / r23 (23)
#   postponed -> vs_imp_post_*  § 84a ods. 3 samozdanenie; base on r11c/r11d/r11e,
#                               tax +r23a/r23b/r23c and -r12c/r12d/r12e
#
# Verified against l10n_sk/data/template/account.tax-sk.csv and the DPHv25
# poučenie (body 38 and 38a).
JCD_TAX_XMLIDS = {
    "paid": {"23": "vs_cust_23", "19": "vs_cust_19", "5": "vs_cust_5"},
    "postponed": {
        "23": "vs_imp_post_23",
        "19": "vs_imp_post_19",
        "5": "vs_imp_post_5",
    },
}


class L10nSkJcd(models.Model):
    _name = "l10n.sk.jcd"
    _description = "Colné vyhlásenie pri dovoze (JCD)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(default="New", readonly=True, copy=False, index="trigram")
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    date = fields.Date(
        string="Dátum prijatia colného vyhlásenia",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    mrn = fields.Char(
        string="MRN / evidenčné číslo",
        tracking=True,
        help="Evidenčné číslo colného vyhlásenia potvrdeného colným orgánom.",
    )
    customs_office_id = fields.Many2one(
        "res.partner",
        string="Colný úrad",
        required=True,
        tracking=True,
        help="Partner, voči ktorému vzniká záväzok za clo a daň pri dovoze.",
    )
    supplier_invoice_ids = fields.Many2many(
        "account.move",
        string="Dodávateľské faktúry",
        domain="[('move_type', '=', 'in_invoice'), ('company_id', '=', company_id)]",
        help="Faktúry zahraničného dodávateľa, ktorých tovar sa dováža.",
    )
    picking_ids = fields.Many2many(
        "stock.picking",
        string="Príjemky",
        help="Príjemky, na ktoré sa clo rozpustí do obstarávacej ceny.",
    )

    customs_value = fields.Monetary(
        string="Colná hodnota", tracking=True, help="Colná hodnota tovaru."
    )
    duty_amount = fields.Monetary(string="Clo", tracking=True)
    other_charges = fields.Monetary(
        string="Iné colné poplatky",
        tracking=True,
        help="Ďalšie poplatky vymerané colným orgánom, ktoré vstupujú do základu dane.",
    )
    vat_base = fields.Monetary(
        string="Základ dane pri dovoze",
        compute="_compute_vat_base",
        store=True,
        readonly=False,
        tracking=True,
        help="Predvolene colná hodnota + clo + iné poplatky (§ 24). Editovateľné — "
             "základ dane pri dovoze má aj ďalšie zložky, ktoré JCD nepozná.",
    )
    vat_rate = fields.Selection(
        [("23", "23 %"), ("19", "19 %"), ("5", "5 %")],
        string="Sadzba dane",
        default="23",
        required=True,
    )
    vat_regime = fields.Selection(
        [
            ("paid", "Daň zaplatená colnému orgánu (§ 49 ods. 2 písm. d)"),
            ("postponed", "Samozdanenie pri dovoze (§ 84a ods. 3)"),
        ],
        string="Režim dane",
        required=True,
        default=lambda self: self.env.company.l10n_sk_jcd_default_regime or "paid",
        tracking=True,
    )
    vat_amount = fields.Monetary(
        string="Daň pri dovoze", compute="_compute_vat_amount", store=True
    )

    customs_document_ok = fields.Boolean(
        string="Dovozný doklad potvrdený colným orgánom",
        compute="_compute_customs_document_ok",
        help="§ 49 ods. 2 písm. d): odpočítať daň možno, len ak platiteľ má "
             "dovozný doklad potvrdený colným orgánom. Splnené, keď je zadané MRN "
             "a doklad je priložený.",
    )
    state = fields.Selection(
        [("draft", "Návrh"), ("posted", "Zaúčtované"), ("cancelled", "Zrušené")],
        default="draft",
        required=True,
        tracking=True,
    )
    move_id = fields.Many2one(
        "account.move", string="Doklad dane a cla", readonly=True, copy=False
    )
    landed_cost_id = fields.Many2one(
        "stock.landed.cost", string="Rozpustenie cla", readonly=True, copy=False
    )

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends("customs_value", "duty_amount", "other_charges")
    def _compute_vat_base(self):
        for jcd in self:
            jcd.vat_base = (
                (jcd.customs_value or 0.0)
                + (jcd.duty_amount or 0.0)
                + (jcd.other_charges or 0.0)
            )

    @api.depends("vat_base", "vat_rate")
    def _compute_vat_amount(self):
        for jcd in self:
            rate = float(jcd.vat_rate or 0)
            jcd.vat_amount = jcd.currency_id.round(
                (jcd.vat_base or 0.0) * rate / 100.0
            )

    @api.depends("mrn")
    def _compute_customs_document_ok(self):
        # Not stored, and attachments are not a field on this model, so the
        # attachment side is evaluated on read rather than driven by @depends.
        for jcd in self:
            attachments = (
                self.env["ir.attachment"].search_count(
                    [("res_model", "=", self._name), ("res_id", "=", jcd.id)]
                )
                if jcd.id
                else 0
            )
            jcd.customs_document_ok = bool(jcd.mrn) and bool(attachments)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("l10n.sk.jcd") or "New"
                )
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_import_tax(self):
        """The l10n_sk tax for this declaration's regime and rate."""
        self.ensure_one()
        xmlid = JCD_TAX_XMLIDS[self.vat_regime][self.vat_rate]
        tax = self.env.ref(
            f"account.{self.company_id.id}_{xmlid}", raise_if_not_found=False
        )
        if not tax:
            raise UserError(
                _(
                    "The import VAT tax %(xmlid)s is missing for company "
                    "%(company)s. It ships with the Slovak chart of accounts — "
                    "check that the company uses l10n_sk.",
                    xmlid=xmlid,
                    company=self.company_id.display_name,
                )
            )
        return tax

    def _duty_expense_account(self):
        """The account the duty is billed to — and capitalised out of.

        These must be the SAME account. The bill debits the duty as an expense;
        validating the landed cost later credits it back and debits stock. If
        the two legs used different accounts the duty would sit in one expense
        account and be capitalised out of another, i.e. counted twice in the
        P&L. Odoo credits ``cost_line.account_id`` or, failing that, the
        product's expense account, so resolve it exactly that way here and pin
        it on the cost line in :meth:`_create_landed_cost`.
        """
        self.ensure_one()
        product = self.company_id.l10n_sk_jcd_duty_product_id
        account = product.product_tmpl_id.with_company(
            self.company_id
        ).get_product_accounts()["expense"]
        if not account:
            raise UserError(
                _(
                    "The customs-duty product %(product)s resolves to no expense "
                    "account (neither on the product nor on its category). The "
                    "duty must be billed to the same account the landed cost "
                    "capitalises it out of.",
                    product=product.display_name,
                )
            )
        return account

    def _check_postable(self):
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only a draft declaration can be posted."))
        if not self.vat_base:
            raise UserError(_("The taxable amount at import is zero."))
        if not self.customs_document_ok:
            # The one rule in this area that is routinely got wrong.
            raise UserError(
                _(
                    "Daň pri dovoze sa nedá odpočítať bez dovozného dokladu "
                    "potvrdeného colným orgánom (§ 49 ods. 2 písm. d)).\n\n"
                    "Zadajte MRN a priložte potvrdený dovozný doklad."
                )
            )
        company = self.company_id
        if not company.l10n_sk_jcd_clearing_account_id:
            raise UserError(
                _("Set the import clearing account in the accounting settings.")
            )
        if self.duty_amount and self.picking_ids:
            if not company.l10n_sk_jcd_duty_product_id:
                raise UserError(
                    _(
                        "Set the customs-duty product in the accounting settings "
                        "so the duty can be added to the stock value."
                    )
                )

    def _prepare_move_lines(self):
        """Base twice on the clearing account, so only VAT and duty are real.

        Nothing is bought from the customs office: the taxable amount at import
        is notional. Posting it +/- on a clearing account lets Odoo's tax engine
        compute the VAT from a base without that base becoming an expense or a
        payable. The `vs_cust_*` base repartition carries no DPH tag, so the
        notional base reaches no row of the return.
        """
        self.ensure_one()
        clearing = self.company_id.l10n_sk_jcd_clearing_account_id
        tax = self._get_import_tax()
        lines = [
            Command.create(
                {
                    "name": _("Základ dane pri dovoze — %s", self.name),
                    "account_id": clearing.id,
                    "price_unit": self.vat_base,
                    "quantity": 1.0,
                    "tax_ids": [Command.set(tax.ids)],
                }
            ),
            Command.create(
                {
                    "name": _("Vyrovnanie pomyselného základu — %s", self.name),
                    "account_id": clearing.id,
                    "price_unit": -self.vat_base,
                    "quantity": 1.0,
                    "tax_ids": [Command.set([])],
                }
            ),
        ]
        if self.duty_amount:
            duty_account = self._duty_expense_account()
            lines.append(
                Command.create(
                    {
                        "name": _("Clo — %s", self.name),
                        "account_id": duty_account.id,
                        "price_unit": self.duty_amount,
                        "quantity": 1.0,
                        "tax_ids": [Command.set([])],
                    }
                )
            )
        if self.other_charges:
            lines.append(
                Command.create(
                    {
                        "name": _("Iné colné poplatky — %s", self.name),
                        "account_id": (
                            self.company_id.expense_account_id.id
                            or self.company_id.l10n_sk_jcd_clearing_account_id.id
                        ),
                        "price_unit": self.other_charges,
                        "quantity": 1.0,
                        "tax_ids": [Command.set([])],
                    }
                )
            )
        return lines

    def _create_landed_cost(self):
        """Capitalise the duty into the stock value of the received goods."""
        self.ensure_one()
        if not (self.duty_amount and self.picking_ids):
            return self.env["stock.landed.cost"]
        landed = self.env["stock.landed.cost"].create(
            {
                "company_id": self.company_id.id,
                "date": self.date,
                "picking_ids": [Command.set(self.picking_ids.ids)],
                "account_journal_id": self.env["account.journal"]
                .search(
                    [("type", "=", "general"), ("company_id", "=", self.company_id.id)],
                    limit=1,
                )
                .id,
                "cost_lines": [
                    Command.create(
                        {
                            "product_id": self.company_id.l10n_sk_jcd_duty_product_id.id,
                            "name": _("Clo — %s", self.name),
                            "split_method": "by_current_cost_price",
                            "price_unit": self.duty_amount,
                            # Pinned so the capitalisation provably credits the
                            # very account the bill debited.
                            "account_id": self._duty_expense_account().id,
                        }
                    )
                ],
            }
        )
        landed.compute_landed_cost()
        return landed

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_post(self):
        for jcd in self:
            jcd._check_postable()
            journal = self.env["account.journal"].search(
                [("type", "=", "purchase"), ("company_id", "=", jcd.company_id.id)],
                limit=1,
            )
            if not journal:
                raise UserError(_("No purchase journal for this company."))
            move = self.env["account.move"].create(
                {
                    "move_type": "in_invoice",
                    "partner_id": jcd.customs_office_id.id,
                    "invoice_date": jcd.date,
                    "date": jcd.date,
                    "journal_id": journal.id,
                    "company_id": jcd.company_id.id,
                    "ref": jcd.mrn or jcd.name,
                    "invoice_line_ids": jcd._prepare_move_lines(),
                }
            )
            move.action_post()
            landed = jcd._create_landed_cost()
            jcd.write(
                {
                    "move_id": move.id,
                    "landed_cost_id": landed.id if landed else False,
                    "state": "posted",
                }
            )
            jcd.message_post(
                body=_(
                    "Zaúčtované: daň pri dovoze %(vat)s, clo %(duty)s.",
                    vat=jcd.vat_amount,
                    duty=jcd.duty_amount,
                )
            )
        return True

    def action_cancel(self):
        for jcd in self:
            if jcd.move_id and jcd.move_id.state == "posted":
                raise UserError(
                    _(
                        "Reverse the posted document %s first — a filed import "
                        "document is not silently unwound.",
                        jcd.move_id.display_name,
                    )
                )
            jcd.state = "cancelled"
        return True

    def action_draft(self):
        for jcd in self:
            if jcd.state != "cancelled":
                raise UserError(_("Only a cancelled declaration can be reset."))
            jcd.state = "draft"
        return True

    def action_view_move(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": self.move_id.id,
            "view_mode": "form",
        }
