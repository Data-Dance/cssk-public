# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Have the holidays of the previous month written into the calendars.

    Through the scheduled action, so that it happens with every module
    loaded and Time Off recounts the leave requests that span a holiday.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["calendar.public.holiday"].cssk_run_scheduled_action_soon()
