# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    """Give the surcharge rules their GL accounts if the accounting bridge is
    already installed.

    The bridge (l10n_sk_hr_payroll_account_oca) maps these rules softly, by
    xmlid, when it configures a company; installed in the other order, the
    surcharges would arrive with no account, and every surcharge on a posted
    payslip would land in the journal's adjustment line instead of on 521.
    """
    Template = env["account.chart.template"]
    if hasattr(Template, "_l10n_sk_payroll_map_rules"):
        Template._l10n_sk_payroll_map_rules("l10n_sk_hr_payroll_surcharges_oca")
