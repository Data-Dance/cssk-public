# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The § 120 difficulty level belongs to the JOB, not to the person doing it.

Annex 1 to the Zákonník práce characterises the six stupne náročnosti in terms
of the work itself — how much independence, responsibility and qualification a
post demands — so an employer classifies posts once and every contract on that
post inherits the classification. Recording it only on the contract, as the
first cut of this module did, means re-deciding it per hire and letting it
drift between two people doing the same job.
"""

from odoo import fields, models

from .l10n_sk_minimum_wage import LEVEL_SELECTION


class HrJob(models.Model):
    _inherit = "hr.job"

    l10n_sk_wage_level = fields.Selection(
        LEVEL_SELECTION,
        string="Stupeň náročnosti",
        groups="hr.group_hr_user",
        help="Difficulty level of this post (§ 120 ods. 2 and Annex 1 to the "
        "Zákonník práce). New contracts on this job start from it. Left "
        "empty, contracts fall back to level 1 — the plain minimum wage.",
    )
