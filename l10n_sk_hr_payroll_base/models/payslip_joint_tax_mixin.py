# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The month's tax of a person with several employee records.

§ 35 ods. 1 zákona č. 595/2003 Z. z. taxes „úhrn zdaniteľných príjmov zo
závislej činnosti zúčtovaných a vyplatených zamestnancovi za kalendárny
mesiac“ less the employee's premiums and one non-taxable amount. Where the
payroll officer has named, on an employee record, the record it is taxed
together with (``hr.employee.l10n_sk_tax_principal_id``):

* the payslip of the LINKED record computes its gross pay, premiums and tax
  base as always, and no non-taxable amount, tax or child bonus. Its exact
  base (income less the employee's premiums, not floored) is shown on the
  line ``TAXBASE_MOVED``;
* the payslip of the PRINCIPAL adds the bases moved by the linked records'
  payslips of the same month (line ``TAXBASE_TAKEN``), floors the total at
  zero once, and computes on it the one non-taxable amount, the advance and
  the child bonus.

So the linked payslips are computed first. The principal's payslip refuses
to be computed while one of them is not, refuses to be confirmed when what it
took over is no longer what the linked payslips hold, and a linked payslip
cannot be changed, cancelled or refunded while a confirmed payslip of the
principal taxes its base. A confirmed payslip is never changed.

A refund and the payslip it refunds are both set aside: neither moves a base
nor takes one over. Payslips are matched by the calendar month of their last
day, in one company. Where the principal has several payslips in a month (a
contract version that changes inside it), one of them takes the bases over:
the first that is computed.

The link itself cannot be changed while a month is half done: one of the two
payslips confirmed and the other not.

A record is taxed on its principal only in a period in which a contract of
the principal runs. Otherwise no payslip of the principal would ever tax its
base, and the record is taxed on its own.

The methods here are the same for both payroll engines; each engine says
which of its payslips are confirmed and which are refunds.
"""

from calendar import monthrange

from odoo import _, api, models
from odoo.exceptions import UserError

#: Line of a linked payslip: the base taxed on the principal's payslip.
MOVED_CODE = "TAXBASE_MOVED"
#: Line of the principal's payslip: the bases taken over.
TAKEN_CODE = "TAXBASE_TAKEN"
#: Inputs of a wage garnishment.
GARNISHMENT_INPUTS = ("GARNISHMENT", "GARNISHMENT_PRIORITY")


class PayslipJointTaxMixin(models.AbstractModel):
    _name = "l10n.sk.payslip.joint.tax.mixin"
    _description = "Slovak payslip: several records of one person taxed together"

    # ------------------------------------------------------------------
    # what each engine says
    # ------------------------------------------------------------------
    def _l10n_sk_joint_tax_applies(self):
        """Whether the payslip is computed on a Slovak structure."""
        self.ensure_one()
        return self.struct_id.country_id.code == "SK"

    def _l10n_sk_joint_tax_is_confirmed(self):
        """Whether the payslip is confirmed (its tax is withheld)."""
        raise NotImplementedError

    def _l10n_sk_joint_tax_is_set_aside(self):
        """Whether the payslip is a refund, or has been refunded."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # who taxes what
    # ------------------------------------------------------------------
    def _l10n_sk_tax_principal(self):
        """The employee record whose payslip taxes this payslip's base.

        Empty for a record taxed on its own, and in a period in which no
        contract of the principal runs.
        """
        self.ensure_one()
        none = self.env["hr.employee"]
        if not self.employee_id or not self._l10n_sk_joint_tax_applies():
            return none
        principal = self.employee_id.sudo().l10n_sk_tax_principal_id
        if not principal or not self.date_from or not self.date_to:
            return none
        if not principal._l10n_sk_contract_runs_in(self.date_from, self.date_to):
            return none
        return principal

    def _l10n_sk_tax_month_payslips(self, employees):
        """The payslips of ``employees`` that count in this payslip's month."""
        self.ensure_one()
        if not employees or not self.date_to:
            return self.browse()
        last_day = monthrange(self.date_to.year, self.date_to.month)[1]
        slips = self.sudo().search([
            ("employee_id", "in", employees.ids),
            ("company_id", "=", self.company_id.id),
            ("date_to", ">=", self.date_to.replace(day=1)),
            ("date_to", "<=", self.date_to.replace(day=last_day)),
            ("state", "!=", "cancel"),
            ("id", "not in", self.ids),
        ])
        return slips.filtered(
            lambda slip: slip._l10n_sk_joint_tax_applies()
            and not slip._l10n_sk_joint_tax_is_set_aside()
        )

    def _l10n_sk_line_total(self, code):
        self.ensure_one()
        return sum(self.line_ids.filtered(lambda line: line.code == code).mapped("total"))

    def _l10n_sk_tax_linked_payslips(self):
        """``(moving, pending)`` payslips of the records taxed on this one.

        *Moving* payslips carry a moved base. *Pending* ones are not computed
        yet, or were computed before the records were linked. A confirmed
        payslip without a moved base was taxed on its own, before the link,
        and is left as it is.
        """
        self.ensure_one()
        moving = pending = self.browse()
        if (
            not self.employee_id
            or not self._l10n_sk_joint_tax_applies()
            or self._l10n_sk_joint_tax_is_set_aside()
        ):
            return moving, pending
        linked = self.employee_id.sudo().l10n_sk_tax_linked_ids
        if not linked:
            return moving, pending
        if any(
            line.code == TAKEN_CODE
            for line in self._l10n_sk_tax_month_payslips(self.employee_id).line_ids
        ):
            # Another payslip of this record took the month's bases over.
            return moving, pending
        for slip in self._l10n_sk_tax_month_payslips(linked):
            if any(line.code == MOVED_CODE for line in slip.line_ids):
                moving |= slip
            elif not slip._l10n_sk_joint_tax_is_confirmed():
                pending |= slip
        return moving, pending

    def _l10n_sk_takes_over_tax_base(self):
        """Rule helper: whether linked payslips move a base to this one."""
        self.ensure_one()
        return bool(self._l10n_sk_tax_linked_payslips()[0])

    def _l10n_sk_tax_base_taken_over(self):
        """Rule helper: the bases the linked payslips of the month move here."""
        self.ensure_one()
        moving, _pending = self._l10n_sk_tax_linked_payslips()
        return round(sum(slip._l10n_sk_line_total(MOVED_CODE) for slip in moving), 2)

    def _l10n_sk_monthly_tax_base(self, exact_base):
        """Rule helper: the base of the month's advance and of the child bonus.

        ``exact_base`` is the payslip's own income less the employee's
        premiums, not floored. A payslip taxed on its own has that base,
        floored at zero, as before. A linked payslip has none: its base is
        taxed on the principal's. The principal's payslip has its own base
        and the bases taken over, floored at zero once.
        """
        self.ensure_one()
        if self._l10n_sk_tax_principal():
            return 0.0
        if not self._l10n_sk_takes_over_tax_base():
            return max(0.0, exact_base)
        return max(0.0, round(exact_base + self._l10n_sk_tax_base_taken_over(), 2))

    # ------------------------------------------------------------------
    # order and consistency
    # ------------------------------------------------------------------
    def _l10n_sk_check_joint_tax_before_compute(self):
        """Refuse what cannot be computed right, with a message for the user.

        A rule's own error reaches the user wrapped in a traceback, so the
        engines call this before the rules run.
        """
        for slip in self:
            if not slip._l10n_sk_joint_tax_applies():
                continue
            _moving, pending = slip._l10n_sk_tax_linked_payslips()
            if pending:
                raise UserError(_(
                    "The income tax of %(employee)s is computed together with "
                    "%(linked)s (Taxed Together With). The payslip "
                    "%(payslip)s of %(linked)s for this month is not computed "
                    "yet, or was computed before the two records were "
                    "linked. Compute it first.",
                    employee=slip.employee_id.display_name,
                    linked=pending[0].employee_id.display_name,
                    payslip=pending[0].display_name,
                ))
            slip._l10n_sk_check_joint_tax_garnishment()

    def _l10n_sk_has_garnishment(self):
        """Whether the wage garnishment rule will compute on this payslip."""
        self.ensure_one()
        if set(self.input_line_ids.mapped("code")) & set(GARNISHMENT_INPUTS):
            return True
        return (
            "hr.wage.garnishment" in self.env
            and bool(self.env["hr.wage.garnishment"]._payslip_has_orders(self))
        )

    def _l10n_sk_check_joint_tax_garnishment(self, force=False):
        """Refuse a wage garnishment on a payslip that is taxed together.

        § 69 ods. 1 Exekučného poriadku deducts „z čistej mzdy povinného“,
        and ods. 2 counts into it „aj čisté odmeny za vedľajšiu činnosť“: the
        net wage is the person's from the employer, all relationships
        together, with the basic sum of § 70 left to the debtor once. A
        payslip holds one relationship. With the month's tax on the
        principal's payslip, its net wage would come out too low there and
        too high on the linked payslip, so no deduction is computed from
        either. Called before the rules run, and again by the rule's own
        helper (``l10n_sk_garnishment_net_wage``, with ``force``).
        """
        for slip in self:
            principal = slip._l10n_sk_tax_principal()
            other = principal or (
                slip._l10n_sk_tax_linked_payslips()[0].employee_id
            )
            if not other or not (force or slip._l10n_sk_has_garnishment()):
                continue
            raise UserError(_(
                "The wage garnishment of %(employee)s cannot be computed on "
                "this payslip. Its income tax is computed together with "
                "%(other)s, and a garnishment is deducted from the person's "
                "whole net wage from the employer (§ 69 Exekučného poriadku), "
                "which one payslip does not hold. Remove Taxed Together With "
                "to tax the records separately, or leave the garnishment "
                "out of this payslip and deduct it by hand.",
                employee=slip.employee_id.display_name,
                other=", ".join(other.mapped("display_name")),
            ))

    def _l10n_sk_confirmed_principal_payslips(self):
        """The principal's confirmed payslips of this (linked) payslip's month."""
        self.ensure_one()
        principal = self.employee_id.sudo().l10n_sk_tax_principal_id
        if not principal or not self._l10n_sk_joint_tax_applies():
            return self.browse()
        return self._l10n_sk_tax_month_payslips(principal).filtered(
            lambda slip: slip._l10n_sk_joint_tax_is_confirmed()
        )

    def _l10n_sk_check_joint_tax_after_compute(self):
        """A linked payslip must not change what a confirmed payslip taxed."""
        for slip in self:
            if slip._l10n_sk_joint_tax_is_set_aside():
                continue
            for confirmed in slip._l10n_sk_confirmed_principal_payslips():
                took = confirmed._l10n_sk_line_total(TAKEN_CODE)
                now = confirmed._l10n_sk_tax_base_taken_over()
                if abs(took - now) >= 0.005:
                    raise UserError(_(
                        "The payslip %(payslip)s of %(principal)s for this "
                        "month is confirmed, and its income tax includes a "
                        "tax base of %(took).2f taken over from the records "
                        "taxed together with it. With this payslip of "
                        "%(employee)s that base would be %(now).2f. Refund or "
                        "cancel the payslip of %(principal)s first, then "
                        "compute this payslip and a new one for "
                        "%(principal)s.",
                        payslip=confirmed.display_name,
                        principal=confirmed.employee_id.display_name,
                        employee=slip.employee_id.display_name,
                        took=took,
                        now=now,
                    ))

    def _l10n_sk_check_joint_tax_before_confirm(self):
        """The principal's payslip is confirmed with what the linked ones hold."""
        for slip in self:
            if (
                not slip._l10n_sk_joint_tax_applies()
                or slip._l10n_sk_joint_tax_is_set_aside()
            ):
                continue
            moved = any(line.code == MOVED_CODE for line in slip.line_ids)
            if moved != bool(slip._l10n_sk_tax_principal()):
                raise UserError(_(
                    "Taxed Together With of %(employee)s, or the contract of "
                    "the record named there, changed after this payslip was "
                    "computed. Compute the payslip again before confirming "
                    "it.",
                    employee=slip.employee_id.display_name,
                ))
            moving, pending = slip._l10n_sk_tax_linked_payslips()
            if pending:
                raise UserError(_(
                    "The income tax of %(employee)s is computed together with "
                    "%(linked)s (Taxed Together With). The payslip "
                    "%(payslip)s of %(linked)s for this month is not computed "
                    "yet, or was computed before the two records were "
                    "linked. Compute it first.",
                    employee=slip.employee_id.display_name,
                    linked=pending[0].employee_id.display_name,
                    payslip=pending[0].display_name,
                ))
            if moving:
                # Two requests at once: whoever changes a linked payslip
                # while this one is confirmed makes this request start over.
                self.env.cr.execute(
                    "SELECT id FROM hr_payslip WHERE id IN %s FOR UPDATE",
                    [tuple(moving.ids)],
                )
            took = slip._l10n_sk_line_total(TAKEN_CODE)
            now = slip._l10n_sk_tax_base_taken_over()
            if abs(took - now) >= 0.005:
                raise UserError(_(
                    "The payslip of %(employee)s was computed with a tax base "
                    "of %(took).2f taken over from %(linked)s, and their "
                    "payslips of this month now hold %(now).2f. Compute the "
                    "payslip of %(employee)s again before confirming it.",
                    employee=slip.employee_id.display_name,
                    linked=", ".join(
                        (moving.employee_id
                         or slip.employee_id.sudo().l10n_sk_tax_linked_ids
                         ).mapped("display_name")),
                    took=took,
                    now=now,
                ))
            slip._l10n_sk_check_joint_tax_after_compute()

    def _l10n_sk_check_joint_tax_before_withdrawal(self):
        """A base taxed on a confirmed payslip stays where it is.

        For a linked payslip that is about to be cancelled, refunded or
        deleted.
        """
        for slip in self:
            if (
                not slip._l10n_sk_joint_tax_applies()
                or slip._l10n_sk_joint_tax_is_set_aside()
                or not any(line.code == MOVED_CODE for line in slip.line_ids)
            ):
                continue
            for confirmed in slip._l10n_sk_confirmed_principal_payslips():
                if any(line.code == TAKEN_CODE for line in confirmed.line_ids):
                    raise UserError(_(
                        "The tax base of this payslip of %(employee)s is taxed "
                        "on the confirmed payslip %(payslip)s of "
                        "%(principal)s. Refund or cancel that payslip first.",
                        employee=slip.employee_id.display_name,
                        payslip=confirmed.display_name,
                        principal=confirmed.employee_id.display_name,
                    ))

    @api.ondelete(at_uninstall=False)
    def _unlink_except_base_taxed_elsewhere(self):
        self._l10n_sk_check_joint_tax_before_withdrawal()

    @api.model
    def _l10n_sk_tax_link_blockers(self, employees):
        """The payslips that forbid changing Taxed Together With now.

        A payslip of one of the linked ``employees`` that moved its base, in
        a month that is half done: it is confirmed and no confirmed payslip
        of the principal has taken the base (unlinked now, the base would
        never be taxed), or a confirmed payslip of the principal has taken it
        and it is still open (unlinked now and computed again, the base would
        be taxed twice).
        """
        slips = self.sudo().search([
            ("employee_id", "in", employees.ids),
            ("state", "!=", "cancel"),
            ("line_ids.code", "=", MOVED_CODE),
        ])
        blockers = self.browse()
        for slip in slips:
            if not slip._l10n_sk_joint_tax_applies() or slip._l10n_sk_joint_tax_is_set_aside():
                continue
            taken = any(
                line.code == TAKEN_CODE
                for line in slip._l10n_sk_confirmed_principal_payslips().line_ids
            )
            if taken != slip._l10n_sk_joint_tax_is_confirmed():
                blockers |= slip
        return blockers
