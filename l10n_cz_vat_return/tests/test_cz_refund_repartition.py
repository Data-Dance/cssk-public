# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCzRefundRepartitionAccounts(AccountTestInvoicingCommon):
    """The refund side of a reverse charge must name the same tax accounts.

    ``l10n_cz`` names both legs on the INVOICE repartition of its four
    reverse-charge purchase taxes and only the deductible leg on the REFUND
    one. A credit note's self-assessed leg then has no tax account and Odoo
    leaves the amount on the base line's account.

    Measured on a seven-year Czech import: 64 reverse-charge corrections left
    **289,031.99** on účet 395000, an internal clearing account that nets to
    zero in the source. The VAT return and the control statement both agreed
    throughout — they read tags, and the tags were right — so the account
    balance was the only witness.
    """

    chart_template = "cz"

    def _tax_legs(self, tax, refund=False):
        reps = (tax.refund_repartition_line_ids if refund
                else tax.invoice_repartition_line_ids)
        return reps.filtered(lambda r: r.repartition_type == "tax")

    def test_no_refund_leg_loses_the_account_its_invoice_leg_names(self):
        """Asserted over the whole chart, not the four known xmlids.

        Historical rate clones inherit the repartition of whatever they were
        cloned from, so a fix aimed at four ids would leave every pre-2024
        Czech rate broken — and a history import is the one job that uses them.
        """
        taxes = self.env["account.tax"].with_context(active_test=False).search(
            [("company_id", "=", self.env.company.id)])
        self.assertTrue(taxes, "the CZ chart must be loaded for this test")
        offenders = []
        for tax in taxes:
            invoice = {leg.factor_percent: leg.account_id
                       for leg in self._tax_legs(tax) if leg.account_id}
            for leg in self._tax_legs(tax, refund=True):
                if not leg.account_id and invoice.get(leg.factor_percent):
                    offenders.append((tax.name, leg.factor_percent))
        self.assertFalse(
            offenders,
            "a refund leg with no account leaves its VAT on the base "
            "account: %s" % offenders[:6])

    def test_the_repair_is_idempotent_and_invents_no_account(self):
        """It copies the invoice side and nothing else.

        A refund leg whose invoice counterpart names no account either is left
        alone — ``0% EU S`` is that shape in reverse and posts 100 % of a zero
        rate, so there is nothing to move and no intent to read.
        """
        company = self.env.company
        self.assertEqual(
            company._cz_fix_refund_repartition_accounts(), 0,
            "a second pass must find nothing left to fix")
        tax = self.env["account.tax"].with_context(active_test=False).search(
            [("company_id", "=", company.id),
             ("refund_repartition_line_ids.account_id", "=", False)], limit=1)
        if tax:
            bare = self._tax_legs(tax, refund=True).filtered(
                lambda r: not r.account_id)
            invoice = {leg.factor_percent for leg in self._tax_legs(tax)
                       if leg.account_id}
            self.assertFalse(
                {leg.factor_percent for leg in bare} & invoice,
                "anything still bare must have no invoice counterpart to copy")
