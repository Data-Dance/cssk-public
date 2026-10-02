# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CsskViesCheck(models.Model):
    """One VIES consultation, as a company made it.

    The proof of an intra-Community exemption check is the consultation
    number VIES gives a *requester*, so it belongs to the company that asked,
    not to the partner. Kept on the partner it was overwritten by whichever
    company checked last, and a check left no trace once the next one ran.
    A fault is logged too: it is evidence the check was attempted.
    """

    _name = "cssk.vies.check"
    _description = "VIES check"
    _order = "check_date desc, id desc"
    _rec_name = "consultation_number"

    partner_id = fields.Many2one(
        "res.partner", required=True, index=True, ondelete="cascade",
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company", index=True, readonly=True,
        help="The company that asked. Empty on checks migrated from before "
        "checks were logged per company, when the requester was not recorded.",
    )
    requester_vat = fields.Char(readonly=True)
    vat = fields.Char(string="Checked VAT", readonly=True)
    check_date = fields.Datetime(
        required=True, default=fields.Datetime.now, readonly=True, index=True,
    )
    result = fields.Selection(
        [("valid", "Valid"), ("invalid", "Invalid"),
         ("fault", "No answer")],
        required=True, readonly=True,
    )
    consultation_number = fields.Char(readonly=True)
    request_date = fields.Date(
        readonly=True, help="The date VIES reports for the consultation.")
    trader_name = fields.Char(string="Registered Name", readonly=True)
    address = fields.Char(string="Registered Address", readonly=True)
    name_match = fields.Char(readonly=True)
    fault_reason = fields.Char(readonly=True)
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, readonly=True)
