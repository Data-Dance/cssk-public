# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Unfold a MIS KPI by partner, product, journal, month... in place.

MIS Builder can only expand a KPI into its accounts. A KPI with *Details by*
set gets detail rows per value of that journal-item field instead: each value
found in the column's data is evaluated with the column's filter plus
``field = value``, and stored as a detail row of the KPI.

Only KPIs computed directly from accounting expressions are unfolded: a KPI
that refers to other KPIs would need every one of them recomputed per value,
and a detail row adding up to a different figure than its KPI is worse than
none.
"""
import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Domain

from odoo.addons.mis_builder.models.aep import AccountingExpressionProcessor as AEP
from odoo.addons.mis_builder.models.expression_evaluator import ExpressionEvaluator
from odoo.addons.mis_builder.models.kpimatrix import KpiMatrix

KEY = "d:"     # detail row key prefix: "d:<value>"


class DetailKpiMatrix(KpiMatrix):
    """A KpiMatrix whose detail rows may be keyed by a field value ("d:...")
    rather than an account id, labelled from ``_detail_labels``."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._detail_labels = {}

    def _load_account_names(self):
        saved = self._detail_rows
        self._detail_rows = {
            kpi: {k: r for k, r in rows.items() if not isinstance(k, str)}
            for kpi, rows in saved.items()}
        try:
            super()._load_account_names()
        finally:
            self._detail_rows = saved

    def get_account_name(self, account_id):
        if isinstance(account_id, str):
            return self._detail_labels.get(account_id, account_id)
        return super().get_account_name(account_id)


class MisReportKpi(models.Model):
    _inherit = "mis.report.kpi"

    details_field_id = fields.Many2one(
        "ir.model.fields", string="Details by",
        domain="[('model', '=', 'account.move.line'), ('ttype', 'in', ('many2one', 'selection', 'date')), ('store', '=', True)]",
        ondelete="set null",
        help="Unfold this KPI into one detail row per value of the field (partner, "
             "product, journal, month of the date...) instead of per account. Only "
             "for KPIs computed directly from accounting expressions.")
    details_limit = fields.Integer(
        string="Most detail rows", default=20,
        help="Largest number of detail rows; the busiest values are shown.")

    @api.constrains("details_field_id", "auto_expand_accounts")
    def _check_details_or_accounts(self):
        for kpi in self:
            if kpi.details_field_id and kpi.auto_expand_accounts:
                raise ValidationError(self.env._(
                    "KPI %s: details by a field replace the details by account; "
                    "choose one.", kpi.description or kpi.name))

    def _details_applicable(self):
        """Accounting terms only: no reference to another KPI."""
        self.ensure_one()
        if not self.details_field_id or not self.expression:
            return False
        other_names = set(self.report_id.all_kpi_ids.mapped("name")) - {self.name}
        words = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", self.expression))
        return AEP.has_account_var(self.expression) and not (words & other_names)


