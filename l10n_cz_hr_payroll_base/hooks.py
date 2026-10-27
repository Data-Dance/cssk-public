# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Take over the statutory accrual plans from an engine module already installed.

Until 19.0.1.0.0 of this module, each payroll engine module
(``l10n_cz_hr_payroll_oca``, ``l10n_cz_hr_payroll_ee``) shipped the four
statutory dovolená accrual plans under its own external IDs. They now live
here. On a database where an engine is already installed, this module is
installed by the engine's upgrade, BEFORE the engine's own migration scripts
run, so the hand-over has to happen here and now:

- without it, loading ``data/hr_leave_accrual_plan_data.xml`` would CREATE a
  second set of plans next to the existing ones, and the engine's upgrade
  would then delete the originals — together with every allocation and
  employee assignment pointing at them;
- with it, the existing records are adopted in place: their IDs, their
  allocations and their translations survive, and this module's data file
  simply updates them.

The Czech fields on ``hr.version`` / ``hr.employee`` need no such step: the
engines still declare them (to set the access group), and Odoo gives a field
one external ID per declaring module, so nothing is ever left without an
owner and no column can be dropped.
"""

import logging

_logger = logging.getLogger(__name__)

ENGINES = ("l10n_cz_hr_payroll_oca", "l10n_cz_hr_payroll_ee")

#: (external-id name, model) of every record moved from the engines.
MOVED_XMLIDS = (
    ("accrual_plan_cz_holiday_4w", "hr.leave.accrual.plan"),
    ("accrual_plan_cz_holiday_4w_level", "hr.leave.accrual.level"),
    ("accrual_plan_cz_holiday_5w", "hr.leave.accrual.plan"),
    ("accrual_plan_cz_holiday_5w_level", "hr.leave.accrual.level"),
    ("accrual_plan_cz_holiday_4w_yearstart", "hr.leave.accrual.plan"),
    ("accrual_plan_cz_holiday_4w_yearstart_level", "hr.leave.accrual.level"),
    ("accrual_plan_cz_holiday_5w_yearstart", "hr.leave.accrual.plan"),
    ("accrual_plan_cz_holiday_5w_yearstart_level", "hr.leave.accrual.level"),
)


def pre_init_hook(env):
    """Re-label the engines' accrual-plan external IDs as this module's."""
    cr = env.cr
    for name, model in MOVED_XMLIDS:
        # Only one engine can be installed at a time (both define the payroll
        # models), but do not rely on it: adopt one row — the installed
        # engine's if there is one — and leave any other alone, so the unique
        # (module, name) key cannot be hit.
        cr.execute(
            """
            UPDATE ir_model_data
               SET module = 'l10n_cz_hr_payroll_base'
             WHERE id = (
                    SELECT d.id FROM ir_model_data d
                      LEFT JOIN ir_module_module m ON m.name = d.module
                     WHERE d.module IN %s AND d.name = %s AND d.model = %s
                     ORDER BY (m.state = 'installed') DESC NULLS LAST, d.id
                     LIMIT 1)
               AND NOT EXISTS (
                    SELECT 1 FROM ir_model_data
                     WHERE module = 'l10n_cz_hr_payroll_base' AND name = %s)
            RETURNING res_id
            """,
            (ENGINES, name, model, name),
        )
        row = cr.fetchone()
        if row:
            _logger.info(
                "l10n_cz_hr_payroll_base: adopted %s (%s #%s) from the engine "
                "module", name, model, row[0])
