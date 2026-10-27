# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import SUPERUSER_ID, api

from odoo.addons.l10n_sk_account_cutoff.hooks import disable_unconfigured_tax_accrual


def migrate(cr, version):
    """Accrual On Taxes off on existing companies too (see the hook)."""
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    disable_unconfigured_tax_accrual(
        env["res.company"].search([("chart_template", "=", "sk")])
    )
