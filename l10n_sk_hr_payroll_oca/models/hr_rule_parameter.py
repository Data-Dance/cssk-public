# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# A lightweight dated rule-parameter mechanism so the Slovak salary rules can
# reference dated statutory values (assessment-base ceiling, income-tax
# thresholds, insurance rates, ...) that change from year to year.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


def _parameter_value_key(value):
    """Compare evaluated definitions without merging bool/int or list/tuple.

    An int and a float compare by value (``1`` matches ``1.0``): every rule
    computes the same result from either. A bool stays apart from both.
    """
    if isinstance(value, bool):
        return bool, value
    if isinstance(value, (int, float)):
        return float, value
    if isinstance(value, (list, tuple)):
        return type(value), tuple(_parameter_value_key(item) for item in value)
    if isinstance(value, dict):
        return dict, frozenset(
            (_parameter_value_key(key), _parameter_value_key(item))
            for key, item in value.items()
        )
    if isinstance(value, (set, frozenset)):
        return type(value), frozenset(_parameter_value_key(item) for item in value)
    return type(value), value


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

    # Odoo 19 ignores ``_sql_constraints``; the declaration has to be a
    # models.Constraint or the table silently has no unique index at all.
    _code_uniq = models.Constraint(
        "unique (code)",
        "Two rule parameters cannot share the same code.",
    )

    @api.model
    def _get_parameter_value(self, code, date):
        """Return the safe_eval'd value of parameter ``code`` effective at ``date``.

        Picks the latest effective date that is still <= ``date``. Identical
        legacy definitions at that date are accepted; conflicting definitions
        require an explicit correction instead of choosing one by row order.
        """
        param = self.search([("code", "=", code)], limit=1)
        if not param:
            raise UserError(
                self.env._("No salary rule parameter found for code '%s'.") % code
            )
        # Two rows: the second tells in the same query whether another
        # definition shares the effective date, so the common path stays one
        # search and only a tie pays for the full peer search below.
        candidates = self.env["hr.rule.parameter.value"].search(
            [
                ("rule_parameter_id", "=", param.id),
                ("date_from", "<=", date),
            ],
            order="date_from desc, id",
            limit=2,
        )
        value = candidates[:1]
        if not value:
            raise UserError(
                self.env._(
                    "No value defined for rule parameter '%(code)s' at date %(date)s."
                )
                % {"code": code, "date": date}
            )
        result = safe_eval(value.parameter_value)
        if len(candidates) < 2 or candidates[1].date_from != value.date_from:
            return result
        # Multiple modules or a native copy can define the same effective date.
        # Preserve equivalent legacy rows, but never let SQL tie order decide
        # which conflicting legal/configuration value a calculation consumes.
        peers = (
            self.env["hr.rule.parameter.value"].search(
                [
                    ("rule_parameter_id", "=", param.id),
                    ("date_from", "=", value.date_from),
                ],
                order="id",
            )
            - value
        )
        if not peers:
            return result
        expected = _parameter_value_key(result)
        if any(
            _parameter_value_key(safe_eval(peer.parameter_value)) != expected
            for peer in peers
        ):
            raise UserError(
                self.env._(
                    "Conflicting salary rule parameter values for '%(code)s' on "
                    "%(date)s. Keep one definition or matching values for that "
                    "effective date."
                )
                % {"code": code, "date": value.date_from}
            )
        return result


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
