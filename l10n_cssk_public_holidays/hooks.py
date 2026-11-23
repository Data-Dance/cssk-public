# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    """Load the years kept present for both countries at install."""
    Holiday = env["calendar.public.holiday"]
    Holiday.cssk_generate(years=Holiday._cssk_kept_years())
    # The working calendars get them once every module is loaded.
    Holiday.cssk_run_scheduled_action_soon()
