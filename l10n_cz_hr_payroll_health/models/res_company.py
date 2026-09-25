# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models

from .l10n_cz_health_common import CZ_HEALTH_INSURERS


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_cz_health_insurer_code = fields.Selection(
        selection=CZ_HEALTH_INSURERS,
        string="Default health insurer",
        default="111",
        help="Default Czech health-insurance company "
        "for employees who have no insurer set on their own record — the "
        "kodZdravotniPojistovny of the PPPZ / HOZ filings.")
    l10n_cz_health_payer_number = fields.Char(
        string="Health payer number",
        help="10-digit health-insurance payer number "
        "(identifikacniCisloPlatce): the employer IČ (8 digits) followed by "
        "the 2-digit accounting-office sub-number (00-99). Leave empty to "
        "derive it from the company IČ as <IČ>00.")
