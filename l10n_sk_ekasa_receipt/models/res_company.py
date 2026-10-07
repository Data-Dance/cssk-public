# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_sk_ekasa_enabled = fields.Boolean(
        string="eKasa Receipt Lookup",
        help="Fetch registered receipts from Finančná správa's "
             "document-verification service when a receipt's QR code is known.")
    # § 18 ods. 11 of act 384/2025 Z. z.: before first use an overovateľ must
    # notify Finančná správa of the address it will call from. There is no way
    # for software to verify that this was done, so it is declared here and the
    # declaration gates the lookup — which at least makes the obligation
    # visible to whoever switches the feature on.
    l10n_sk_ekasa_ip_notified = fields.Boolean(
        string="IP Address Notified (§ 18/11)",
        help="Tick once Finančná správa has been notified of the IP address "
             "this database calls the verification service from, as act "
             "384/2025 Z. z. § 18 ods. 11 requires of an overovateľ.")
    l10n_sk_ekasa_ip_address = fields.Char(
        string="Notified IP Address",
        help="The address declared to Finančná správa. Recorded here so the "
             "declaration can be checked against the egress address actually "
             "in use.")
    l10n_sk_ekasa_ip_notified_on = fields.Date(string="Notified On")
    l10n_sk_ekasa_hourly_budget = fields.Integer(
        string="Hourly Lookup Budget", default=60,
        help="Maximum lookups per clock hour. The service permits roughly 60 "
             "per hour per IP address and blocks the address beyond that, so "
             "this module refuses to exceed the budget rather than lose "
             "access. Note the real limit is per address: several companies "
             "sharing one egress address share one budget.")
    l10n_sk_ekasa_timeout = fields.Integer(
        string="Lookup Timeout (s)", default=30)

    def _l10n_sk_ekasa_check_ready(self):
        """Raise unless this company may call the verification service."""
        self.ensure_one()
        if not self.l10n_sk_ekasa_enabled:
            raise UserError(_(
                "The eKasa receipt lookup is switched off for %s. Enable it in "
                "Settings ▸ Accounting ▸ Fiscal Receipt Capture.",
                self.display_name))
        if not self.l10n_sk_ekasa_ip_notified:
            raise UserError(_(
                "Act 384/2025 Z. z. § 18 ods. 11 requires an overovateľ to "
                "notify Finančná správa of the IP address it will use before "
                "calling the document-verification service, and to send "
                "truthful verification results. Confirm the notification in "
                "Settings ▸ Accounting ▸ Fiscal Receipt Capture before using "
                "the lookup.\n\n"
                "Finančná správa had not yet published the conditions of use "
                "for this service when this module was written; until it does, "
                "satisfying the obligation means contacting them directly."))
        return True
