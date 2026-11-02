# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Split a MIS Builder column into one column per value of a field.

A period with a *breakdown field* (journal, partner, company, product,
analytic account, ... - any many2one or selection field of its move line
source) is computed once per value found in its data, then once more as the
total under its own key. The total keeps the period's id as column key, so sum
and comparison columns that reference the period keep working; the sub-columns
use ``"<period id>:<value>"`` keys, which drill-down understands.
"""
from odoo import api, fields, models
from odoo.fields import Domain

from odoo.addons.mis_builder.models.expression_evaluator import ExpressionEvaluator

SEP = ":"


class MisReportInstancePeriod(models.Model):
    _inherit = "mis.report.instance.period"

    breakdown_field_id = fields.Many2one(
        "ir.model.fields", string="Columns by",
        domain="[('model', '=', source_aml_model_name), ('ttype', 'in', ('many2one', 'selection')), ('store', '=', True)]",
        ondelete="set null",
        help="Split this column into one column per value of the field found in "
             "its data, followed by the total.")
    breakdown_limit = fields.Integer(
        string="Most columns", default=12,
        help="Largest number of breakdown columns; values beyond it are left to the total.")

    def _breakdown_values(self, query_company_ids):
        """[(value, label)] of the breakdown field found in this period's data,
        most used first, capped at ``breakdown_limit``."""
        self.ensure_one()
        field = self.breakdown_field_id
        Model = self.env[self.source_aml_model_name]
        domain = Domain(self._get_additional_move_line_filter()) & Domain([
            ("date", ">=", self.date_from), ("date", "<=", self.date_to)])
        if "company_id" in Model._fields:
            domain &= Domain("company_id", "in", query_company_ids.ids)
        groups = Model._read_group(domain, [field.name], ["__count"], order="__count desc")
        values = []
        selection = dict(Model._fields[field.name]._description_selection(self.env)) \
            if field.ttype == "selection" else {}
        for value, _count in groups[: self.breakdown_limit or None]:
            if field.ttype == "many2one":
                values.append((value.id or 0, value.display_name or self.env._("Undefined")))
            else:
                values.append((value or "", selection.get(value, value) or self.env._("Undefined")))
        return sorted(values, key=lambda v: v[1].lower())

    def _breakdown_domain(self, value):
        self.ensure_one()
        field = self.breakdown_field_id
        if field.ttype == "many2one":
            return [(field.name, "=", int(value) or False)]
        return [(field.name, "=", value or False)]


class MisReportInstance(models.Model):
    _inherit = "mis.report.instance"

    def _add_column_move_lines(self, aep, kpi_matrix, period, label, description):
        if period.breakdown_field_id and period.date_from and period.date_to:
            for value, value_label in period._breakdown_values(self.query_company_ids):
                evaluator = ExpressionEvaluator(
                    aep, period.date_from, period.date_to,
                    period._get_additional_move_line_filter() + period._breakdown_domain(value),
                    period.source_aml_model_name,
                )
                self.report_id._declare_and_compute_period(
                    evaluator, kpi_matrix, f"{period.id}{SEP}{value}", value_label, label,
                    period.subkpi_ids, period._get_additional_query_filter,
                    no_auto_expand_accounts=self.no_auto_expand_accounts,
                )
            label = self.env._("%s (total)", label)
        return super()._add_column_move_lines(aep, kpi_matrix, period, label, description)

    @api.model
    def _split_breakdown_key(self, period_id):
        if isinstance(period_id, str) and SEP in period_id:
            period_key, value = period_id.split(SEP, 1)
            return int(period_key), value
        return period_id, None

    def drilldown(self, arg):
        period_id, value = self._split_breakdown_key(arg.get("period_id"))
        if value is None:
            return super().drilldown(arg)
        action = super().drilldown(dict(arg, period_id=period_id))
        if action:
            period = self.env["mis.report.instance.period"].browse(period_id)
            action["domain"] = list(Domain(action["domain"]) & Domain(period._breakdown_domain(value)))
        return action
