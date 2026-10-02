# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""BEST builders and statement parser, against KB's published layout."""

from datetime import date, timedelta

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.account_cz_bankfile_base.utils.common import BankPaymentItem
from odoo.addons.account_kb_best_base.utils.best import (
    build_best_domestic,
    build_best_foreign,
    is_best_statement,
    parse_best_statement,
    sequence_no,
)

from . import best_fixtures as f

# domestic 01 record offsets (spec 2.1.2)
D01 = {
    "seq": (2, 5), "created": (7, 8), "due": (15, 8), "currency": (23, 3),
    "amount": (26, 15), "operation": (41, 1), "counter_currency": (42, 3),
    "conversion": (45, 1), "ks": (46, 10), "av": (56, 140), "bank": (199, 4),
    "account": (203, 16), "description": (239, 30), "partner_bank": (272, 4),
    "partner_account": (276, 16), "vs": (292, 10), "ss": (302, 10),
    "express": (342, 1), "forex": (343, 1),
}
# foreign 02 record offsets (spec 2.2.2)
F02 = {
    "seq": (8, 5), "created": (13, 8), "due": (21, 8), "currency": (29, 3),
    "amount": (32, 15), "charges": (47, 3), "express": (69, 1),
    "bank": (120, 4), "account": (124, 16), "payer_currency": (140, 3),
    "bic": (248, 35), "remittance": (423, 140), "slash": (563, 1),
    "iban": (564, 34), "beneficiary": (598, 140), "bank_address": (738, 140),
    "cheque": (878, 1), "sepa": (879, 1),
}


def field(record, spec, name):
    offset, width = spec[name]
    return record[offset:offset + width]


