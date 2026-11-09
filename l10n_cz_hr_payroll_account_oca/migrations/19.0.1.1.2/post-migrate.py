# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Map the new SOCIAL_PENSIONER rule on an upgrade.

The mapping lives in a post_init_hook, which does not run on upgrade.
"""

from odoo import SUPERUSER_ID, api

from odoo.addons.l10n_cz_hr_payroll_account_oca.hooks import (
    _configure_cz_payroll_accounts,
)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _configure_cz_payroll_accounts(env)
