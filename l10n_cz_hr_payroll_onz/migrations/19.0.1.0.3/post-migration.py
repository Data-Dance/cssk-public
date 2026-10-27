# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Close the form version: ONZ is replaced by the JMHZ employee registration from 1 April 2026.

The version record is ``noupdate``, so the new ``valid_to`` in the data
file reaches only a fresh install. Write it here for existing databases.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    record = env.ref("l10n_cz_hr_payroll_onz.onz_version_2022", raise_if_not_found=False)
    if record and not record.valid_to:
        record.valid_to = "2026-03-31"