@tagged("post_install", "-at_install")
class TestBestBuilders(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = date(2026, 7, 1)
        cls.kb = cls.env["res.bank"].create({"name": "Komerční banka",
                                             "bic": "KOMBCZPP"})
        cls.company_bank = cls.env["res.partner.bank"].create({
            "acc_number": "90093-669910217/0100",
            "partner_id": cls.env.company.partner_id.id,
        })
        cls.supplier = cls.env["res.partner"].create({"name": "Dodavatel s.r.o."})
        cls.supplier_bank = cls.env["res.partner.bank"].create({
            "acc_number": "CZ5530000000000019012333",
            "partner_id": cls.supplier.id,
        })
        cls.germany = cls.env.ref("base.de")
        cls.usa = cls.env.ref("base.us")
        cls.deutsche = cls.env["res.bank"].create({
            "name": "Deutsche Bank", "bic": "DEUTDEMM", "country": cls.germany.id,
        })
        cls.foreign = cls.env["res.partner"].create({
            "name": "Lieferant GmbH", "street": "Hauptstraße 12",
            "city": "München", "zip": "80331", "country_id": cls.germany.id,
        })
        cls.foreign_bank = cls.env["res.partner.bank"].create({
            "acc_number": "DE89370400440532013000",
            "partner_id": cls.foreign.id,
            "bank_id": cls.deutsche.id,
        })

    def _item(self, **kwargs):
        vals = {
            "partner_bank": self.supplier_bank, "amount": 1234.5,
            "currency_name": "CZK", "vs": "20260042", "ks": "0308", "ss": "77",
            "message": "Faktura č. 2026/0042", "date": self.today,
            "label": "L1", "partner": self.supplier, "ref_id": 45,
        }
        vals.update(kwargs)
        return BankPaymentItem(**vals)

    def _records(self, data):
        text = data.decode("cp1250")
        self.assertTrue(text.endswith("\r\n"))
        return text[:-2].split("\r\n")

    # ------------------------------------------------------------ domestic
    def test_domestic_layout(self):
        data = build_best_domestic(
            self.company_bank, [self._item(), self._item(ref_id=46, amount=10)],
            "CZK", self.today, file_id="DAVKA1")
        records = self._records(data)
        self.assertEqual([len(r) for r in records], [351] * 4)
        header, first, _second, trailer = records
        self.assertEqual(header[:2], "HI")
        self.assertEqual(header[11:17], "260701")
        self.assertEqual(header[17:23], "DAVKA1")
        g = lambda name: field(first, D01, name)  # noqa: E731
        self.assertEqual(first[:2], "01")
        self.assertEqual(g("seq"), "00019")  # base 36 of line id 45
        self.assertEqual(g("created"), "20260701")
        self.assertEqual(g("currency"), "CZK")
        self.assertEqual(g("amount"), "000000000123450")
        self.assertEqual(g("operation"), "0")
        self.assertEqual(g("ks"), "0000000308")
        self.assertEqual(g("bank"), "0100")
        self.assertEqual(g("account"), "0900930669910217")
        self.assertEqual(g("partner_bank"), "3000")
        self.assertEqual(g("partner_account"), "0000000019012333")
        self.assertEqual(g("vs"), "0020260042")
        self.assertEqual(g("ss"), "0000000077")
        self.assertEqual(g("express"), "S")
        self.assertEqual(g("forex"), "N")
        # diacritics survive: BEST domestic is CP1250 and KB's sample has them
        self.assertTrue(g("av").startswith("Faktura č. 2026/0042"))
        # trailer: count and the sum of all amounts
        self.assertEqual(trailer[:2], "TI")
        self.assertEqual(trailer[17:23], "000002")
        self.assertEqual(trailer[23:41], "000000000000124450")

    def test_domestic_due_date_never_in_the_past(self):
        data = build_best_domestic(
            self.company_bank, [self._item(date=self.today - timedelta(days=3))],
            "CZK", self.today)
        self.assertEqual(field(self._records(data)[1], D01, "due"), "20260701")

    def test_domestic_direct_debit(self):
        data = build_best_domestic(self.company_bank, [self._item()], "CZK",
                                   self.today, batch_type="inbound")
        self.assertEqual(field(self._records(data)[1], D01, "operation"), "1")

    def test_domestic_urgent(self):
        data = build_best_domestic(self.company_bank,
                                   [self._item(iso_priority="URGP")], "CZK",
                                   self.today)
        self.assertEqual(field(self._records(data)[1], D01, "express"), "E")

    def test_domestic_conversion_flag(self):
        """A CZK payment from a EUR account: the amount is in the
        counter-account currency, flagged "P"."""
        data = build_best_domestic(self.company_bank, [self._item()], "EUR",
                                   self.today)
        record = self._records(data)[1]
        self.assertEqual(field(record, D01, "currency"), "EUR")
        self.assertEqual(field(record, D01, "counter_currency"), "CZK")
        self.assertEqual(field(record, D01, "conversion"), "P")

    def test_domestic_foreign_currency_outside_kb_refused(self):
        with self.assertRaisesRegex(UserError, "another KB account"):
            build_best_domestic(self.company_bank,
                                [self._item(currency_name="EUR")], "EUR",
                                self.today)

    def test_forbidden_constant_symbols(self):
        for ks in ("0005", "1151", "0006", "0007"):
            with self.subTest(ks=ks), self.assertRaisesRegex(UserError, ks):
                build_best_domestic(self.company_bank, [self._item(ks=ks)],
                                    "CZK", self.today)

    def test_account_must_be_at_kb(self):
        other = self.env["res.partner.bank"].create({
            "acc_number": "19-2000145399/0800",
            "partner_id": self.env.company.partner_id.id,
        })
        with self.assertRaisesRegex(UserError, "not a KB account"):
            build_best_domestic(other, [self._item()], "CZK", self.today)

    def test_sequence_numbers(self):
        self.assertEqual(sequence_no(self._item(ref_id=1), 9), "00001")
        self.assertEqual(sequence_no(self._item(ref_id=36 ** 2), 9), "00100")
        # no id: the position in the file
        self.assertEqual(sequence_no(self._item(ref_id=None), 9), "00009")

    # ------------------------------------------------------------- foreign
    def _foreign_item(self, **kwargs):
        vals = {"partner_bank": self.foreign_bank, "partner": self.foreign,
                "currency_name": "EUR", "amount": 41.0, "vs": "", "ks": "",
                "ss": "", "message": "Rechnung 77"}
        vals.update(kwargs)
        return self._item(**vals)

    def test_sepa_payment(self):
        data = build_best_foreign(self.company_bank,
                                  self.env.company.partner_id,
                                  [self._foreign_item()], "EUR", self.today)
        records = self._records(data)
        self.assertEqual([len(r) for r in records], [882] * 4)
        payment, address = records[1], records[2]
        g = lambda name: field(payment, F02, name)  # noqa: E731
        self.assertEqual(payment[:2], "02")
        self.assertEqual(g("currency"), "EUR")
        self.assertEqual(g("amount"), "000000000004100")
        self.assertEqual(g("charges"), "SLV")
        self.assertEqual(g("sepa"), "Y")
        self.assertEqual(g("express"), "E")
        self.assertEqual(g("bank"), "0100")
        self.assertEqual(g("account"), "0900930669910217")
        # an 8-character BIC is padded with three spaces for KB to fill
        self.assertEqual(g("bic"), "DEUTDEMM".ljust(35))
        self.assertEqual(g("slash"), "/")
        self.assertEqual(g("iban").strip(), "DE89370400440532013000")
        self.assertTrue(g("beneficiary").startswith("Lieferant GmbH"))
        # SWIFT character set only
        self.assertIn("Hauptstrasse 12", g("beneficiary"))
        self.assertIn("Munchen, 80331", g("beneficiary"))
        # 03 follows its 02 with the same sequence number
        self.assertEqual(address[:2], "03")
        self.assertEqual(address[8:13], g("seq"))
        self.assertEqual(address[255:290].strip(), "Munchen")
        self.assertEqual(address[325:327], "DE")
        # trailer counts 02 and 03 records
        self.assertEqual(records[3][17:23], "000002")

    def test_foreign_non_sepa_needs_full_address(self):
        partner = self.env["res.partner"].create({"name": "US Vendor"})
        bank = self.env["res.partner.bank"].create({
            "acc_number": "123456789", "partner_id": partner.id,
            "bank_id": self.env["res.bank"].create({
                "name": "Chase", "bic": "CHASUS33XXX",
                "country": self.usa.id}).id,
        })
        item = self._foreign_item(partner=partner, partner_bank=bank,
                                  currency_name="USD")
        with self.assertRaisesRegex(UserError, "name, street, city and country"):
            build_best_foreign(self.company_bank, self.env.company.partner_id,
                               [item], "CZK", self.today)
        partner.write({"street": "1 Main St", "city": "New York",
                       "zip": "10001", "country_id": self.usa.id})
        data = build_best_foreign(self.company_bank,
                                  self.env.company.partner_id, [item], "CZK",
                                  self.today)
        payment = self._records(data)[1]
        self.assertEqual(field(payment, F02, "sepa"), "N")
        self.assertEqual(field(payment, F02, "charges"), "SHA")
        self.assertEqual(field(payment, F02, "payer_currency"), "CZK")

    def test_eea_payment_only_with_shared_charges(self):
        with self.assertRaisesRegex(UserError, "only\\s+with shared charges"):
            build_best_foreign(
                self.company_bank, self.env.company.partner_id,
                [self._foreign_item(iso_charge_bearer="DEBT")], "EUR",
                self.today)

    def test_invalid_bic_refused(self):
        # past the ORM: account_payment_order checks the length and
        # account_banking_pain_base the shape, but neither need be installed
        # and data arrives by import too
        self.env.cr.execute(
            "UPDATE res_bank SET bic = %s WHERE id = %s",
            ("DEU1DEMM", self.deutsche.id))
        self.deutsche.invalidate_recordset(["bic"])
        with self.assertRaisesRegex(UserError, "not a BIC"):
            build_best_foreign(self.company_bank, self.env.company.partner_id,
                               [self._foreign_item()], "EUR", self.today)

    def test_no_remittance_line_starts_with_dash_or_colon(self):
        message = "x" * 34 + " -dash :colon " + "y" * 30 + " :z"
        data = build_best_foreign(
            self.company_bank, self.env.company.partner_id,
            [self._foreign_item(message=message)], "EUR", self.today)
        remittance = field(self._records(data)[1], F02, "remittance")
        for start in range(0, 140, 35):
            self.assertNotIn(remittance[start], "-:")

    def test_variable_symbol_in_remittance(self):
        data = build_best_foreign(
            self.company_bank, self.env.company.partner_id,
            [self._foreign_item(vs="123", ks="0308")], "EUR", self.today)
        remittance = field(self._records(data)[1], F02, "remittance")
        self.assertTrue(remittance.startswith("/VS/123 /KS/0308 Rechnung 77"))


@tagged("post_install", "-at_install")
class TestBestStatement(TransactionCase):
    def _single(self, data, **kwargs):
        triplets = parse_best_statement(data, **kwargs)
        self.assertEqual(len(triplets), 1)
        return triplets[0]

    def test_statement(self):
        currency, account, stmts = self._single(f.statement(
            f.transaction(),
        ), with_symbols=True)
        self.assertEqual((currency, account), ("CZK", f.IBAN))
        stmt = stmts[0]
        self.assertEqual(stmt["name"], "BEST %s/20" % f.IBAN)
        self.assertEqual(stmt["date"], date(2026, 7, 1))
        self.assertAlmostEqual(stmt["balance_start"], 10000.0)
        self.assertAlmostEqual(stmt["balance_end_real"], 11234.5)
        line = stmt["transactions"][0]
        self.assertAlmostEqual(line["amount"], 1234.5)
        self.assertEqual(line["variable_symbol"], "20260042")
        self.assertEqual(line["constant_symbol"], "0308")
        self.assertNotIn("specific_symbol", line)
        self.assertEqual(line["account_number"], "19012333/0300")
        self.assertEqual(line["partner_name"], "ODBERATEL AS")
        self.assertIn("FA 2026/0042", line["payment_ref"])
        # our own description is the credit side's on a credit
        self.assertEqual(line["ref"], "Faktura 42")
        self.assertIn("001-01072026 1602 602021 005093", line["unique_import_id"])

    def test_accounting_codes(self):
        """0 debit, 1 credit, 2 debit reversal, 3 credit reversal — the
        signs of the spec's own check NZ = SZ - OD + OK."""
        _c, _a, stmts = self._single(f.statement(
            f.transaction(txno=1, ku="0", cents=1000),
            f.transaction(txno=2, ku="1", cents=2000),
            f.transaction(txno=3, ku="2", cents=300),
            f.transaction(txno=4, ku="3", cents=40),
            old=0, new=1260,
        ))
        amounts = [t["amount"] for t in stmts[0]["transactions"]]
        self.assertEqual(amounts, [-10.0, 20.0, 3.0, -0.4])
        self.assertAlmostEqual(stmts[0]["balance_start"] + sum(amounts),
                               stmts[0]["balance_end_real"])

    def test_negative_balance_sign(self):
        _c, _a, stmts = self._single(f.statement(
            f.transaction(ku="0", cents=500), old=-100, new=-600))
        self.assertAlmostEqual(stmts[0]["balance_start"], -1.0)
        self.assertAlmostEqual(stmts[0]["balance_end_real"], -6.0)

    def test_non_accounting_records_skipped(self):
        _c, _a, stmts = self._single(f.statement(
            f.transaction(txno=1),
            f.transaction(txno=2, record="53", cents=999),
        ))
        self.assertEqual(len(stmts[0]["transactions"]), 1)

    def test_name_suppressing_ss_is_not_a_symbol(self):
        _c, _a, stmts = self._single(f.statement(
            f.transaction(ss="9999999999")), with_symbols=True)
        self.assertNotIn("specific_symbol", stmts[0]["transactions"][0])

    def test_foreign_payment_counter_account(self):
        """A foreign payment books against KB's internal account; the
        partner's account is in "Popis 1"."""
        _c, _a, stmts = self._single(f.statement(f.transaction(
            flag="2", counter16="0000000000000000", bank="0100",
            desc_debit="ucet DE89370400440532013000")))
        line = stmts[0]["transactions"][0]
        self.assertEqual(line["account_number"], "DE89370400440532013000")

    def test_without_iban_the_national_form(self):
        _c, account, _s = self._single(f.statement(f.transaction(), iban=""))
        self.assertEqual(account, f.NATIONAL)

    def test_two_days_two_statements(self):
        data = f.best_bytes(
            f.header(),
            f.turnover(booked="20260701", number="020"),
            f.transaction(txno=1),
            f.turnover(booked="20260702", number="021", old=1123450,
                       new=1123450 + 5000, credit=5000),
            f.transaction(txno=1, cents=5000, booked="20260702",
                          kbi="001-02072026 1602 600001 000001"),
            f.trailer(count=4),
        )
        _c, _a, stmts = self._single(data)
        self.assertEqual([s["name"][-2:] for s in stmts], ["20", "21"])
        ids = [t["unique_import_id"] for s in stmts for t in s["transactions"]]
        self.assertEqual(len(set(ids)), 2)

    def test_trailing_spaces_lost(self):
        """A file whose records lost their trailing blanks still parses."""
        data = f.statement(f.transaction(flag=" "))
        stripped = b"\r\n".join(line.rstrip() for line in data.split(b"\r\n"))
        _c, _a, stmts = self._single(stripped)
        self.assertAlmostEqual(stmts[0]["transactions"][0]["amount"], 1234.5)

    def test_not_best(self):
        self.assertEqual(parse_best_statement(b"074000000192000145399\r\n"), [])
        self.assertFalse(is_best_statement(b":20:STARTUMS\r\n"))
        self.assertTrue(is_best_statement(f.statement(f.transaction())))
