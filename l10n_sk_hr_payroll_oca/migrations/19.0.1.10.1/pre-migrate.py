"""Make the statutory leave configuration updatable again.

The Slovak leave types, work-entry types and accrual plans shipped with
``noupdate="1"``, which froze them at their install-time values: a statutory
change (a new day-cap, a corrected plan) never reached a database that had
already installed the module. These records are legislation, not customer
configuration, so the flag is gone from the data files as of this version —
matching how the Czech modules have always shipped them.

Dropping the attribute is NOT enough on its own. ``ir.model.data.noupdate``
is written when the row is first created and never refreshed afterwards:
``_build_update_xmlids_query`` only ever updates (model, res_id, write_date),
and its ``AND NOT ir_model_data.noupdate`` guard skips exactly the rows we
want to refresh. So an upgraded database would keep the frozen records
forever. Clear the flag here, in PRE-migration, so the data files loaded
later in this same upgrade actually apply.

Only the leave-related models of this module are touched; anything else the
module deliberately froze keeps its flag.
"""

MODULE = "l10n_sk_hr_payroll_oca"

# The models whose data files dropped noupdate in this version.
MODELS = (
    "hr.leave.type",
    "hr.leave.accrual.plan",
    "hr.leave.accrual.level",
    "hr.work.entry.type",
)


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """
        UPDATE ir_model_data SET noupdate = FALSE
         WHERE module = %s AND model IN %s AND noupdate
        """,
        (MODULE, MODELS),
    )
