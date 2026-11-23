# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Annual settlements already made keep their stored result.

The new stored field tax_underpayment_waived is computed together with
the result. Left to the ORM, adding its column would recompute every existing
settlement under the rules of this version, the posted ones included, whose
amount is already on a payslip. Creating the column here keeps the ORM from
doing that; the post-migration recomputes the settlements not yet posted.
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """
        ALTER TABLE l10n_sk_tax_reconciliation
        ADD COLUMN IF NOT EXISTS tax_underpayment_waived numeric
        """
    )
