# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Map the rules the first version left without accounts.

CHILDBONUS, ANNUAL_TAX_SETTLEMENT and SOCIAL_DISCOUNT had no debit/credit
account, so their amounts never reached 331 / 342 / 524 / 336 although the
employee was paid them. The mapping lives in a post_init_hook, which does not
run on upgrade; re-run it. It only (re)writes the accounts of the mapped
rules for companies that carry the Czech chart.
"""

from odoo import SUPERUSER_ID, api

from odoo.addons.l10n_cz_hr_payroll_account_oca.hooks import (
    _configure_cz_payroll_accounts,
)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _configure_cz_payroll_accounts(env)
