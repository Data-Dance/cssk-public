# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Statutory figures that a new year replaces and that must not carry over.

Most salary rule parameters stay in force until changed, so taking the latest
value is right. These are published for each year: the meal allowance limit and
the amounts behind the non-attachable part of a wage. From 2027 a payslip using
one refuses to compute on last year's figure.
"""

from datetime import date as date_type

from odoo import _
from odoo.exceptions import UserError

CZ_ANNUAL_PARAMETERS = frozenset({
    "l10n_cz_meal_exempt",
    "l10n_cz_garnish_subsistence",
    "l10n_cz_garnish_normative_rent",
    "l10n_cz_garnish_energy",
    "l10n_cz_garnish_unlimited_limit",
})
GUARD_FROM = date_type(2027, 1, 1)


def check_annual_value(code, date, value_date):
    """Raise when ``code`` is annual and its value is from an earlier year."""
    if (code in CZ_ANNUAL_PARAMETERS and date and date >= GUARD_FROM
            and value_date and value_date.year != date.year):
        raise UserError(_(
            "The %(year)s value of salary rule parameter %(code)s has not been "
            "entered yet; the latest one is from %(found)s.",
            year=date.year, code=code, found=value_date.year,
        ))
