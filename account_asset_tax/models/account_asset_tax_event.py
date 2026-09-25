from odoo import fields, models


class AccountAssetTaxEvent(models.Model):
    """A lifecycle event that reshapes the tax-depreciation board.

    Events are persisted and replayed every time the board is recomputed, so a
    recompute is idempotent: the clean statutory schedule is laid out first, then
    each event (in date order) folds in its effect.

    As with :class:`account.asset.tax.line`, the ``asset_id`` relation is added
    by the bridge so the core stays independent of the asset implementation.
    """

    _name = "account.asset.tax.event"
    _description = "Tax Depreciation Event"
    _order = "company_id, date, id"

    company_id = fields.Many2one(
        "res.company", required=True, index=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(related="company_id.currency_id")

    event_type = fields.Selection(
        [
            ("improvement", "Technical Improvement (TZ)"),
            ("suspension", "Suspension / Interruption"),
            ("disposal", "Disposal"),
        ],
        required=True,
    )
    date = fields.Date(required=True)
    amount = fields.Monetary(
        help="Technical-improvement amount (for improvement events). Ignored for "
        "suspension and disposal.",
    )
    duration_years = fields.Integer(
        string="Years",
        default=1,
        help="Number of whole tax periods to suspend (suspension events).",
    )
    note = fields.Char()
