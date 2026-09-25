# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# Make the salary structure country-scoped, mirroring how the accounting
# localization scopes its configuration: a structure carries a country_id and
# may be country-global (company_id left empty) so that every company of that
# country shares it. A record rule (see security/) then filters the salary
# structure list and the struct_id selection to the country of the user's
# active company. The payslip's company comes from the employee, not from the
# structure, so leaving company_id empty is safe for the payroll engine.

from odoo import fields, models


class HrPayrollStructure(models.Model):
    _inherit = "hr.payroll.structure"

    country_id = fields.Many2one(
        "res.country",
        string="Country",
        index=True,
        help="Country this salary structure belongs to. Leave empty for a "
        "structure shared by companies of any country. The payroll "
        "configuration is filtered so a company only sees the salary "
        "structures of its own country.",
    )
    # Relax the engine's required=True so a structure can be country-global
    # (company_id empty) and shared by every company of its country.
    company_id = fields.Many2one(required=False)
