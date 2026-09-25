# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Warn when a document's counterparty is no longer in the register.

Both directions matter, for different reasons. Invoicing a company that was
struck off means invoicing something that cannot pay or be pursued. Taking a
vendor bill from one is worse: a supplier that did not exist on the supply date
puts the deduction itself in question.

Non-blocking, like every other register check in this repository. Documents get
booked for dissolved subjects all the time — a final invoice, a late credit
note, a bill that arrives after the counterparty wound up. The date on the
document, not the register's state today, decides whether that is legitimate,
and only a person can weigh that.
"""

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_sk_register_warning = fields.Text(
        string="SK register warning",
        compute="_compute_l10n_sk_register_warning",
        help="Raised when the register shows the counterparty as dissolved, "
        "deleted or suspended.",
    )

    @api.depends(
        "move_type",
        "company_id",
        "partner_id",
        "partner_id.l10n_sk_register_inactive",
        "partner_id.l10n_sk_register_status",
        "partner_id.l10n_sk_dissolved_on",
    )
    def _compute_l10n_sk_register_warning(self):
        for move in self:
            move.l10n_sk_register_warning = False
            if not move.is_invoice(include_receipts=True):
                continue
            if move.company_id.account_fiscal_country_id.code != "SK":
                continue
            partner = move.partner_id.commercial_partner_id
            if not partner.l10n_sk_register_inactive:
                continue
            warning = partner._l10n_sk_register_warning()
            if not warning:
                continue
            if move.is_purchase_document(include_receipts=True):
                warning += (
                    " Doklad od subjektu, ktorý v čase dodania nemusel "
                    "existovať — overte nárok na odpočítanie dane."
                )
            move.l10n_sk_register_warning = warning

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        for move in posted:
            if move.l10n_sk_register_warning:
                move.message_post(body=move.l10n_sk_register_warning)
        return posted
