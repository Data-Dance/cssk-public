# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

METHOD = "skpaybysquare_qr"


@tagged("post_install", "-at_install")
class TestQrMethodPreference(AccountTestInvoicingCommon):
    """PAY by square must not win the automatic choice outside Slovakia.

    It, payme and core's SEPA QR all sit at sequence 20 and all accept any
    EUR SEPA IBAN, so the winner fell to module load order and a Czech
    company's EUR invoice to a German customer printed a Slovak code.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.eur = cls.env.ref("base.EUR")
        cls.eur.active = True
        cls.holder = cls.env["res.partner"].create({
            "name": "Issuer", "country_id": cls.env.ref("base.sk").id})
        cls.bank = cls.env["res.partner.bank"].create({
            "acc_number": "SK3112000000198742637541",
            "partner_id": cls.holder.id,
        })
        cls.sk_debtor = cls.env["res.partner"].create({
            "name": "SK debtor", "country_id": cls.env.ref("base.sk").id})
        cls.de_debtor = cls.env["res.partner"].create({
            "name": "DE debtor", "country_id": cls.env.ref("base.de").id})

    def _auto(self, debtor):
        vals = self.bank._build_qr_code_vals(
            10.0, "INV/1", "INV/1", self.eur, debtor)
        return vals and vals["qr_method"]

    def test_slovak_parties_keep_pay_by_square_eligible(self):
        self.assertTrue(self.bank._qr_method_suits(METHOD, self.sk_debtor))
        self.assertTrue(self.bank._qr_method_suits(
            METHOD, self.env["res.partner"]))

    def test_foreign_debtor_is_not_given_pay_by_square(self):
        self.assertFalse(self.bank._qr_method_suits(METHOD, self.de_debtor))
        self.assertNotEqual(self._auto(self.de_debtor), METHOD)

    def test_foreign_issuer_is_not_given_pay_by_square(self):
        self.holder.country_id = self.env.ref("base.cz")
        self.assertFalse(self.bank._qr_method_suits(METHOD, self.sk_debtor))
        self.assertNotEqual(self._auto(self.de_debtor), METHOD)

    def test_explicit_choice_is_honoured(self):
        vals = self.bank._build_qr_code_vals(
            10.0, "INV/1", "INV/1", self.eur, self.de_debtor, qr_method=METHOD)
        self.assertEqual(vals and vals["qr_method"], METHOD)

    def test_nothing_preferred_falls_back_to_core(self):
        # With every candidate held back the code is still produced.
        self.patch(type(self.bank), "_qr_method_suits", lambda *a: False)
        self.assertTrue(self._auto(self.de_debtor))
