# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    """Overviews that exist already were not entered by hand.

    ``manual_entry`` defaults to "no payroll app installed", and the ORM
    fills a new column with the default on every existing row. On a database
    whose payroll app was removed since, that would mark every overview
    generated from payslips as entered by hand, with amounts of zero, and a
    quarter's refund request would then count those months as nothing.
    Creating the column first leaves the existing rows unticked.
    """
    if not version:
        return
    cr.execute(
        "ALTER TABLE l10n_sk_prehlad "
        "ADD COLUMN IF NOT EXISTS manual_entry boolean")
