# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models

# ÚDZS common health-insurer codes (kód zdravotnej poisťovne).
HEALTH_INSURER_CODES = [
    ("25", "VšZP (25)"),
    ("24", "Dôvera (24)"),
    ("27", "Union (27)"),
]


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_sk_health_insurer_code = fields.Selection(
        HEALTH_INSURER_CODES,
        string="Health insurer (dávka 514)",
        default="25",
        help="Target health insurance company for the monthly dávka 514. "
        "The dávka 514 structure is common to all "
        "three insurers; only this code and the payer/bank details differ.")
    l10n_sk_health_payer_number = fields.Char(
        string="Health payer number",
        help="Payer number assigned to the employer by the health insurer — "
        "the payer-number item of the dávka 514 identification block.")
