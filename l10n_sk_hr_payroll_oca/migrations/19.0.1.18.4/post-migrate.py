# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Carried-over dovolenka no longer lapses (§ 113 Zákonníka práce).

The statutory accrual plans used to put carried-over leave on a 364-day
validity window. The data files now set accrual_validity to False, but an
allocation that was already carried over still holds a pending
carried_over_days_expiration_date and expiring_carryover_days. Odoo
skips the expiry once the level has no validity, yet the stale date still
steers nextcall and misreports the balance as expiring. Clear it on every
allocation of this module's dovolenka plans.

Days that already lapsed under the old plans are NOT restored here: the
amount cannot be told apart from leave that was taken, so it is a payroll
decision per employee (see the CHANGELOG).
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """
        UPDATE hr_leave_allocation a
           SET carried_over_days_expiration_date = NULL,
               expiring_carryover_days = 0
          FROM ir_model_data d
         WHERE d.module = %s
           AND d.model = 'hr.leave.accrual.plan'
           AND d.name LIKE 'l10n_sk_accrual_plan_dovolenka%%'
           AND a.accrual_plan_id = d.res_id
           AND (a.carried_over_days_expiration_date IS NOT NULL
                OR COALESCE(a.expiring_carryover_days, 0) <> 0)
        """,
        ("l10n_sk_hr_payroll_oca",),
    )
