# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    """Map the SK payroll accounts for companies that already use the SK chart.

    Companies that load the ``l10n_sk`` chart *after* this module is installed
    are handled by the ``account.chart.template._load`` override; this hook
    covers companies whose chart was loaded *before* the install.
    """
    companies = env["res.company"].search([("chart_template", "=", "sk")])
    if companies:
        env["account.chart.template"]._configure_sk_payroll_accounts(companies)
