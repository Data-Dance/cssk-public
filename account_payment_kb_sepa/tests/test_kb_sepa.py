# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

NS = {"p": "urn:iso:std:iso:20022:tech:xsd:pain.001.001.03"}


@tagged("post_install", "-at_install")
class TestKbSepa(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids += cls.env.ref(
            "account_payment_order.group_account_payment")
        cls.eur = cls.env.ref("base.EUR")
        cls.eur.active = True
        czech = cls.env.ref("base.cz")
        germany = cls.env.ref("base.de")
        cls.company_data["company"].partner_id.write({
            "street": "Na Příkopě 33", "city": "Praha", "zip": "114 07",
            "country_id": czech.id,
        })
        kb = cls.env["res.bank"].create({
            "name": "Komerční banka", "bic": "KOMBCZPPXXX", "country": czech.id})
        cls.kb_account = cls.env["res.partner.bank"].create({
            "acc_number": "CZ5901000900930669910217", "bank_id": kb.id,
            "partner_id": cls.company_data["company"].partner_id.id,
        })
        cls.journal = cls.env["account.journal"].create({
            "name": "KB EUR", "code": "KBEU", "type": "bank",
            "bank_account_id": cls.kb_account.id, "currency_id": cls.eur.id,
        })
        commerz = cls.env["res.bank"].create({
            "name": "Commerzbank", "bic": "COBADEFFXXX", "country": germany.id})
        cls.creditor = cls.env["res.partner"].create({
            "name": "Lieferant Müller GmbH", "street": "Sandstraße 55",
            "zip": "80335", "city": "München", "country_id": germany.id,
        })
        cls.creditor_bank = cls.env["res.partner.bank"].create({
            "acc_number": "DE89370400440532013000", "bank_id": commerz.id,
            "partner_id": cls.creditor.id, "allow_out_payment": True,
        })
        cls.method = cls.env.ref(
            "account_banking_sepa_credit_transfer.sepa_credit_transfer")
        cls.method.convert_to_ascii = False  # KB forces it regardless

    def _xml(self, journal=None):
        journal = journal or self.journal
        mode = self.env["account.payment.mode"].create({
            "name": "SEPA", "payment_method_id": self.method.id,
            "bank_account_link": "fixed", "fixed_journal_id": journal.id,
        })
        order = self.env["account.payment.order"].create({
            "payment_mode_id": mode.id, "payment_type": "outbound",
            "journal_id": journal.id,
        })
        self.env["account.payment.line"].create({
            "order_id": order.id, "partner_id": self.creditor.id,
            "partner_bank_id": self.creditor_bank.id,
            "currency_id": self.eur.id, "amount_currency": 41.0,
            "communication": "Rechnung 77",
        })
        order.draft2open()
        # the OCA generator validates against the pain.001.001.03 XSD itself
        data, _name = order.generate_payment_file()
        return etree.fromstring(data)

    def test_structured_creditor_address(self):
        root = self._xml()
        address = root.find(".//p:Cdtr/p:PstlAdr", NS)
        tags = [etree.QName(child).localname for child in address]
        self.assertEqual(tags, ["StrtNm", "PstCd", "TwnNm", "Ctry"])
        self.assertEqual(address.find("p:TwnNm", NS).text, "Munchen")
        self.assertEqual(address.find("p:StrtNm", NS).text, "Sandstrasse 55")
        self.assertIsNone(address.find("p:AdrLine", NS))
        # SWIFT character set, whatever the payment method says
        self.assertEqual(root.find(".//p:Cdtr/p:Nm", NS).text,
                         "Lieferant Muller GmbH")
        self.assertEqual(root.find(".//p:ChrgBr", NS).text, "SLEV")
        self.assertEqual(root.find(".//p:SvcLvl/p:Cd", NS).text, "SEPA")

    def test_no_town_no_address(self):
        """Any address element makes town and country mandatory at KB."""
        self.creditor.city = False
        root = self._xml()
        self.assertIsNone(root.find(".//p:Cdtr/p:PstlAdr", NS))

    def test_other_bank_untouched(self):
        cs = self.env["res.partner.bank"].create({
            "acc_number": "CZ6508000000192000145399",
            "partner_id": self.company_data["company"].partner_id.id,
            "bank_id": self.env["res.bank"].create({
                "name": "Česká spořitelna", "bic": "GIBACZPXXXX"}).id,
        })
        journal = self.env["account.journal"].create({
            "name": "CS EUR", "code": "CSEU", "type": "bank",
            "bank_account_id": cs.id, "currency_id": self.eur.id,
        })
        root = self._xml(journal)
        address = root.find(".//p:Cdtr/p:PstlAdr", NS)
        # OCA's own pain.001.001.03 address: country + address lines
        self.assertIsNotNone(address.find("p:AdrLine", NS))
        self.assertIsNone(address.find("p:TwnNm", NS))
