# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from markupsafe import Markup

from odoo import _, fields, models

from .res_partner import CSSK_RELIABILITY

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    """The same check as on the vendor bill, at the moment that matters.

    The liability for a supplier's unpaid VAT (§69 ods. 14 SK / §109 CZ)
    attaches to *paying* an unregistered account, and weeks can pass between
    the bill and the payment. So an outbound supplier payment is checked again
    when it is posted, against the account it actually pays. Warns; never
    blocks, like the bill check.
    """

    _inherit = "account.payment"

    cssk_reliability_checked_on = fields.Datetime(
        string="Reliability Checked On", readonly=True, copy=False)
    cssk_bank_acc_status = fields.Selection(
        [
            ("registered", "Paid account is registered"),
            ("not_registered", "Paid account NOT registered"),
            ("no_account", "No bank account set"),
            ("unknown", "Not checked / unavailable"),
        ],
        string="Bank Account Check", readonly=True, copy=False,
    )
    cssk_supplier_reliability = fields.Selection(
        CSSK_RELIABILITY, string="Supplier Reliability", readonly=True,
        copy=False)
    cssk_registered_accounts = fields.Char(
        string="Registered Accounts (at check)", readonly=True, copy=False)
    cssk_vat_deregistration = fields.Char(
        string="VAT Deregistration Listing", readonly=True, copy=False)
    cssk_reliability_warning = fields.Text(
        string="Reliability Warning", readonly=True, copy=False)

    def _cssk_is_reliability_relevant(self):
        self.ensure_one()
        return (
            self.payment_type == "outbound"
            and self.partner_type == "supplier"
            and bool(self.partner_id)
            and self.company_id.account_fiscal_country_id.code in ("SK", "CZ")
        )

    def action_cssk_check_reliability(self):
        for payment in self.filtered(lambda p: p._cssk_is_reliability_relevant()):
            payment._cssk_run_reliability_check()
        return True

    def _cssk_run_reliability_check(self):
        self.ensure_one()
        partner = self.partner_id.commercial_partner_id
        vals, warnings = partner._cssk_reliability_verdict(self.partner_bank_id)
        vals["cssk_reliability_warning"] = "\n".join(warnings) or False
        self.write(vals)
        if warnings:
            self.message_post(
                body=Markup("<br/>").join(
                    [_("⚠ Supplier reliability check at payment:")] + warnings
                )
            )
        return True

    def action_post(self):
        res = super().action_post()
        for payment in self:
            if (
                payment.state != "draft"
                and payment._cssk_is_reliability_relevant()
                and payment.company_id.cssk_reliability_autocheck
            ):
                # The savepoint matters: swallowing a database error without
                # one would leave the cursor aborted, and the payment would
                # fail later, somewhere unrelated.
                try:
                    with self.env.cr.savepoint():
                        payment._cssk_run_reliability_check()
                except Exception:  # never block a payment on a register hiccup
                    _logger.exception(
                        "Supplier reliability check failed for payment %s",
                        payment.name,
                    )
        return res
