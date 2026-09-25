# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Turn a month's garnishment deductions into money owed to the bailiff.

The payroll entry credits one collective liability account for the whole
garnishment total — payroll cannot split a salary rule per creditor, and on
the Enterprise engine the payslip line's partner is derived from the salary
rule, so it cannot vary per employee either.

Remittance closes that gap. Per order and period it books:

    Dr  garnishment liability (collective)
        Cr  accounts payable of the bailiff/creditor, partner set

leaving an ordinary open payable stamped with the case number as the
variable symbol. From there the existing payment-order and bank-file
machinery pays it exactly like any supplier — which is what "part of the
salary is sent to the bailiff directly" means in accounting terms.
"""

from odoo import Command, _, fields, models
from odoo.exceptions import AccessError, UserError


class HrWageGarnishmentLine(models.Model):
    _inherit = "hr.wage.garnishment.line"

    #: What an accountant may change on a deduction line. Remitting writes
    #: exactly these two, and this module's ACL exists to let that happen —
    #: not to hand the amounts of an employee's wage deduction to whoever can
    #: post an entry. Payroll decides what is withheld; accounting records
    #: that it was paid, and the two roles stay apart.
    _CSSK_REMITTANCE_WRITABLE = frozenset({"state", "move_id"})

    def write(self, vals):
        if not self.env.su and not self.env.user.has_group("hr.group_hr_user"):
            beyond = set(vals) - self._CSSK_REMITTANCE_WRITABLE
            if beyond:
                raise AccessError(_(
                    "Only payroll may change a wage deduction. An accountant "
                    "records the remittance; changing %(fields)s on a "
                    "deduction line needs an HR role.",
                    fields=", ".join(sorted(beyond)),
                ))
        return super().write(vals)

    # Declared here rather than in the base: the base depends on ``hr`` and
    # ``mail`` only, so ``account.move`` is not guaranteed to be loaded there.
    move_id = fields.Many2one(
        "account.move",
        "Remittance Entry",
        readonly=True,
        copy=False,
        index="btree_not_null",
        help="Journal entry that turned this deduction into a payable to the "
        "bailiff.",
    )

    def action_remit(self):
        """Book the payables for the selected deductions."""
        moves = self._remit()
        if not moves:
            raise UserError(
                _("Nothing to remit — the selected deductions are already booked.")
            )
        return {
            "type": "ir.actions.act_window",
            "name": _("Remittance Entries"),
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [("id", "in", moves.ids)],
        }

    def _remit(self):
        """Group pending deductions per order and book one entry each.

        One entry per *order* rather than per payee: a bailiff commonly runs
        several cases against the same employer and each needs its own
        variable symbol to be matched on the receiving end.
        """
        pending = self.filtered(lambda line: line.state == "computed")
        moves = self.env["account.move"]
        for order, lines in pending.grouped("garnishment_id").items():
            moves |= lines._remit_one(order)
        return moves

    def _remit_one(self, order):
        company = order.company_id
        self._check_remittance_config(company, order)
        total = sum(self.mapped("amount"))
        if company.currency_id.is_zero(total):
            return self.env["account.move"]
        payee = order.payee_partner_id
        payable = payee.with_company(company).property_account_payable_id
        if not payable:
            raise UserError(
                _(
                    "%(payee)s has no Account Payable set, so the deduction "
                    "for case %(case)s cannot be booked.",
                    payee=payee.display_name,
                    case=order.case_number,
                )
            )
        date = max(self.mapped("date_to"))
        label = _("Wage garnishment %(case)s", case=order.case_number)
        move = (
            self.env["account.move"]
            .with_company(company)
            .create(
                {
                    "move_type": "entry",
                    "journal_id": company.l10n_cssk_garnishment_journal_id.id,
                    "date": date,
                    "ref": label,
                    "partner_id": payee.id,
                    # The order carries its own "Payee Bank Account", domain-
                    # restricted to the payee, precisely because one bailiff
                    # collects for several cases on different accounts. Dropped
                    # here, the payment order downstream silently fell back to
                    # the payee's default account and the money went to the
                    # right creditor on the wrong account.
                    **({"partner_bank_id": order.partner_bank_id.id}
                       if order.partner_bank_id else {}),
                    "line_ids": [
                        Command.create(
                            {
                                "name": label,
                                "account_id": company.l10n_cssk_garnishment_account_id.id,
                                "debit": total,
                                "credit": 0.0,
                            }
                        ),
                        Command.create(
                            {
                                "name": label,
                                "account_id": payable.id,
                                "partner_id": payee.id,
                                "credit": total,
                                "debit": 0.0,
                            }
                        ),
                    ],
                }
            )
        )
        move.action_post()
        # The payment symbols are stored computes keyed on ``name``, which is
        # only assigned at posting — set them afterwards or the recompute
        # would overwrite the case number with the entry's own number.
        move.write(
            {
                "l10n_cssk_variable_symbol": order.variable_symbol,
                "l10n_cssk_specific_symbol": order.specific_symbol,
                "l10n_cssk_constant_symbol": order.constant_symbol,
            }
        )
        self.write({"state": "done", "move_id": move.id})
        # ``sudo`` on the note, not write access on the order: ``message_post``
        # demands write, and granting an accountant write on an exekučný
        # príkaz would let whoever can post an entry change the amount being
        # withheld from someone's wage. The note is the system recording a
        # remittance that did happen, so it is the system that writes it.
        order.sudo().message_post(
            body=_(
                "Remitted %(amount)s to %(payee)s (entry %(move)s).",
                amount=total,
                payee=payee.display_name,
                move=move.name,
            )
        )
        return move

    def _check_remittance_config(self, company, order):
        if not company.l10n_cssk_garnishment_journal_id:
            raise UserError(
                _(
                    "Set a Garnishment Remittance Journal on %s before "
                    "remitting deductions.",
                    company.display_name,
                )
            )
        if not company.l10n_cssk_garnishment_account_id:
            raise UserError(
                _(
                    "Set a Garnishment Liability Account on %s before "
                    "remitting deductions.",
                    company.display_name,
                )
            )
        if not order.payee_partner_id:
            raise UserError(
                _(
                    "Case %s has neither a bailiff nor a creditor, so there is "
                    "nobody to pay.",
                    order.case_number,
                )
            )
