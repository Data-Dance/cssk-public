# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_sk_sp_vs = fields.Char(
        string="Sociálna poisťovňa variable symbol",
        help="10-digit identification number assigned to "
        "the employer by the Sociálna poisťovňa — the <variabilnySymbol> "
        "element of the MVP overview.")
