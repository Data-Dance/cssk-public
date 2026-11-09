# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Close the form version: the annual statement ends with 2026.

Act No. 360/2025 Sb. abolishes the vyúčtování daně z příjmů ze závislé
činnosti from the 2027 tax period; the data are reported monthly in the JMHZ
(Act No. 323/2025 Sb.). The version record is ``noupdate``, so the new
``valid_to`` in the data file reaches only a fresh install. Write it here for
existing databases. A later end date is corrected too: no version of
this form can be valid for 2027.
"""
from odoo import SUPERUSER_ID, api, fields


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    record = env.ref(
        "l10n_cz_hr_payroll_annual_tax_settlement.vyuctovani_version_dpzvd6",
        raise_if_not_found=False)
    end = fields.Date.to_date("2026-12-31")
    if record and (not record.valid_to or record.valid_to > end):
        record.valid_to = end
