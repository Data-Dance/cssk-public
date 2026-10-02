"""Which company sends through Peppol, to whom, and books what it receives where.

One database can hold a company that must send e-invoices (hascon, a Slovak
VAT payer under the 2027 mandate) and one that must not (SmarterHOME CZ).
Everything that used to be a database-wide parameter is therefore the
company's; the migration to 19.0.1.4.0 carried the former values over.
"""

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    peppol_send_enabled = fields.Boolean(
        string="Allow e-invoicing via Peppol",
        help="A permission for this company, not a routing decision: it says "
        "e-invoicing MAY be used, never that a given invoice will be. Which "
        "documents actually leave through Peppol is decided per contact, by "
        "'Invoice sending' on the contact, and for contacts that state no "
        "preference by the Peppol scope below.\n\n"
        "Off: no customer invoice or credit note of this company ever goes out "
        "through Peppol, whatever a contact is set to — the invoice says so on "
        "its Peppol badge. Receiving vendor bills is unaffected; that is the "
        "provider's inbound poll, not this.")
    peppol_scope = fields.Selection(
        [("sk_mandate", "Slovak mandate: domestic B2B and B2G only"),
         ("addressable", "Any customer with a Peppol address")],
        string="Peppol scope",
        default="addressable",
        help="Slovak mandate: a document goes through Peppol only when both "
        "parties are Slovak and the customer is a business or a public body; "
        "consumers, Czech and other foreign customers get the PDF.")
    peppol_auto_send = fields.Boolean(
        string="Auto-send Peppol on Invoice Post",
        help="Every posted customer document routed to Peppol is generated "
        "and queued at once. Off: use the 'Send via Peppol' button.")
    peppol_purchase_journal_id = fields.Many2one(
        "account.journal",
        string="Peppol Purchase Journal",
        domain="[('type', '=', 'purchase'), ('company_id', '=', id)]",
        help="Journal for inbound Peppol vendor bills. Empty: the company's "
        "first purchase journal.")
