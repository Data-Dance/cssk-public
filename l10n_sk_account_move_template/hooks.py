# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from .models.account_chart_template import sk_move_template_data

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Create the starter predkontácie on SK companies that already had the
    chart loaded before this module was installed.

    Reuses the chart-template loader rather than hand-rolling record creation,
    so the xmlids, the company prefixing and the account dereferencing are
    identical to the ones a fresh chart load would produce.

    Only templates the company does not have yet are loaded. ``_load_data``
    calls ``_load_records`` without ``update=True``, and the ``noupdate`` flag
    only takes effect on a module *upgrade* — so an existing record is always
    rewritten, and the ``Command.create`` line payloads would append a second
    copy of every line (violating the ``(sequence, template_id)`` unique
    constraint). Skipping what exists makes the hook idempotent and, more
    importantly, means it never reverts an edit the accountant made to a
    shipped predkontácia: these are editable data records, not code.

    Runs sudo: a post-init hook must work whatever companies the installing
    user happens to belong to.
    """
    companies = env["res.company"].search([("chart_template", "=", "sk")])
    chart_template = env["account.chart.template"].sudo()
    for company in companies:
        loader = chart_template.with_company(company)
        if not loader.ref("general", raise_if_not_found=False):
            _logger.warning(
                "No general journal for company %s — SK predkontácie skipped",
                company.name,
            )
            continue
        missing = {
            xmlid: vals
            for xmlid, vals in sk_move_template_data().items()
            if not loader.ref(xmlid, raise_if_not_found=False)
        }
        if not missing:
            continue
        loader._load_data({"account.move.template": missing})
        _logger.info(
            "SK predkontácie: %s template(s) loaded for company %s",
            len(missing),
            company.name,
        )
