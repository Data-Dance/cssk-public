# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Move supplies to private persons in other member states from A.1 to D.2.

The resolver sent a non-taxable customer to D.2 only when the customer was
not in the EU; one in another member state, taxed at Slovak rates, went to
A.1. Confirmed wrong by an accountant on 2026-09-21. The section is stored and
depends on data, not code, so the affected lines are recomputed here: posted
sales documents of Slovak companies whose partner is in another EU state.
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    eu = env.ref("base.europe", raise_if_not_found=False)
    if not eu:
        return
    foreign_eu = eu.country_ids.filtered(lambda c: c.code != "SK")
    companies = env["res.company"].with_context(active_test=False).search(
        [("account_fiscal_country_id.code", "=", "SK")])
    changed = 0
    for company in companies:
        lines = env["account.move.line"].with_company(company).search([
            ("company_id", "=", company.id),
            ("parent_state", "=", "posted"),
            ("move_id.move_type", "in", ("out_invoice", "out_refund")),
            ("move_id.partner_id.country_id", "in", foreign_eu.ids),
        ])
        changed += lines._cssk_recompute_section_codes()
    _logger.info("l10n_sk_kv_dph 19.0.2.0.8: %s line(s) changed section "
                 "(EU private customers to D.2)", changed)
