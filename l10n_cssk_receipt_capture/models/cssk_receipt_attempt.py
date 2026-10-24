# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class CSSKReceiptAttempt(models.Model):
    """One attempt to read a receipt, by one provider.

    The receipt itself only ever shows the latest reading, so before this a
    retry overwrote what the previous attempt had cost and why it had failed —
    and a failure in the Expenses upload left no trace a user could find. This
    is the history: written by ``cssk.receipt.action_capture`` itself, never by
    a provider, so no provider can forget to.

    It is not the eKasa call ledger (``sk.ekasa.call``), which records each
    network call to Finančná správa for § 18 ods. 11 and the hourly budget —
    one attempt can make several of those, and a scan makes none of these.
    """

    _name = "cssk.receipt.attempt"
    _description = "Fiscal Receipt Capture Attempt"
    _order = "started_at desc, id desc"

    receipt_id = fields.Many2one(
        "cssk.receipt", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="receipt_id.company_id", store=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    provider_id = fields.Many2one("cssk.receipt.provider", string="Provider")
    started_at = fields.Datetime(required=True, default=fields.Datetime.now)
    duration_ms = fields.Integer(string="Duration (ms)")
    outcome = fields.Selection(
        [
            ("captured", "Captured"),
            ("review", "Needs review"),
            ("error", "Failed"),
            ("unavailable", "Not available"),
        ],
        required=True)
    message = fields.Text(
        help="Why it failed, or what the reconciliation gates found.")
    transient = fields.Boolean(
        help="The failure is worth retrying unchanged later — a busy model or a "
             "network error. A refusal is not, and is never retried on a timer.")
    model_label = fields.Char(
        string="Model", help="The model that served an AI reading, if any.")
    input_tokens = fields.Integer()
    output_tokens = fields.Integer()
    cost = fields.Float(
        digits=(16, 6),
        help="What the call cost, including a call that produced nothing usable.")
    confidence = fields.Float(digits=(16, 2))
