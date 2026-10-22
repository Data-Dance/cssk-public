# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_sk_dic = fields.Char(
        string="DIČ (tax identification number)",
        help="10-digit tax identification number assigned by the tax "
        "administrator — the <dic> element of the monthly "
        "tax overview.")