class MisReport(models.Model):
    _inherit = "mis.report"

    def prepare_kpi_matrix(self, companies=None):
        matrix = super().prepare_kpi_matrix(companies)
        if not any(self.kpi_ids.mapped("details_field_id")):
            return matrix
        detailed = DetailKpiMatrix(self.env, companies, self.account_model)
        for kpi in self.kpi_ids:
            detailed.declare_kpi(kpi)
        return detailed

    def _declare_and_compute_period(self, expression_evaluator, kpi_matrix, col_key, col_label,
                                    col_description, subkpis_filter=None,
                                    get_additional_query_filter=None, locals_dict=None,
                                    no_auto_expand_accounts=False):
        res = super()._declare_and_compute_period(
            expression_evaluator, kpi_matrix, col_key, col_label, col_description,
            subkpis_filter, get_additional_query_filter, locals_dict, no_auto_expand_accounts)
        if (no_auto_expand_accounts or not isinstance(kpi_matrix, DetailKpiMatrix)
                or not expression_evaluator.aep):
            return res
        subkpis = ([s for s in self.subkpi_ids if s in subkpis_filter]
                   if subkpis_filter else self.subkpi_ids)
        col = kpi_matrix._cols[col_key]
        for kpi in self.kpi_ids.filtered(lambda k: k._details_applicable()):
            for value, label in self._details_values(expression_evaluator, kpi):
                key = f"{KEY}{value}"
                kpi_matrix._detail_labels[key] = label
                extra = self._details_domain(kpi, value)
                evaluator = ExpressionEvaluator(
                    expression_evaluator.aep, expression_evaluator.date_from,
                    expression_evaluator.date_to,
                    list(expression_evaluator.additional_move_line_filter or []) + extra,
                    expression_evaluator.aml_model)
                evaluator.aep_do_queries()
                vals, drilldown_args, name_error = evaluator.eval_expressions(
                    kpi._get_expressions(subkpis), col.locals_dict)
                if name_error:
                    continue
                for arg in drilldown_args:
                    if arg:
                        arg.update(period_id=col_key, kpi_id=kpi.id, detail_domain=extra)
                kpi_matrix.set_values_detail_account(kpi, col_key, key, vals, drilldown_args)
        # Leave the shared AEP holding this column's own figures, as the parent
        # left it, for anything evaluated after this call.
        expression_evaluator.aep.do_queries(
            expression_evaluator.date_from, expression_evaluator.date_to,
            expression_evaluator.additional_move_line_filter, expression_evaluator.aml_model)
        return res

    @api.model
    def _details_domain(self, kpi, value):
        field = kpi.details_field_id
        if field.ttype == "date":
            start = fields.Date.to_date(value)
            end = fields.Date.end_of(start, "month")
            return [(field.name, ">=", start), (field.name, "<=", end)]
        if field.ttype == "many2one":
            return [(field.name, "=", int(value) or False)]
        return [(field.name, "=", value or False)]

    def _details_values(self, expression_evaluator, kpi):
        """[(value, label)] of the field among the journal items the KPI reads
        in this column, busiest first, capped at ``details_limit``."""
        field = kpi.details_field_id
        aml_model = expression_evaluator.aml_model or "account.move.line"
        Model = self.env[aml_model]
        if field.name not in Model._fields:
            return []
        expr = kpi._get_expressions(self.subkpi_ids)[0]
        expr = expr and expr.name or kpi.expression
        domain = Domain(expression_evaluator.aep.get_aml_domain_for_expr(
            expr, expression_evaluator.date_from, expression_evaluator.date_to))
        domain &= Domain(expression_evaluator.additional_move_line_filter or [])
        groupby = f"{field.name}:month" if field.ttype == "date" else field.name
        groups = Model._read_group(domain, [groupby], ["__count"], order="__count desc")
        selection = dict(Model._fields[field.name]._description_selection(self.env)) \
            if field.ttype == "selection" else {}
        values = []
        for value, _count in groups[: kpi.details_limit or None]:
            if field.ttype == "date":
                values.append((fields.Date.to_string(value), value.strftime("%Y-%m") if value else "-"))
            elif field.ttype == "many2one":
                values.append((value.id or 0, value.display_name or self.env._("Undefined")))
            else:
                values.append((value or "", selection.get(value, value) or self.env._("Undefined")))
        return values


class MisReportInstance(models.Model):
    _inherit = "mis.report.instance"

    def drilldown(self, arg):
        extra = arg.get("detail_domain")
        if not extra:
            return super().drilldown(arg)
        action = super().drilldown({k: v for k, v in arg.items() if k != "detail_domain"})
        if action:
            action["domain"] = list(Domain(action["domain"]) & Domain(extra))
        return action


class MisReportInstanceAnnotation(models.Model):
    _inherit = "mis.report.instance.annotation"

    @staticmethod
    def _kpi_details_plain_cell_id(cell_id):
        # A note belongs to the KPI and period, never to a detail row; MIS
        # unpacks the row's account as an integer, which a "d:" key is not.
        parts = cell_id.split("#")
        if len(parts) == 4 and parts[1] and not parts[1].isdigit():
            parts[1] = ""
        return "#".join(parts)

    def _get_first_matching_annotation(self, cell_id, instance_id):
        return super()._get_first_matching_annotation(
            self._kpi_details_plain_cell_id(cell_id), instance_id)

    @api.model
    def set_annotation(self, cell_id, instance_id, note):
        return super().set_annotation(self._kpi_details_plain_cell_id(cell_id), instance_id, note)

    @api.model
    def remove_annotation(self, cell_id, instance_id):
        return super().remove_annotation(self._kpi_details_plain_cell_id(cell_id), instance_id)
