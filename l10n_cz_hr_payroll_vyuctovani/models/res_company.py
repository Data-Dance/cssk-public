# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_cz_fu_code = fields.Char(
        string="Tax office code (FÚ)",
        help="1-4 digit numeric code of the locally competent tax office "
        "from the ÚFO register — the annual tax settlement "
        "<VetaD c_ufo_cil> attribute.")
    l10n_cz_vyuctovani_typ_ds = fields.Selection(
        [("F", "F — natural person"),
         ("P", "P — legal entity"),
         ("L", "L — payer's cashier")],
        string="Filing subject type",
        default="P",
        help="Type of the filing subject — the annual tax settlement "
        "<VetaP typ_ds> attribute.")
