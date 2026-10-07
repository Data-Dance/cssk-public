# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SkEkasaCall(models.Model):
    """One call to the document-verification service.

    Two jobs. It is the hourly budget counter — the service permits about 60
    lookups per clock hour per IP address and blocks the address beyond that.
    And it is the local record of what was verified, which is the only evidence
    a company has of its own compliance with § 18 ods. 11's duty to send
    truthful verification results.
    """

    _name = "sk.ekasa.call"
    _description = "eKasa Verification Call"
    _order = "create_date desc, id desc"
    _rec_name = "request_key"

    company_id = fields.Many2one(
        "res.company", required=True, index=True,
        default=lambda s: s.env.company)
    receipt_id = fields.Many2one(
        "cssk.receipt", ondelete="set null", index=True)
    request_key = fields.Char(
        required=True,
        help="The identifier or composite key the service was asked about.")
    called_at = fields.Datetime(
        required=True, default=fields.Datetime.now, index=True)
    outcome = fields.Selection(
        [
            ("found", "Receipt found"),
            ("not_found", "Not registered"),
            ("refused", "Refused by the service"),
            ("transport", "Network or transport error"),
        ],
        required=True, index=True)
    http_status = fields.Integer()
    return_value = fields.Integer(
        help="The service's own returnValue field.")
    message = fields.Text()

    @api.model
    def _hour_start(self, now=None):
        now = now or fields.Datetime.now()
        return now.replace(minute=0, second=0, microsecond=0)

    @api.model
    def _used_this_hour(self, company):
        """Calls already made in the current clock hour.

        The service's window is the clock hour (hh:00 to hh:59), not a rolling
        sixty minutes, so the count resets on the hour.
        """
        return self.search_count([
            ("company_id", "=", company.id),
            ("called_at", ">=", fields.Datetime.to_string(self._hour_start())),
        ])

    @api.model
    def _check_budget(self, company):
        """Raise unless there is budget left in this clock hour.

        A budget of zero means no lookups, not "use the default": writing
        ``or 60`` here made setting the limit to 0 silently grant 60. Existing
        companies are given the default by this module's post-install hook, so
        a zero in the field is always deliberate.
        """
        budget = company.l10n_sk_ekasa_hourly_budget
        if budget <= 0:
            raise UserError(_(
                "The hourly eKasa lookup budget for %(company)s is set to "
                "zero, so no lookups are made. Raise it in Settings ▸ "
                "Accounting ▸ Fiscal Receipt Capture.",
                company=company.display_name))
        used = self._used_this_hour(company)
        if used >= budget:
            raise UserError(_(
                "The hourly eKasa lookup budget for %(company)s is spent "
                "(%(used)s of %(budget)s used since %(since)s). Finančná "
                "správa limits the service to roughly 60 lookups per clock "
                "hour per IP address and blocks the address beyond that, so "
                "the remaining receipts have to wait for the next hour.",
                company=company.display_name, used=used, budget=budget,
                since=fields.Datetime.to_string(self._hour_start())[-8:-3]))
        return budget - used
