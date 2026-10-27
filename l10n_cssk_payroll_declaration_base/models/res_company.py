# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # The ČSSZ employer identification every Czech ČSSZ form needs (PVPOJ,
    # ELDP, ONZ). Each of those modules declares the field too; declaring it
    # here as well gives the company form ONE place to show it, whichever of
    # them is installed.
    l10n_cz_ossz_vs = fields.Char(
        string="ČSSZ variable symbol (VS)",
        help="Variable symbol the ČSSZ assigned to the employer (10 digits).")
    l10n_cz_ossz_code = fields.Char(
        string="OSSZ code",
        help="Numeric code (100-999) of the locally competent District "
        "Social Security Administration (OSSZ).")
