"""The NACE code's default target is now ``res.partner.nace_code``
(``partner_nace``). Re-apply the defaults without overwriting a mapping
someone chose, so an upgraded database points the NACE at it."""

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["partner.autocomplete.provider.orsf_sk"]._orsf_apply_default_mappings()
