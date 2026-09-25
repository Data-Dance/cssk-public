# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Per-contract inputs to the Czech surcharge rules.

``hr.version`` is core ``hr`` in Odoo 19, so these live in the engine-neutral
base and are guarded by ``hr.group_hr_user`` rather than either engine's
payroll group.

Note what is NOT here: there is no Czech counterpart to the Slovak *stupeň
náročnosti*. Zákon č. 230/2024 Sb. abolished *zaručená mzda* for the private
sector from 1 January 2025, leaving one minimum wage for every commercial
employer whatever the job. The four surviving *zaručený plat* groups belong to
the public-sector *plat* regime, which this module does not cover.
"""

from odoo import fields, models


class HrVersion(models.Model):
    _inherit = "hr.version"

    l10n_cz_difficult_factors = fields.Integer(
        string="Ztížené prostředí — počet vlivů",
        groups="hr.group_hr_user",
        tracking=True,
        help="Number of aggravating influences under nařízení vlády č. "
        "567/2006 Sb. Each earns a further 10 % of the basic minimum wage "
        "rate (§ 117). Zero means the surcharge does not apply — recording "
        "hours alone will not pay it.",
    )
    l10n_cz_surcharge_agreed = fields.Boolean(
        string="Sjednaná jiná výše příplatků",
        groups="hr.group_hr_user",
        tracking=True,
        help="A collective or individual agreement sets a different minimum "
        "for the night (§ 116) and weekend (§ 118) surcharges. Only those two "
        "sections permit it; the agreed percentages are configured on the "
        "wage-surcharge rate record.",
    )
