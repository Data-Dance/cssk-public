# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).

from odoo import fields, models


class AdvanceSaldoXlsxWizard(models.TransientModel):
    _name = "advance.saldo.xlsx.wizard"
    _description = "Open Advances Saldo (XLSX)"

    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    include_settled = fields.Boolean(
        string="Include Settled Advances",
        help="Also list advances that are fully paid, tax-documented and "
        "deducted (open saldo zero).",
    )

    def action_print(self):
        self.ensure_one()
        return self.env.ref(
            "advance_invoice_saldo_xlsx.report_advance_saldo_xlsx"
        ).report_action(self)
