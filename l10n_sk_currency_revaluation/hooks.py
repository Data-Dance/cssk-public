# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import json
import logging

from .models.account_chart_template import SK_REVAL_ACCOUNTS

_logger = logging.getLogger(__name__)

KURZ_NAMES = {
    "en_US": "Exchange Rate Differences",
    "sk_SK": "Kurzové rozdiely",
    "cs_CZ": "Kurzové rozdíly",
}


def post_init_hook(env):
    """Wire the revaluation defaults, then name the KURZ journal in all languages."""
    _post_init(env)
    adopt_kurz_journal_names(env, "sk")


def _post_init(env):
    """Set OCA revaluation accounts + journal on existing Slovak companies."""
    companies = env["res.company"].search([("chart_template", "=", "sk")])
    for company in companies:
        vals = {}
        for field, xmlid in SK_REVAL_ACCOUNTS.items():
            if company[field]:
                continue
            account = env.ref(
                f"account.{company.id}_{xmlid}", raise_if_not_found=False
            )
            if account:
                vals[field] = account.id
        if not company.currency_reval_journal_id:
            # An existing KURZ (in Slovak and Czech this is often Odoo's own
            # exchange journal, whose code EXCH is translated to KURZ), else
            # the company's exchange-difference journal; a new KURZ only when
            # the company has neither.
            Journal = env["account.journal"]
            journal = Journal.search(
                [("code", "=", "KURZ"), ("company_id", "=", company.id)], limit=1
            ) or company.currency_exchange_journal_id
            if not journal:
                journal = Journal.create(
                    {
                        "name": KURZ_NAMES["en_US"],
                        "code": "KURZ",
                        "type": "general",
                        "company_id": company.id,
                    }
                )
                _write_journal_names(env, journal, KURZ_NAMES)
            vals["currency_reval_journal_id"] = journal.id
        if vals:
            company.write(vals)
            _logger.info("Slovak revaluation defaults set for %s", company.name)


def _stored_journal_names(env, journal):
    journal.flush_recordset(["name"])
    env.cr.execute("SELECT name FROM account_journal WHERE id = %s", [journal.id])
    row = env.cr.fetchone()
    return (row and row[0]) or {}


def _write_journal_names(env, journal, names):
    """Write every language, installed or not (the ORM refuses inactive ones)."""
    journal.flush_recordset(["name"])
    env.cr.execute(
        "UPDATE account_journal SET name = COALESCE(name, '{}'::jsonb) || %s::jsonb"
        " WHERE id = %s",
        [json.dumps(names), journal.id],
    )
    journal.invalidate_recordset(["name"])


def adopt_kurz_journal_names(env, chart_template):
    """Name the KURZ journal in Slovak, Czech and English.

    Earlier versions created it with only the national name, stored as its
    English source. A journal still carrying that name gets all three; one
    whose English name is already ours only gets the languages it lacks; a
    journal the user renamed is left alone.
    """
    companies = env["res.company"].search([("chart_template", "=", chart_template)])
    journals = env["account.journal"].search(
        [("code", "=", "KURZ"), ("company_id", "in", companies.ids)]
    )
    ours = {name for lang, name in KURZ_NAMES.items() if lang != "en_US"}
    for journal in journals:
        stored = _stored_journal_names(env, journal)
        current = stored.get("en_US")
        if current in ours:
            _write_journal_names(env, journal, KURZ_NAMES)
        elif current == KURZ_NAMES["en_US"]:
            missing = {k: v for k, v in KURZ_NAMES.items() if k not in stored}
            if missing:
                _write_journal_names(env, journal, missing)
