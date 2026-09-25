# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class L10nSkFuelSplit(models.TransientModel):
    _name = "l10n.sk.fuel.split"
    _description = "Split fuel between its tax-deductible and non-deductible shares"

    move_id = fields.Many2one("account.move", required=True, readonly=True)
    company_id = fields.Many2one(related="move_id.company_id")
    currency_id = fields.Many2one(related="move_id.currency_id")
    line_ids = fields.Many2many(
        "account.move.line",
        string="Fuel lines",
        required=True,
        help="Bill lines representing a purchase of fuel.",
    )
    income_ratio = fields.Float(
        string="Tax-expense share (%)",
        required=True,
        default=lambda self: self.env.company.l10n_sk_fuel_income_ratio or 80.0,
        help="§ 19 ods. 2 písm. l) bod 3 — paušál do výšky 80 %. Týka sa dane z "
             "príjmov; odpočet DPH rieši samostatne § 85n (50 %) cez sadzbu dane "
             "na riadku faktúry.",
    )
    nondeductible_account_id = fields.Many2one(
        "account.account",
        string="Non-deductible account",
        required=True,
        default=lambda self: (
            self.env.company.l10n_sk_vehicle_nondeductible_account_id
        ),
    )

    @api.constrains("income_ratio")
    def _check_income_ratio(self):
        for wizard in self:
            if not 0.0 < wizard.income_ratio <= 100.0:
                raise UserError(
                    _("The tax-expense share must be above 0 and at most 100 %.")
                )

    def action_split(self):
        """Reclassify the non-tax share of the fuel cost, totals unchanged.

        This is the **income-tax** half of the treatment only. The VAT half is not
        done here and must not be: § 85n restricts the *deduction*, which has to
        happen in the tax repartition (``vs_auto_*``) so that only the deductible
        half carries the DPH tag. Splitting VAT with journal lines here would
        report the full amount on the return.

        So the base is merely moved between two expense accounts — the bill total,
        the VAT and the payable are all untouched.
        """
        self.ensure_one()
        move = self.move_id
        if move.state != "draft":
            raise UserError(_("Only a draft bill can be split."))
        if any(line.move_id != move for line in self.line_ids):
            raise UserError(_("All selected lines must belong to this bill."))

        already = self.line_ids.filtered("l10n_sk_fuel_split_done")
        if already:
            # Splitting an already-split line would reclassify a share of the
            # remainder again, compounding silently.
            raise UserError(
                _(
                    "These lines have already been split: %s",
                    ", ".join(already.mapped("name")),
                )
            )

        ratio = self.income_ratio / 100.0
        new_lines = []
        for line in self.line_ids:
            net = line.price_subtotal
            if not net:
                continue
            non_tax = move.currency_id.round(net * (1 - ratio))
            if not non_tax:
                continue
            # Same taxes on both parts: the VAT treatment does not change, only
            # which expense account carries the cost.
            new_lines.append(
                Command.create(
                    {
                        "name": _(
                            "Fuel — non-deductible share (%(pct).0f %%) of %(label)s",
                            pct=(1 - ratio) * 100,
                            label=line.name or "",
                        ),
                        "account_id": self.nondeductible_account_id.id,
                        "quantity": 1.0,
                        "price_unit": non_tax,
                        "discount": 0.0,
                        "tax_ids": [Command.set(line.tax_ids.ids)],
                        "l10n_sk_fuel_split_done": True,
                    }
                )
            )
            # price_subtotal is already net of any discount, so the remainder is
            # written as a plain 1 × price with the discount cleared. Leaving a
            # non-zero discount here would apply it a second time to a figure
            # that has already had it deducted.
            line.write(
                {
                    "quantity": 1.0,
                    "price_unit": move.currency_id.round(net - non_tax),
                    "discount": 0.0,
                    "l10n_sk_fuel_split_done": True,
                }
            )

        if not new_lines:
            raise UserError(_("The selected lines carry no amount to split."))
        move.write({"invoice_line_ids": new_lines})
        move.message_post(
            body=_(
                "Fuel split: tax-expense share %(ratio).0f %%, non-deductible "
                "part to account %(account)s. The § 85n VAT restriction is "
                "handled by the tax on the line.",
                ratio=self.income_ratio,
                account=self.nondeductible_account_id.display_name,
            )
        )
        return {"type": "ir.actions.act_window_close"}
