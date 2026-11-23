# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Rounding of a wage component to the cent.

§ 130 ods. 1 Zákonníka práce rounds the wage paid out upward and the Code has
no rule for a single component. Each component (base pay, leave pay, an
obstacle compensation) is therefore rounded upward as well: the direction
that can never take a fraction of a cent from the employee.
"""

from odoo.tools import float_round

# Nine decimals hold every true fraction the wage formulas produce (a wage in
# cents x hours / hours; hours x a four-decimal average x a percentage), and
# the noise of binary arithmetic lies below them.
NOISE_PLACES = 9


def round_wage_component(amount):
    """Round a wage component up to the cent.

    Pass the exact result of the component's formula for the whole payslip
    period and round it here once: parts rounded one by one add up to more
    than the whole. An amount that is a whole cent stays that cent, also when
    binary arithmetic delivers it a hair above. A negative amount, the
    component of a refund, mirrors the original: its absolute value is
    rounded up and the sign kept.
    """
    return float_round(
        round(amount, NOISE_PLACES), precision_digits=2, rounding_method="UP"
    )
