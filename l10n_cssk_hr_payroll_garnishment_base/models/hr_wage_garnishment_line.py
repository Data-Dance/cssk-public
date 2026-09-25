# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""One month's deduction against one garnishment order.

These lines are the ledger the whole feature turns on: they drive the paid /
remaining balance on the order, they are what the *vyúčtování srážek* report
prints, and the accounting bridge groups them per payee to build the payable
that actually sends the money to the bailiff.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrWageGarnishmentLine(models.Model):
    _name = "hr.wage.garnishment.line"
    _description = "Wage Garnishment Deduction"
    _order = "date_to desc, garnishment_id"

    _check_amount = models.Constraint(
        "CHECK (amount >= 0)",
        "A garnishment deduction may not be negative.",
    )

    garnishment_id = fields.Many2one(
        "hr.wage.garnishment", required=True, index=True, ondelete="cascade"
    )
    employee_id = fields.Many2one("hr.employee", required=True, index=True)
    company_id = fields.Many2one(
        "res.company", related="garnishment_id.company_id", store=True
    )
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id")
    payee_partner_id = fields.Many2one(
        "res.partner", related="garnishment_id.payee_partner_id", store=True
    )
    case_number = fields.Char(related="garnishment_id.case_number", store=True)
    claim_class = fields.Selection(
        related="garnishment_id.claim_class", store=True
    )

    payslip_ref = fields.Char(
        required=True,
        index=True,
        help="Engine-neutral reference to the payslip the deduction came from "
        "(``hr.payslip,<id>``). The base module never stores a foreign key to "
        "a payslip table, so it works on either payroll engine.",
    )
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True, index=True)

    amount = fields.Monetary(required=True)
    amount_first_third = fields.Monetary(
        "From First Third",
        help="Part taken from the first third, shared by all claims in pořadí.",
    )
    amount_second_third = fields.Monetary(
        "From Second Third",
        help="Part taken from the second third, reserved for priority claims.",
    )
    amount_unlimited = fields.Monetary(
        "From Unlimited Part",
        help="Always zero: the calculator does not split this out per line. "
        "The fully seizable amount above the statutory limit is merged into "
        "the two third-pools before anything is allocated (see "
        "``garnishment_calc.compute_cz`` / ``compute_sk``), so a deduction's "
        "share of it is not a fact the waterfall produces — only the pool "
        "totals are. Kept as a stored field so existing rows are unchanged; "
        "not shown, because a column that always reads zero is read as "
        "'nothing came from there' rather than 'not tracked'.",
    )

    state = fields.Selection(
        [
            ("computed", "Computed"),
            ("done", "Remitted"),
        ],
        default="computed",
        required=True,
        index=True,
        help="'Remitted' once the accounting bridge has booked the payable to "
        "the payee. Remitted lines are never recomputed.",
    )
    # The link to the remittance journal entry (``move_id``) is added by
    # l10n_cssk_hr_payroll_garnishment_account. It cannot live here: this
    # module depends on ``hr`` and ``mail`` only, so ``account.move`` may not
    # exist in the registry.

    def unlink(self):
        if any(line.state == "done" for line in self):
            raise UserError(
                _(
                    "Remitted garnishment deductions cannot be deleted — the "
                    "money has already been booked as payable to the payee. "
                    "Reverse the remittance entry instead."
                )
            )
        return super().unlink()

    @api.model
    def _open_for_remittance(self, company, date_to, payee=None):
        """Computed lines not yet turned into a payable."""
        domain = [
            ("company_id", "=", company.id),
            ("state", "=", "computed"),
            ("date_to", "<=", date_to),
        ]
        if payee:
            domain.append(("payee_partner_id", "=", payee.id))
        return self.search(domain)
