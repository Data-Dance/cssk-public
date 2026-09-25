# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# A lightweight dated rule-parameter mechanism so the Czech salary rules can
# reference dated statutory values (insurance ceilings, tax thresholds, credits,
# ...) that change from year to year.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class HrRuleParameter(models.Model):
    _name = "hr.rule.parameter"
    _description = "Salary Rule Parameter"
    _order = "code"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(
        required=True,
        help="Code used to reference this parameter from a salary rule, "
        "via payslip.rule_parameter('code').",
    )
    country_id = fields.Many2one("res.country", string="Country")
    description = fields.Text()
    parameter_value_ids = fields.One2many(
        "hr.rule.parameter.value",
        "rule_parameter_id",
        string="Values",
    )

    _sql_constraints = [
        ("code_uniq", "unique (code)", "Two rule parameters cannot share the same code."),
    ]

    @api.model
    def _get_parameter_value(self, code, date):
        """Return the safe_eval'd value of parameter ``code`` effective at ``date``.

        Picks the value whose ``date_from`` is the latest one that is still
        <= ``date``.
        """
        param = self.search([("code", "=", code)], limit=1)
        if not param:
            raise UserError(
                self.env._("No salary rule parameter found for code '%s'.") % code
            )
        value = self.env["hr.rule.parameter.value"].search(
            [
                ("rule_parameter_id", "=", param.id),
                ("date_from", "<=", date),
            ],
            order="date_from desc",
            limit=1,
        )
        if not value:
            raise UserError(
                self.env._(
                    "No value defined for rule parameter '%(code)s' at date %(date)s."
                )
                % {"code": code, "date": date}
            )
        return safe_eval(value.parameter_value)


class HrRuleParameterValue(models.Model):
    _name = "hr.rule.parameter.value"
    _description = "Salary Rule Parameter Value"
    _order = "date_from desc"

    rule_parameter_id = fields.Many2one(
        "hr.rule.parameter",
        string="Rule Parameter",
        required=True,
        ondelete="cascade",
    )
    date_from = fields.Date(string="From", required=True)
    parameter_value = fields.Text(
        string="Value",
        required=True,
        help="A python literal (evaluated with safe_eval), e.g. a number, "
        "tuple or dict.",
    )
