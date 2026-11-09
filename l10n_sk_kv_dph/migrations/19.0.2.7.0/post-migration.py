# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Create the § 69 ods. 12 písm. a) až e) sale tax on existing SK companies."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["res.company"].search([("chart_template", "=", "sk")])._cssk_ensure_rc_out_tax()
