# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, tools

# Rule codes behind each money tile. The country rule sets name their totals
# differently, so a tile is a LIST of codes: Slovak payroll
# (l10n_sk_hr_payroll_oca) and Czech payroll (l10n_cz_hr_payroll_oca). A code
# that no installed rule emits simply contributes nothing.
#
# - SK: SOCIALEMPLOYERTOTAL already includes the employer health contribution
#   (HEALTHEMPLOYER sits in the SOCIALEMPLOYER category it totals).
# - CZ: social (SOCIALERTOT) and health (HEALTHERTOT) are separate totals, and
#   the employer's sleva na pojistném (SOCIAL_DISCOUNT, negative) is a third
#   line — the same three the Czech EMPLOYERCOST rule adds to GROSS.
GROSS_CODES = ("GROSS",)
NET_CODES = ("NET",)
EMPLOYER_CODES = (
    "SOCIALEMPLOYERTOTAL",
    "SOCIALERTOT",
    "HEALTHERTOT",
    "SOCIAL_DISCOUNT",
)
INCOME_TAX_CODES = ("INCOMETAXTOTAL", "INCOMETAXTOT")

# kpi key -> (sequence, kind, codes); payslips and employees are counts.
KPIS = {
    "gross": (10, "money", GROSS_CODES),
    "net": (20, "money", NET_CODES),
    "employer": (30, "money", EMPLOYER_CODES),
    "labour_cost": (40, "money", GROSS_CODES + EMPLOYER_CODES),
    "income_tax": (50, "money", INCOME_TAX_CODES),
    "payslips": (60, "count", None),
    "employees": (70, "count", None),
}

# Only payslips in this state are counted. Draft and verify payslips can still
# change, and cancelled ones were never paid.
COUNTED_STATE = "done"


class PayrollKpi(models.Model):
    """Read-only SQL view: one row per headline payroll KPI and company,
    rendered as a tile in a kanban dashboard. All-period totals of DONE
    payslips (the dataset is the payroll history); counts for payslips and
    employees."""

    _name = "payroll.kpi"
    _description = "Payroll KPI tile"
    _auto = False
    _order = "company_id, sequence"

    kpi = fields.Selection(
        [
            ("gross", "Total gross"),
            ("net", "Total net"),
            ("employer", "Employer contributions"),
            ("labour_cost", "Total labour cost"),
            ("income_tax", "Income tax"),
            ("payslips", "Payslips"),
            ("employees", "Employees"),
        ],
        string="Figure",
        readonly=True,
    )
    sequence = fields.Integer(readonly=True)
    kind = fields.Selection(
        [("money", "Money"), ("count", "Count")], readonly=True
    )
    value = fields.Float(readonly=True)
    company_id = fields.Many2one("res.company", readonly=True)
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id"
    )

    def _compute_display_name(self):
        labels = dict(self._fields["kpi"]._description_selection(self.env))
        for record in self:
            record.display_name = labels.get(record.kpi, record.kpi or "")

    def _select_queries(self):
        """One SELECT per KPI, each grouped by company."""
        queries = []
        for number, (key, (sequence, kind, codes)) in enumerate(
            KPIS.items(), start=1
        ):
            if key == "payslips":
                value = "COUNT(*)::numeric"
                source = "hr_payslip s"
                where = "s.state = %(state)s"
            elif key == "employees":
                value = "COUNT(DISTINCT s.employee_id)::numeric"
                source = "hr_payslip s"
                where = "s.state = %(state)s"
            else:
                value = "COALESCE(SUM(l.total), 0.0)"
                source = "hr_payslip_line l JOIN hr_payslip s ON s.id = l.slip_id"
                where = "s.state = %%(state)s AND l.code IN (%s)" % ", ".join(
                    "'%s'" % code for code in codes
                )
            queries.append(
                """
                SELECT c.id * 100 + {number} AS id,
                       c.id AS company_id,
                       '{key}' AS kpi,
                       {sequence} AS sequence,
                       '{kind}' AS kind,
                       COALESCE(agg.value, 0.0) AS value
                  FROM res_company c
             LEFT JOIN (SELECT s.company_id, {value} AS value
                          FROM {source}
                         WHERE {where}
                      GROUP BY s.company_id) agg ON agg.company_id = c.id
                """.format(
                    number=number,
                    key=key,
                    sequence=sequence,
                    kind=kind,
                    value=value,
                    source=source,
                    where=where,
                )
            )
        return queries

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = "CREATE VIEW %s AS (%s)" % (
            self._table,
            " UNION ALL ".join(self._select_queries()),
        )
        self.env.cr.execute(query, {"state": COUNTED_STATE})
