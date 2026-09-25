# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Post-install: tag the standard SK intra-EU supply taxes with their Súhrnný
výkaz (EC sales list) transaction code, so cssk.ec.summary collects them without
manual per-company tax configuration. Identifies the taxes by their l10n_sk
chart-template xmlids (account.<company>_<template>), so it is translation- and
rename-proof.
"""
import logging

_logger = logging.getLogger(__name__)

# l10n_sk tax template -> Súhrnný výkaz transaction code (KOD_PLN):
#   0 = dodanie tovaru, 1 = trojstranný obchod, 2 = dodanie služby
_EC_CODES = {"vy_eu_m": "0", "vy_eu_t": "1", "vy_eu_s": "2"}


def post_init_hook(env):
    for company in env["res.company"].search([("chart_template", "=", "sk")]):
        for template, code in _EC_CODES.items():
            tax = env.ref(
                "account.%s_%s" % (company.id, template), raise_if_not_found=False)
            if tax and not tax.cssk_ec_summary_code:
                tax.cssk_ec_summary_code = code
                _logger.info(
                    "l10n_sk_ec_sales: %s (%s) -> EC code %s",
                    tax.name, company.name, code)
