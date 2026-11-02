# -*- coding: utf-8 -*-
"""Gift cards and eWallets are "prostředky k platbě v omezené síti" (§ 5 odst. 1
písm. e) ZoET). Both the top-up and every redemption are evidenced sales when
made at the till (§ 4 odst. 2; FS answers 585 and 584; item methodology ch. 13–14):

* top-up of 1 000 Kč plus a 50 Kč drink paid cash -> celk_trzba 1050,
  urceno_cerp_zuct 1000;
* later redemption of 300 Kč -> celk_trzba 300, cerp_zuct 300.

Odoo books a redemption as a negative reward line, so ``amount_total`` is only
what was paid on top. The total reported to EET is widened by the redeemed
amount, and an order settled entirely by a card/wallet, which has no payment
line at all, is still in scope.

A POS refund flips every line, so a refunded redemption comes out as
``celk_trzba`` -X / ``cerp_zuct`` -X, which is exactly the storno form the
item methodology prescribes (ch. 14, example 3: -121.00 / -121.00).
"""
from odoo import models

PAYMENT_PROGRAMS = ("gift_card", "ewallet")


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _l10n_cz_eet2_payment_products(self):
        """Products whose sale loads a gift card or eWallet, for this company.

        Looked up across every gift-card / eWallet program of the company,
        archived or expired ones included: a resend or a late sync must
        classify the line the way it was sold, not the way the catalogue
        looks today.
        """
        self.ensure_one()
        programs = self.env["loyalty.program"].sudo().with_context(
            active_test=False).search([
                ("program_type", "in", PAYMENT_PROGRAMS),
                ("company_id", "in", [False, self.company_id.id]),
            ])
        return programs.rule_ids.product_ids

    def _l10n_cz_eet2_topup_lines(self):
        """Lines that load value onto a gift card or eWallet."""
        self.ensure_one()
        products = self._l10n_cz_eet2_payment_products()
        return self.lines.filtered(
            lambda l: not l.is_reward_line and l.product_id in products)

    def _l10n_cz_eet2_redemption_lines(self):
        """Negative reward lines that spend gift-card or eWallet value."""
        self.ensure_one()
        return self.lines.filtered(
            lambda l: l.is_reward_line
            and l.reward_id.program_id.program_type in PAYMENT_PROGRAMS)

    def _l10n_cz_eet2_amounts(self):
        amounts = super()._l10n_cz_eet2_amounts()
        topup = sum(self._l10n_cz_eet2_topup_lines().mapped("price_subtotal_incl"))
        redeemed = -sum(self._l10n_cz_eet2_redemption_lines().mapped("price_subtotal_incl"))
        amounts["urceno_cerp_zuct"] += topup
        amounts["cerp_zuct"] += redeemed
        # The drawdown is a payment in its own right: add it back to the total
        # that Odoo already reduced by the reward line.
        amounts["celk_trzba"] += redeemed
        return amounts

    def _l10n_cz_eet2_in_scope(self):
        if super()._l10n_cz_eet2_in_scope():
            return True
        company = self.company_id
        if not company.l10n_cz_eet2_enabled or not company.l10n_cz_eet2_eic_popl:
            return False
        # Paid entirely with a card/wallet: no payment line, still a contact
        # drawdown that must be recorded.
        return bool(self._l10n_cz_eet2_redemption_lines())
