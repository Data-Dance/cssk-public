# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Several relationships of one person with one employer, taxed together.

An employment and an agreement beside it are two employee records, each with
its own payslip. § 35 ods. 1 zákona č. 595/2003 Z. z.: „Zdaniteľnou mzdou je
úhrn zdaniteľných príjmov zo závislej činnosti zúčtovaných a vyplatených
zamestnancovi za kalendárny mesiac ..., znížený o a) sumy zrazené na poistné a
príspevky, ktoré je povinný platiť zamestnanec, b) nezdaniteľnú časť základu
dane na daňovníka“. The taxable wage is the total the employer pays the
employee in the month, with one non-taxable amount.

No authority says in so many words how two relationships at one employer are
taxed, so nothing is inferred from the data: the payroll officer names, on a
record, the record it is *taxed together with*. The payslip of the record
named, the principal, then taxes the month's total
(``l10n.sk.payslip.joint.tax.mixin``).
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .hr_version import birth_number_key


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    l10n_sk_tax_principal_id = fields.Many2one(
        "hr.employee",
        string="Taxed Together With",
        domain="[('company_id', '=', company_id), ('id', '!=', id), "
        "('l10n_sk_tax_principal_id', '=', False)]",
        help="Another employee record of the same person in this company, for "
        "example the employment beside this agreement. The income tax of "
        "this record is then computed on the payslip of that record: it "
        "taxes the total of the month with one non-taxable amount and one "
        "child tax bonus (§ 35 ods. 1 zákona č. 595/2003 Z. z.), and the "
        "payslip of this record shows its tax base and no tax. Compute the "
        "payslip of this record first. Leave empty to tax this record on "
        "its own.",
        groups="hr.group_hr_user",
        tracking=True,
        copy=False,
        index="btree_not_null",
        ondelete="restrict",
    )
    l10n_sk_tax_linked_ids = fields.One2many(
        "hr.employee",
        "l10n_sk_tax_principal_id",
        string="Taxed on This Record",
        help="The employee records of the same person whose tax base is taxed "
        "on the payslip of this record.",
        groups="hr.group_hr_user",
    )

    @api.constrains("l10n_sk_tax_principal_id", "company_id")
    def _check_l10n_sk_tax_principal(self):
        for employee in self.sudo():
            principal = employee.l10n_sk_tax_principal_id
            for linked in employee.l10n_sk_tax_linked_ids:
                if linked.company_id != employee.company_id:
                    raise ValidationError(_(
                        "%(linked)s is taxed together with %(employee)s, so "
                        "the two records have to stay in one company.",
                        linked=linked.display_name,
                        employee=employee.display_name,
                    ))
            if not principal:
                continue
            if principal == employee:
                raise ValidationError(_(
                    "%(employee)s cannot be taxed together with itself.",
                    employee=employee.display_name,
                ))
            if principal.company_id != employee.company_id:
                raise ValidationError(_(
                    "%(employee)s can be taxed together only with a record of "
                    "the same company: the tax of the month is the tax of "
                    "what one employer pays.",
                    employee=employee.display_name,
                ))
            if principal.l10n_sk_tax_principal_id:
                raise ValidationError(_(
                    "%(principal)s is itself taxed together with "
                    "%(other)s. Choose %(other)s for %(employee)s as well: "
                    "one record taxes the month for all the others.",
                    principal=principal.display_name,
                    other=principal.l10n_sk_tax_principal_id.display_name,
                    employee=employee.display_name,
                ))
            if employee.l10n_sk_tax_linked_ids:
                raise ValidationError(_(
                    "%(employee)s already taxes the month for %(linked)s, so "
                    "it cannot be taxed on another record. One record taxes "
                    "the month for all the others.",
                    employee=employee.display_name,
                    linked=", ".join(
                        employee.l10n_sk_tax_linked_ids.mapped("display_name")),
                ))
            employee._l10n_sk_check_tax_principal_person()

    def write(self, vals):
        if "l10n_sk_tax_principal_id" in vals:
            self._l10n_sk_check_tax_link_change(vals["l10n_sk_tax_principal_id"])
        return super().write(vals)

    def _l10n_sk_check_tax_link_change(self, new_principal_id):
        """Refuse to change the link in the middle of a month's payroll.

        The payslips of the two records are computed and confirmed one after
        the other. Between the two confirmations a change of the link would
        leave a base taxed twice or not at all, and nothing could put a
        confirmed payslip right (``_l10n_sk_tax_link_blockers``).
        """
        Payslip = self.env.get("hr.payslip")
        if Payslip is None or not hasattr(Payslip, "_l10n_sk_tax_link_blockers"):
            return
        changing = self.sudo().filtered(
            lambda employee: employee.l10n_sk_tax_principal_id
            and employee.l10n_sk_tax_principal_id.id != (new_principal_id or False)
        )
        blocker = Payslip._l10n_sk_tax_link_blockers(changing)[:1] if changing else Payslip
        if blocker:
            raise ValidationError(_(
                "Taxed Together With of %(employee)s cannot be changed now. "
                "The payslip %(payslip)s moved its tax base to the payslip of "
                "%(principal)s, and of the two payslips of that month one is "
                "confirmed and the other is not. Confirm both, or refund the "
                "confirmed one, and change the link then.",
                employee=blocker.employee_id.display_name,
                payslip=blocker.display_name,
                principal=blocker.employee_id.sudo().l10n_sk_tax_principal_id.display_name,
            ))

    def _l10n_sk_check_tax_principal_person(self):
        """Records taxed together are one person: the same birth number.

        Checked when both records carry one; a record without it is the
        officer's word alone.
        """
        for employee in self.sudo():
            for other in (
                employee.l10n_sk_tax_principal_id | employee.l10n_sk_tax_linked_ids
            ):
                mine = birth_number_key(employee.identification_id)
                theirs = birth_number_key(other.identification_id)
                if mine and theirs and mine != theirs:
                    raise ValidationError(_(
                        "%(employee)s and %(other)s have different birth "
                        "numbers, so they are not one taxpayer and cannot be "
                        "taxed together.",
                        employee=employee.display_name,
                        other=other.display_name,
                    ))

    def _l10n_sk_contract_runs_in(self, first, last):
        """Whether a contract of this record runs on a day of the period."""
        self.ensure_one()
        return any(
            version.contract_date_start
            and version.contract_date_start <= last
            and (not version.contract_date_end or version.contract_date_end >= first)
            for version in self.sudo().version_ids
        )
