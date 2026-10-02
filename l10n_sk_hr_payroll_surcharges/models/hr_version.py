# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Per-contract inputs to the surcharge and minimum-wage-claim rules.

``hr.version`` is core ``hr`` in Odoo 19, so these fields can live in the
engine-neutral base. They are guarded by ``hr.group_hr_user`` rather than
either engine's payroll group for the same reason.
"""

from odoo import _, api, fields, models

from .l10n_sk_minimum_wage import LEVEL_SELECTION
from .surcharge_calc import STANDARD_WEEKLY_HOURS


class HrVersion(models.Model):
    _inherit = "hr.version"

    l10n_sk_wage_level = fields.Selection(
        LEVEL_SELECTION,
        string="Stupeň náročnosti",
        groups="hr.group_hr_user",
        tracking=True,
        help="Difficulty level of the job (§ 120 ods. 2 Zákonníka práce). "
        "Sets the minimum wage claim the achieved wage is topped up to. "
        "Left empty it is treated as level 1, the plain minimum wage.",
    )
    # Deliberately NO default. A default of "1" would be indistinguishable
    # from a deliberate classification as pomocné práce, and — worse — it
    # would make the inheritance from hr.job dead code, since the field would
    # never be empty for it to fill. Everything that consumes the level reads
    # it as ``level or "1"``, so an unclassified post still behaves as the
    # plain minimum wage; it just no longer claims to have been classified.
    l10n_sk_risk_work = fields.Boolean(
        string="Riziková práca",
        groups="hr.group_hr_user",
        tracking=True,
        help="The work is classified in category 3 or 4 (riziková práca), "
        "raising the night surcharge to 50 % and the overtime surcharge to "
        "35 %. It also rules out the reduced night rate.",
    )
    l10n_sk_night_reduced = fields.Boolean(
        string="Reduced night rate agreed",
        groups="hr.group_hr_user",
        tracking=True,
        help="§ 122a ods. 3 — a collective agreement sets the night surcharge "
        "at the lower statutory floor because the predominant part of the "
        "work is performed at night. Ignored for risky work.",
    )
    l10n_sk_saturday_reduced = fields.Boolean(
        string="Reduced Saturday rate agreed",
        groups="hr.group_hr_user",
        tracking=True,
        help="§ 122b ods. 2 — a collective agreement sets the Saturday "
        "surcharge at the lower statutory floor because the nature of the "
        "work requires regular work on Saturdays.",
    )
    l10n_sk_sunday_reduced = fields.Boolean(
        string="Reduced Sunday rate agreed",
        groups="hr.group_hr_user",
        tracking=True,
        help="§ 122c ods. 2 — a collective agreement sets the Sunday "
        "surcharge at the lower statutory floor because the nature of the "
        "work requires regular work on Sundays.",
    )

    # ------------------------------------------------------------------
    # minimum wage claim: surface a shortfall at data-entry time
    # ------------------------------------------------------------------
    l10n_sk_min_wage_warning = fields.Char(
        string="Minimum Wage Warning",
        compute="_compute_l10n_sk_min_wage_warning",
        help="Set when the agreed wage falls below the § 120 minimum wage "
        "claim for this contract's difficulty level.",
    )

    @api.onchange("job_id")
    def _onchange_l10n_sk_job_wage_level(self):
        """Inherit the post's difficulty level when a job is chosen.

        Only ever fills a level in — it never overwrites one already set, so a
        contract that legitimately differs from its post keeps its own value.
        """
        for version in self:
            level = version.job_id.l10n_sk_wage_level
            if level and not version.l10n_sk_wage_level:
                version.l10n_sk_wage_level = level

    def _l10n_sk_full_time_fraction(self):
        """This contract's working time as a fraction of full time.

        § 120 ods. 4 reduces the monthly claim in proportion for a shorter
        working week, so a part-timer on a proportionately lower wage is
        lawfully paid and must not be warned about.
        """
        self.ensure_one()
        calendar = self.resource_calendar_id
        if not calendar or not calendar.hours_per_week:
            return 1.0
        full_time = (
            calendar.full_time_required_hours
            or self._l10n_sk_standard_weekly_hours()
        )
        if not full_time:
            return 1.0
        return min(1.0, calendar.hours_per_week / full_time)

    def _l10n_sk_standard_weekly_hours(self):
        """§ 85 ods. 5 ustanovený týždenný pracovný čas, from the dated rate
        record. Falls back to the kernel default rather than raising: this only
        ever backstops a calendar with no full-time reference, and a contract
        form must not blow up because the rate table has not been loaded yet."""
        self.ensure_one()
        rate = self.env["l10n.sk.wage.surcharge.rate"].search(
            [("date_from", "<=", self.date_version or fields.Date.today())],
            order="date_from desc", limit=1,
        )
        return rate.standard_weekly_hours if rate else STANDARD_WEEKLY_HOURS

    @api.depends(
        "wage", "l10n_sk_wage_level", "date_version", "resource_calendar_id"
    )
    def _compute_l10n_sk_min_wage_warning(self):
        claim_model = self.env["l10n.sk.minimum.wage"]
        for version in self:
            version.l10n_sk_min_wage_warning = False
            if version.company_id.country_id.code != "SK" or not version.wage:
                continue
            # § 120 governs employment relationships. Agreements (dohody) are
            # outside it — they answer to the plain minimum hourly wage — so a
            # dohodár's monthly figure is not comparable to a monthly claim.
            # Same table the payslip rule consults, so the warning and the
            # payment can no longer disagree about who § 120 covers.
            if not version.l10n_sk_applies("MIN_WAGE_CLAIM"):
                continue
            # Hourly contracts are compared per hour on the payslip, not
            # against a monthly figure; skip rather than warn wrongly.
            if version._fields.get("l10n_sk_hourly_wage") and version.l10n_sk_hourly_wage:
                continue
            claim = claim_model.search(
                [
                    ("date_from", "<=", version.date_version or fields.Date.today()),
                    ("level", "=", version.l10n_sk_wage_level or "1"),
                ],
                order="date_from desc",
                limit=1,
            )
            if not claim:
                continue
            due = round(claim.amount_monthly * version._l10n_sk_full_time_fraction(), 2)
            if version.wage + 0.005 < due:
                version.l10n_sk_min_wage_warning = _(
                    "The agreed wage of %(wage).2f is below the minimum wage "
                    "claim of %(due).2f for stupeň náročnosti %(level)s "
                    "(§ 120 Zákonníka práce). The payslip will top it up, but "
                    "the contract itself does not meet the statutory minimum.",
                    wage=version.wage,
                    due=due,
                    level=version.l10n_sk_wage_level or "1",
                )
