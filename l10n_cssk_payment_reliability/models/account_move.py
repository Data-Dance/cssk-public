# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from markupsafe import Markup

from odoo import _, fields, models

from .res_partner import CSSK_RELIABILITY

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    cssk_reliability_checked_on = fields.Datetime(
        string="Reliability Checked On", readonly=True, copy=False
    )
    cssk_bank_acc_status = fields.Selection(
        [
            ("registered", "Paid account is registered"),
            ("not_registered", "Paid account NOT registered"),
            ("no_account", "No bank account set"),
            ("unknown", "Not checked / unavailable"),
        ],
        string="Bank Account Check",
        readonly=True,
        copy=False,
    )
    cssk_supplier_reliability = fields.Selection(
        CSSK_RELIABILITY, string="Supplier Reliability", readonly=True, copy=False
    )
    cssk_registered_accounts = fields.Char(
        string="Registered Accounts (at check)", readonly=True, copy=False
    )
    cssk_reliability_warning = fields.Text(
        string="Reliability Warning", readonly=True, copy=False
    )
    cssk_reliability_alert = fields.Boolean(
        compute="_compute_cssk_reliability_alert"
    )

    def _compute_cssk_reliability_alert(self):
        for move in self:
            move.cssk_reliability_alert = bool(move.cssk_reliability_warning)

    # ------------------------------------------------------------------
    def _cssk_is_reliability_relevant(self):
        self.ensure_one()
        return (
            self.move_type in ("in_invoice", "in_refund")
            and self.company_id.account_fiscal_country_id.code in ("SK", "CZ")
        )

    def action_cssk_check_reliability(self):
        for move in self.filtered(lambda m: m._cssk_is_reliability_relevant()):
            move._cssk_run_reliability_check()
        return True

    def _cssk_run_reliability_check(self):
        """Look up the supplier's registered accounts + reliability and store
        a point-in-time snapshot on the bill. Warns; never blocks."""
        self.ensure_one()
        partner = self.partner_id.commercial_partner_id
        # One provider query per check (CZ ADIS answers both in one response).
        accounts, reliability = partner._cssk_get_reliability_data()

        vals = {"cssk_reliability_checked_on": fields.Datetime.now()}
        warnings = []

        if accounts is None:
            vals["cssk_bank_acc_status"] = "unknown"
            vals["cssk_registered_accounts"] = False
        else:
            vals["cssk_registered_accounts"] = ", ".join(accounts) or False
            paid = self.partner_bank_id.sanitized_acc_number
            if not paid:
                vals["cssk_bank_acc_status"] = "no_account"
            elif paid in accounts:
                vals["cssk_bank_acc_status"] = "registered"
            else:
                vals["cssk_bank_acc_status"] = "not_registered"
                warnings.append(
                    _(
                        "The bank account %s is NOT among the accounts the "
                        "supplier registered with the tax authority. Paying an "
                        "unregistered account can make you liable for the "
                        "supplier's unpaid VAT (§69 ods. 14 SK / §109 CZ); you "
                        "may instead remit the VAT directly to the tax office."
                    )
                    % paid
                )

        if reliability is not None:
            vals["cssk_supplier_reliability"] = reliability
            if reliability in ("less_reliable", "unreliable"):
                label = dict(CSSK_RELIABILITY).get(reliability, reliability)
                warnings.append(
                    _("The supplier's tax-reliability rating is '%s'.") % label
                )

        vals["cssk_reliability_warning"] = "\n".join(warnings) or False
        self.write(vals)
        if warnings:
            # ``Markup.join`` escapes each non-Markup part, which matters:
            # a warning carries a supplier name straight from the register.
            self.message_post(
                body=Markup("<br/>").join(
                    [_("⚠ Supplier reliability check:")] + warnings
                )
            )
        return True

    def _post(self, soft=True):
        moves = super()._post(soft=soft)
        for move in moves:
            if (
                move._cssk_is_reliability_relevant()
                and move.company_id.cssk_reliability_autocheck
            ):
                try:
                    move._cssk_run_reliability_check()
                except Exception:  # never block posting on a register hiccup
                    _logger.exception(
                        "Supplier reliability check failed for %s", move.name
                    )
        return moves
