# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Re-run the ř43/ř44 tagging with signed tag names, and retag what is posted.

The hook matched nothing on this series (it looked for ``VAT 3 Base`` where
the chart says ``+VAT 3 Base``), so every Czech company upgraded through here
has self-assessed taxes whose deduction reaches no line of the return and
whose declaration the return engine reads with the wrong sign.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "cz")])
    if companies:
        companies._cz_tag_selfassessed_deduction()
        # And the entries already posted, or a period straddling this upgrade
        # reads the old lines and the new ones with opposite signs and they
        # cancel. See ``_cz_retag_posted_selfassessed_lines``.
        companies._cz_retag_posted_selfassessed_lines()
