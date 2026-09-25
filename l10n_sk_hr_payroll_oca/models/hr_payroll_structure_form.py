# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Make the employment form a single choice on the OCA contract.

The OCA engine has no ``hr.payroll.structure.type``, so the form is carried by
the STRUCTURE here — which costs nothing, because its ``rule_ids`` is a
Many2many and all four structures share one rule set. (Enterprise is the
opposite way round: rules there carry a required Many2one to their structure,
so it uses types instead. Same behaviour, different mechanism, which the parity
harness exists to keep honest.)
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.l10n_sk_hr_payroll_base.applicability import ALL_FORMS


class HrPayrollStructure(models.Model):
    _inherit = "hr.payroll.structure"

    l10n_sk_agreement_type = fields.Selection(
        selection=[
            ("none", "Employment (pracovný pomer)"),
            ("dovp", "DoVP — agreement to perform work"),
            ("dopc", "DoPČ — agreement on work activity"),
            ("dobps", "DoBPŠ — student work agreement"),
        ],
        string="Slovak employment form",
        help="The Slovak employment form this structure represents. Choosing "
        "the structure sets the contract's agreement type, and a contract may "
        "not then disagree with it.",
    )

    def _l10n_sk_form(self):
        """The declared form, or None where the structure declares none."""
        self.ensure_one()
        form = self.l10n_sk_agreement_type
        return form if form in ALL_FORMS else None


class HrVersion(models.Model):
    _inherit = "hr.version"

    @api.depends("struct_id")
    def _compute_l10n_sk_agreement_type(self):
        """The structure decides the employment form.

        A compute rather than an onchange, because an onchange never runs on
        create: a contract created programmatically would sit on the DoPČ
        structure still calling itself employment, and the constraint below
        would reject it at the point of creation.
        """
        for version in self:
            form = version.struct_id._l10n_sk_form() if version.struct_id else None
            version.l10n_sk_agreement_type = (
                form or version.l10n_sk_agreement_type or "none"
            )

    @api.constrains("struct_id", "l10n_sk_agreement_type")
    def _check_l10n_sk_agreement_matches_structure(self):
        for version in self:
            if not version.struct_id:
                continue
            form = version.struct_id._l10n_sk_form()
            if form and version.l10n_sk_agreement_type != form:
                raise ValidationError(
                    _(
                        "This contract is on the %(struct)s structure, which "
                        "is the %(form)s employment form, but its agreement "
                        "type is %(actual)s. Change the structure rather than "
                        "the agreement type — the structure is what decides "
                        "the form.",
                        struct=version.struct_id.name,
                        form=form,
                        actual=version.l10n_sk_agreement_type or "none",
                    )
                )
