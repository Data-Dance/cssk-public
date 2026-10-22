# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command, models


class HrExpenseSheet(models.Model):
    """18.0 ONLY. 19.0 deleted ``hr.expense.sheet``.

    On 19.0 an expense posts itself: ``hr.expense.action_post`` is the gate and
    ``hr.expense._prepare_receipts_vals`` builds the employee-paid vendor
    receipt. 18.0 still reports expenses on a sheet, which creates both moves
    at APPROVAL time (``_do_approve`` -> ``_check_can_create_move`` ->
    ``_do_create_moves``) and builds the employee-paid bill itself in
    ``_prepare_bills_vals``. So the two overrides 19.0 puts on ``hr.expense``
    belong here, and nowhere else: a gate on ``action_post`` would run after
    the entry it is meant to vet had already been written.

    The company-paid half stays on ``hr.expense``, because
    ``_prepare_payments_vals`` is on the expense in both series.
    """

    _inherit = "hr.expense.sheet"

    def _prepare_bills_vals(self):
        """Employee-paid: the vendor bill carries one line per VAT rate.

        This is 19.0's ``hr.expense._prepare_receipts_vals`` override, moved to
        the model that owns the bill here. Each line keeps ``expense_id``, so
        ``hr_expense`` still treats its amount as tax-included, and the
        partner, account, analytic and product are those Odoo chose for the
        expense's single line.

        The amounts are each rate's gross in COMPANY currency, as on 19.0: an
        own-account sheet is always in the company currency on 18.0 too
        (``hr_expense_sheet._compute_currency_id``), and so is the
        ``price_unit`` core puts on the line.
        """
        vals = super()._prepare_bills_vals()
        lines = []
        for command in vals.get("line_ids", []):
            line = command[2] if len(command) > 2 and isinstance(command[2], dict) else {}
            expense = (self.env["hr.expense"].browse(line["expense_id"])
                       if line.get("expense_id") else None)
            parts = expense._cssk_rate_parts() if expense else None
            if not parts:
                lines.append(command)
                continue
            expense._cssk_check_parts(parts)
            for (_gross, tax, rate), amount in zip(
                    parts, expense._cssk_company_amounts(parts)):
                lines.append(Command.create(dict(
                    line, quantity=1, price_unit=amount,
                    tax_ids=[Command.set(tax.ids)],
                    name="%s (%g %%)" % (line.get("name") or "", rate))))
        vals["line_ids"] = lines
        return vals

    def _check_can_create_move(self):
        """Refuse to build entries for an expense edited away from its receipt.

        19.0 checks this in ``hr.expense.action_post``. Here the moves are
        written at approval, so this — the gate ``_do_approve`` calls first —
        is the moment that counts.
        """
        super()._check_can_create_move()
        for expense in self.expense_line_ids:
            parts = expense._cssk_rate_parts()
            if parts:
                expense._cssk_check_parts(parts)
