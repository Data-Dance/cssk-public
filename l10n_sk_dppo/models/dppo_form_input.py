# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DppoFormInput(models.AbstractModel):
    _name = "l10n.sk.dppo.form.input.mixin"
    _description = "DPPO entered official annex facts"

    return_id = fields.Many2one(
        "cssk.income.tax.return", required=True, ondelete="cascade"
    )
    company_id = fields.Many2one(related="return_id.company_id", store=True)
    currency_id = fields.Many2one(related="return_id.currency_id")

    @api.model_create_multi
    def create(self, values_list):
        self.check_access("create")
        with self.env.cr.savepoint():
            normalized = [dict(values) for values in values_list]
            for values in normalized:
                values.setdefault(
                    "return_id", self.env.context.get("default_return_id")
                )
                if type(values["return_id"]) is not int or values["return_id"] <= 0:
                    raise UserError(
                        _("Choose a return before entering official annex facts.")
                    )
            identifiers = sorted({values["return_id"] for values in normalized})
            parents = self.env["cssk.income.tax.return"].browse(identifiers).exists()
            if len(parents) != len(identifiers):
                raise UserError(
                    _("Choose an existing return before entering official annex facts.")
                )
            parents.check_access("write")
            by_id = {parent.id: parent for parent in parents}
            for values in normalized:
                parent = by_id[values["return_id"]]
                company = values.pop(
                    "company_id", self.env.context.get("default_company_id")
                )
                currency = values.pop(
                    "currency_id", self.env.context.get("default_currency_id")
                )
                if company and company != parent.company_id.id:
                    raise UserError(
                        _(
                            "Official annex inputs must belong to their return's company."
                        )
                    )
                if currency and currency != parent.currency_id.id:
                    raise UserError(
                        _("Official annex inputs must use their return's currency.")
                    )
            # One globally ordered lock set, even if callers supply opposite
            # multi-return orders. No mutation precedes complete normalization.
            parents._l10n_sk_form_inputs_editable()
            context = dict(self.env.context)
            context.pop("default_company_id", None)
            context.pop("default_currency_id", None)
            return super(DppoFormInput, self.with_context(context)).create(normalized)

    def write(self, values):
        self.check_access("write")
        if {"return_id", "company_id", "currency_id"} & values.keys():
            raise UserError(
                _(
                    "Official annex inputs cannot be reassigned to another return or company."
                )
            )
        with self.env.cr.savepoint():
            self.return_id._l10n_sk_form_inputs_editable()
            return super().write(values)

    def unlink(self):
        self.check_access("unlink")
        with self.env.cr.savepoint():
            self.return_id._l10n_sk_form_inputs_editable()
            return super().unlink()
