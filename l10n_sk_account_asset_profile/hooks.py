# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Give the starter profiles to SK companies that already had the chart.

    The profiles are chart-template data (``@template("sk",
    "account.asset.profile")``), and a template is only applied when the chart
    is LOADED. Installed afterwards — the ordinary case for a company that
    exists before anyone needs fixed assets — the module created nothing at
    all, and every asset class an import tried to map had no profile to land
    on. Measured on an i6 migration: 0 profiles, 8 asset classes blocking the
    load until the template was loaded by hand.

    Same shape as ``l10n_sk_account_move_template``'s hook, for the same
    reasons: the chart-template loader keeps xmlids, company prefixing and
    account dereferencing identical to a fresh load, and only the profiles a
    company lacks are loaded — ``_load_data`` rewrites an existing record, so
    reloading would revert the useful lives an accountant has already set.

    Runs sudo: a post-init hook must work whatever companies the installing
    user happens to belong to.
    """
    companies = env["res.company"].search([("chart_template", "=", "sk")])
    chart_template = env["account.chart.template"].sudo()
    for company in companies:
        loader = chart_template.with_company(company)
        missing = {
            xmlid: vals
            for xmlid, vals in loader._get_sk_account_asset_profile().items()
            if not loader.ref(xmlid, raise_if_not_found=False)
        }
        if not missing:
            continue
        try:
            # A company that deleted or renumbered an account the template
            # names (012000, 072000, 551000 …) cannot take these profiles as
            # shipped. That is no reason to abort an upgrade, which is where
            # this also runs: skip it and say so.
            with env.cr.savepoint():
                loader._load_data({"account.asset.profile": missing})
        except Exception as exc:  # noqa: BLE001 - reported, not swallowed
            _logger.warning(
                "SK asset profiles NOT loaded for company %s: %s",
                company.name, exc)
            continue
        _logger.info(
            "SK asset profiles: %s loaded for company %s",
            len(missing),
            company.name,
        )
