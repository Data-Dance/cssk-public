# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Post-install: flag the standard Czech reverse-charge taxes so the engine
recognises self-assessment for the control statement and the VAT return without
manual per-company tax configuration.

The list and the mechanism live on ``res.company`` — see
``_cssk_reverse_charge_tax_templates`` — because the same work has to happen on
three occasions: install (here), **chart load** (a company created after the
module was installed, which is the normal case on a migration project) and
**upgrade** (a company that already existed when an earlier version shipped).
Having it in only one of the three is how a company ends up with no flagged
taxes and a control statement that files with no B.1 section.
"""
import logging

_logger = logging.getLogger(__name__)

_BATCH = 10000


def post_init_hook(env):
    companies = env["res.company"].search([("chart_template", "=", "cz")])
    flagged = companies._cssk_flag_reverse_charge_taxes()
    _logger.info(
        "l10n_cz_kh: %s reverse-charge tax(es) flagged across %s company/companies",
        flagged, len(companies),
    )
    _recompute_section_codes(env, "CZ", "l10n_cz_kh")


def _recompute_section_codes(env, country_code, label):
    """Recompute the stored section code of every existing move line.

    ``cssk_control_section_code`` is added by ``l10n_cssk_kv_kh_base``, and
    Odoo computes a new stored column for the existing rows at the moment the
    column is created — that is, when the BASE module installs, while the only
    resolver loaded is the base one that returns ``False`` for everything. This
    module's resolver arrives a few seconds later, and nothing tells Odoo the
    stored values are now stale: none of the field's dependencies changed.

    So on a database with history, every line kept ``False`` and every
    statement computed empty, with no error anywhere. Measured on a Slovak
    agenda installed into an existing database: all tax-bearing posted lines
    January to August 2026 carried no section, and the write_date of every one
    was the base module's install second.
    """
    # Archived companies too: a company closed down can still owe a late or
    # corrective statement for a period in which it traded.
    companies = env["res.company"].sudo().with_context(active_test=False).search(
        [("account_fiscal_country_id.code", "=", country_code)])
    changed = 0
    for company in companies:
        aml = env["account.move.line"].sudo().with_company(company).with_context(
            allowed_company_ids=[company.id])
        ids = aml.search([("company_id", "=", company.id),
                          ("parent_state", "=", "posted")]).ids
        # In chunks, and with the cache dropped between them: an agenda of a
        # few hundred thousand lines otherwise holds every line, partner and
        # tax the resolver touched in one prefetch set until the end.
        for start in range(0, len(ids), _BATCH):
            changed += aml.browse(ids[start:start + _BATCH])._cssk_recompute_section_codes()
            env.invalidate_all()
    _logger.info("%s: control section assigned on %s existing move line(s) "
                 "across %s company/companies", label, changed, len(companies))
    return changed
