# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, tools


class PayrollKpi(models.Model):
    """Read-only SQL view: one row per headline payroll KPI, rendered as a
    tile in a kanban dashboard. All-period totals (the dataset is the payroll
    history); counts for payslips and employees."""

    _name = "payroll.kpi"
    _description = "Payroll KPI tile"
    _auto = False
    _order = "sequence"

    name = fields.Char(readonly=True)
    sequence = fields.Integer(readonly=True)
    kind = fields.Selection(
        [("money", "Money"), ("count", "Count")], readonly=True
    )
    value = fields.Float(readonly=True)
    currency_id = fields.Many2one(
        "res.currency", compute="_compute_currency_id"
    )

    def _compute_currency_id(self):
        currency = self.env.company.currency_id
        for record in self:
            record.currency_id = currency

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """
            CREATE VIEW %s AS (
                SELECT 1 AS id, 10 AS sequence, 'Total gross' AS name,
                       'money' AS kind, COALESCE(SUM(total), 0.0) AS value
                  FROM hr_payslip_line WHERE code = 'GROSS'
                UNION ALL
                SELECT 2, 20, 'Total net', 'money', COALESCE(SUM(total), 0.0)
                  FROM hr_payslip_line WHERE code = 'NET'
                UNION ALL
                SELECT 3, 30, 'Employer contributions', 'money',
                       COALESCE(SUM(total), 0.0)
                  FROM hr_payslip_line WHERE code = 'SOCIALEMPLOYERTOTAL'
                UNION ALL
                SELECT 4, 40, 'Total labour cost', 'money',
                       COALESCE(SUM(total), 0.0)
                  FROM hr_payslip_line
                 WHERE code IN ('GROSS', 'SOCIALEMPLOYERTOTAL')
                UNION ALL
                SELECT 5, 50, 'Income tax', 'money', COALESCE(SUM(total), 0.0)
                  FROM hr_payslip_line WHERE code = 'INCOMETAXTOTAL'
                UNION ALL
                SELECT 6, 60, 'Payslips', 'count',
                       (SELECT COUNT(*) FROM hr_payslip)::numeric
                UNION ALL
                SELECT 7, 70, 'Employees', 'count',
                       (SELECT COUNT(DISTINCT employee_id) FROM hr_payslip)::numeric
            )
            """
            % self._table
        )
