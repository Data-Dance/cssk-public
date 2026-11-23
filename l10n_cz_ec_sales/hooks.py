# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Post-install: give companies that already had the l10n_cz chart what the
chart template now carries for later ones.

* the intermediary's triangular-trade taxes (rows 30 / 31, EC code 2), which
  the l10n_cz chart lacks;
* the Souhrnné hlášení (EC sales list) transaction code on the standard
  intra-EU supply taxes, so cssk.ec.summary collects them without manual
  per-company tax configuration.

Taxes are identified by their chart-template xmlids
(account.<company>_<template>), so this is translation- and rename-proof.
"""
import logging

from .models.account_chart_template import EC_CODES, TRIANGULAR_TAXES

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    for company in env["res.company"].search([("chart_template", "=", "cz")]):
        # One company whose chart was edited (a tag deleted, a group renamed)
        # must not stop the upgrade for every other company.
        try:
            with env.cr.savepoint():
                _ensure_triangular_taxes(env, company)
        except Exception:  # noqa: BLE001 - logged, the others still run
            _logger.exception(
                "l10n_cz_ec_sales: the triangular-trade taxes could not be "
                "added to %s; add them by hand", company.name)
        for template, code in EC_CODES.items():
            tax = env.ref(
                "account.%s_%s" % (company.id, template), raise_if_not_found=False)
            if tax and not tax.cssk_ec_summary_code:
                tax.cssk_ec_summary_code = code
                _logger.info(
                    "l10n_cz_ec_sales: %s (%s) -> EC code %s",
                    tax.name, company.name, code)


def _ensure_triangular_taxes(env, company):
    """Load the triangular-trade taxes a company charted earlier lacks.

    Only the missing ones: ``_load_data`` rewrites a record it is handed, so
    passing a tax the company already has would revert whatever was changed
    on it since.
    """
    Template = env["account.chart.template"].with_company(company)
    missing = [xmlid for xmlid in TRIANGULAR_TAXES if not env.ref(
        "account.%s_%s" % (company.id, xmlid), raise_if_not_found=False)]
    if not missing:
        return
    data = Template._parse_csv("cz", "account.tax", module="l10n_cz_ec_sales")
    Template._deref_account_tags("cz", data)
    taxes = {xmlid: data[xmlid] for xmlid in missing}
    for xmlid in missing:
        if xmlid in EC_CODES:
            taxes[xmlid]["cssk_ec_summary_code"] = EC_CODES[xmlid]
    # ``_load_data`` drops the ``field@lang`` columns (a chart load applies
    # them in a separate step this path does not run), so they are taken
    # before it sees the dict.
    translations = {
        xmlid: {key: value for key, value in vals.items() if "@" in key and value}
        for xmlid, vals in taxes.items()}
    Template._load_data({"account.tax": taxes})
    for xmlid, columns in translations.items():
        tax = env.ref("account.%s_%s" % (company.id, xmlid))
        for key, value in columns.items():
            field, lang = key.split("@", 1)
            code = {"cs": "cs_CZ"}.get(lang, lang)
            if env["res.lang"]._lang_get(code) and field in tax._fields:
                tax.with_context(lang=code)[field] = value
    _logger.info("l10n_cz_ec_sales: triangular-trade taxes %s added to %s",
                 ", ".join(missing), company.name)
