# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Clear the carried-over-leave expiry the dovolená plans used to set.

The statutory plans expired carried-over dovolená 364 days after the 1 January
carryover. § 218 zákoníku práce has no forfeiture, so the plans no longer carry
an accrual validity. Allocations already processed under the old plans still
hold a future ``carried_over_days_expiration_date``; core would no longer act
on it (the level's ``accrual_validity`` is off), but the date keeps showing on
the Time Off dashboard and keeps a leave-expiry reminder firing. Clear it.

Days the old plan already removed on a past expiry date are NOT restored: core
keeps no record of the cut, so the balance has to be corrected by hand.

The plans moved to l10n_cz_hr_payroll_base in a later release, whose
pre_init_hook re-labels their external IDs BEFORE this script runs on a
database that jumps both versions at once — so both owners are matched.
"""

PLAN_XMLIDS = (
    "accrual_plan_cz_holiday_4w",
    "accrual_plan_cz_holiday_5w",
    "accrual_plan_cz_holiday_4w_yearstart",
    "accrual_plan_cz_holiday_5w_yearstart",
)


def migrate(cr, version):
    cr.execute(
        """
        UPDATE hr_leave_allocation a
           SET carried_over_days_expiration_date = NULL,
               expiring_carryover_days = 0
          FROM ir_model_data d
         WHERE d.module IN ('l10n_cz_hr_payroll_oca',
                            'l10n_cz_hr_payroll_base')
           AND d.model = 'hr.leave.accrual.plan'
           AND d.name IN %s
           AND a.accrual_plan_id = d.res_id
           AND (a.carried_over_days_expiration_date IS NOT NULL
                OR a.expiring_carryover_days <> 0)
        """,
        (PLAN_XMLIDS,),
    )
