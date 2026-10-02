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
    cssk_vat_deregistration = fields.Char(
        string="VAT Deregistration Listing", readonly=True, copy=False,
        help="Set when the supplier was on the tax authority's list of VAT "
        "payers with grounds for cancelling their registration at the time "
        "of the check.",
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
        vals, warnings = partner._cssk_reliability_verdict(self.partner_bank_id)
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

    def _cron_cssk_recheck_open_bills(self, stale_days=7, limit=200):
        """Re-check unpaid vendor bills whose last check is stale.

        A supplier can become unreliable, or drop the account it registered,
        between the bill and its payment — and the payment is what the
        liability attaches to. So bills still waiting to be paid are checked
        again on a schedule, not only once when posted.
        """
        cutoff = fields.Datetime.subtract(fields.Datetime.now(), days=stale_days)
        companies = self.env["res.company"].search([
            ("cssk_reliability_autocheck", "=", True),
            ("account_fiscal_country_id.code", "in", ("SK", "CZ")),
        ])
        if not companies:
            return
        bills = self.search([
            ("company_id", "in", companies.ids),
            ("move_type", "in", ("in_invoice", "in_refund")),
            ("state", "=", "posted"),
            ("payment_state", "in", ("not_paid", "partial")),
            "|",
            ("cssk_reliability_checked_on", "=", False),
            ("cssk_reliability_checked_on", "<", cutoff),
        ], limit=limit, order="cssk_reliability_checked_on asc nulls first, id")
        for bill in bills:
            try:
                with self.env.cr.savepoint():
                    bill.with_company(bill.company_id)._cssk_run_reliability_check()
            except Exception:  # one register hiccup must not stop the batch
                _logger.exception(
                    "Scheduled supplier reliability check failed for %s",
                    bill.name,
                )
            if not self.env["ir.cron"]._commit_progress(1):
                return

    def _post(self, soft=True):
        moves = super()._post(soft=soft)
        for move in moves:
            if (
                move._cssk_is_reliability_relevant()
                and move.company_id.cssk_reliability_autocheck
            ):
                # In a savepoint, so a database error inside the check cannot
                # leave the cursor aborted under a successful post.
                try:
                    with self.env.cr.savepoint():
                        move._cssk_run_reliability_check()
                except Exception:  # never block posting on a register hiccup
                    _logger.exception(
                        "Supplier reliability check failed for %s", move.name
                    )
        return moves
