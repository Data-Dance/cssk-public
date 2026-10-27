# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date


def post_init_hook(env):
    """Load the current and the next year for both countries at install."""
    year = date.today().year
    env["calendar.public.holiday"].cssk_generate(years=(year, year + 1))
