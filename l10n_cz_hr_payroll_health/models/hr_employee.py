# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models

from .l10n_cz_health_common import CZ_HEALTH_INSURERS


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    l10n_cz_health_insurer_code = fields.Selection(
        selection=CZ_HEALTH_INSURERS,
        string="Health insurer",
        groups="hr.group_hr_user",
        help="The employee's Czech health-insurance company. "
        "PPPZ / HOZ filings are grouped per insurer: this "
        "employee is reported to the insurer set here, or — if empty — to the "
        "company's default health insurer.")

    def _l10n_cz_effective_health_insurer(self):
        """The insurer this employee is reported to for CZ health filings:
        the employee's own insurer, falling back to the company default."""
        self.ensure_one()
        return (self.l10n_cz_health_insurer_code
                or self.company_id.l10n_cz_health_insurer_code)
