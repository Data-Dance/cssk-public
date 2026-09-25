# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # Re-declared (compatible) so ELDP does not have to depend on the PVPOJ
    # module; if that module is installed the field definitions simply merge.
    l10n_cz_ossz_vs = fields.Char(
        string="ČSSZ variable symbol (VS)",
        help="8-10 digit variable symbol assigned to the "
        "employer by the ČSSZ — the ELDP <comp vs> attribute.")
    l10n_cz_ossz_code = fields.Char(
        string="OSSZ code",
        default="100",
        help="Numeric code (100-999) of the locally competent District Social "
        "Security Administration (OSSZ) — the ELDP <eldp09 tco/dep>.")
