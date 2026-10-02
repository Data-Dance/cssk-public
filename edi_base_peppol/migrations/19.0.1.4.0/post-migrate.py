"""Peppol settings moved from global parameters to the company.

Nothing changes for an existing database: a company whose partner has a
Peppol address could send before and still can (scope "any customer with a
Peppol address"), the auto-send flag applies to every company as it did, and
the purchase journal belongs to its own company. The parameters are left in
place, unread.
"""

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ICP = env["ir.config_parameter"]
    auto_send = (ICP.get_param("peppol.auto_send") or "").lower() not in (
        "", "0", "false")
    for company in env["res.company"].with_context(active_test=False).search([]):
        partner = company.partner_id
        company.write({
            "peppol_send_enabled": bool(partner.peppol_eas and partner.peppol_endpoint),
            "peppol_auto_send": auto_send,
        })
    journal_id = ICP.get_param("peppol.purchase_journal_id")
    if journal_id and journal_id.isdigit():
        journal = env["account.journal"].browse(int(journal_id)).exists()
        if journal:
            journal.company_id.peppol_purchase_journal_id = journal
