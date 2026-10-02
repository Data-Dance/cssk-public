# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import hashlib
import os

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.l10n_cssk_oss_base.tests.common import OssReturnCommon

NS = {"vun": "urn:ec.europa.eu:taxud:frsr:vatunion:v1.0"}


@tagged("post_install", "-at_install")
class TestSkOssReturn(OssReturnCommon):

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls._oss_setup("SK2022749619", "l10n_sk_oss.sk_oss_version_dposs_eu01")
        cls.de = cls.env.ref("base.de")
        cls.at = cls.env.ref("base.at")
        cls.gr = cls.env.ref("base.gr")

    def _text(self, root, path):
        return root.findtext(path, namespaces=NS)

    def test_export_matches_the_eform_structure(self):
        self._oss_invoice(self.de, 100.0, 19.0, "2025-07-10")
        self._oss_invoice(self.de, 30.0, 7.0, "2025-07-11")
        self._oss_invoice(self.at, 50.0, 20.0, "2025-08-01",
                          product=self.service)
        ret = self._oss_return(2025, 3)
        ret.action_export_xml()
        raw = base64.b64decode(ret.xml_attachment_id.datas)
        # the eForm loader matches elements by the literal 'vun:' prefix
        self.assertIn(b"<vun:OSSVATReturnMSCON", raw)
        root = self._oss_xml(ret)
        vat = root.find("vun:TraderID/vun:VATNumber", NS)
        self.assertEqual((vat.get("issuedBy"), vat.text), ("SK", "SK2022749619"))
        self.assertEqual(self._text(root, "vun:Period/vun:Year"), "2025")
        self.assertEqual(self._text(root, "vun:Period/vun:Quarter"), "3")
        self.assertEqual(self._text(root, "vun:NilVatReturn"), "0")
        rows = root.findall("vun:Supplies/vun:MSIDSupplies", NS)
        self.assertEqual(len(rows), 3)
        by_key = {(r.findtext("vun:MSCONCountrycode", namespaces=NS),
                   r.findtext("vun:VATRate", namespaces=NS)): r for r in rows}
        de7 = by_key[("DE", "7.00")]
        self.assertEqual(de7.find("vun:VATRate", NS).get("type"), "REDUCED")
        self.assertEqual(de7.findtext("vun:VATAmount", namespaces=NS), "2.10")
        at = by_key[("AT", "20.00")]
        self.assertEqual(at.findtext("vun:SupplyType", namespaces=NS),
                         "SERVICES")
        self.assertEqual(self._text(root, "vun:GrandTotalMSIDGoods"), "21.10")
        self.assertEqual(self._text(root, "vun:GrandTotalMSIDServices"),
                         "10.00")
        self.assertEqual(self._text(root, "vun:GrandTotal"), "31.10")
        self.assertEqual(self._text(root, "vun:TotalVATAmountDue"), "31.10")

    def test_negative_balance_is_left_out_of_the_total_due(self):
        """AT is corrected down by more than this quarter's AT VAT: its
        balance goes negative and is refunded by AT, not netted against DE."""
        q2 = self._oss_invoice(self.at, 100.0, 20.0, "2025-06-10")
        self._oss_refund(q2, "2025-07-15")
        self._oss_invoice(self.de, 100.0, 19.0, "2025-07-16")
        ret = self._oss_return(2025, 3)
        self.assertAlmostEqual(ret.total_corrections, -20.0)
        self.assertAlmostEqual(ret.total_due, 19.0)
        ret.action_export_xml()
        root = self._oss_xml(ret)
        corr = root.find("vun:Corrections/vun:Correction", NS)
        self.assertEqual(corr.findtext("vun:Period/vun:Quarter",
                                       namespaces=NS), "2")
        self.assertEqual(corr.findtext("vun:MSCONCountryCode",
                                       namespaces=NS), "AT")
        self.assertEqual(corr.findtext("vun:TotalVATAmountCorrection",
                                       namespaces=NS), "-20.00")
        balances = {b.findtext("vun:MSCONCountryCode", namespaces=NS):
                    b.findtext("vun:BalanceOfVATDue", namespaces=NS)
                    for b in root.findall("vun:Balances/vun:Balance", NS)}
        self.assertEqual(balances, {"AT": "-20.00", "DE": "19.00"})
        self.assertEqual(self._text(root, "vun:TotalVATAmountDue"), "19.00")

    def test_greece_is_filed_as_el(self):
        self._oss_invoice(self.gr, 100.0, 24.0, "2025-07-10")
        ret = self._oss_return(2025, 3)
        ret.action_export_xml()
        self.assertEqual(self._text(self._oss_xml(ret),
                                    "vun:Supplies/vun:MSIDSupplies/"
                                    "vun:MSCONCountrycode"), "EL")

    def test_nil_return(self):
        ret = self._oss_return(2026, 1)
        ret.action_export_xml()
        root = self._oss_xml(ret)
        self.assertEqual(self._text(root, "vun:NilVatReturn"), "1")
        self.assertIsNone(root.find("vun:Supplies", NS))
        self.assertEqual(self._text(root, "vun:TotalVATAmountDue"), "0.00")

    def test_supply_from_an_establishment_elsewhere(self):
        """Goods dispatched from a warehouse in CZ go to MSESTSupplies."""
        ret = self._oss_return(2025, 3)
        self.env["cssk.oss.return.line"].create({
            "return_id": ret.id, "is_manual": True,
            "member_state_id": self.de.id,
            "origin_country_id": self.env.ref("base.cz").id,
            "origin_vat": "CZ25663585",
            "supply_type": "goods", "vat_rate": 19.0, "rate_type": "standard",
            "taxable_amount": 100.0, "vat_amount": 19.0,
        })
        ret.action_compute_lines()   # a manual row survives the recompute
        self.assertEqual(len(ret.line_ids), 1)
        ret.action_export_xml()
        root = self._oss_xml(ret)
        est = root.find("vun:Supplies/vun:MSESTSupplies", NS)
        vat = est.find("vun:EUTraderID/vun:VATIdentificationNumber", NS)
        self.assertEqual((vat.get("issuedBy"), vat.text), ("CZ", "25663585"))
        self.assertEqual(self._text(root, "vun:GrandTotalMSESTGoods"), "19.00")

    def test_rows_must_not_be_negative(self):
        """A credit note that names no original cannot become a correction."""
        invoice = self._oss_invoice(self.de, 100.0, 19.0, "2025-06-10")
        refund = self._oss_refund(invoice, "2025-07-15")
        refund.reversed_entry_id = False
        ret = self._oss_return(2025, 3)
        self.assertLess(self._row(ret, "DE", 19.0).taxable_amount, 0)
        with self.assertRaisesRegex(UserError, "Negative row"):
            ret.action_export_xml()

    def test_slovak_five_percent_is_mapped_abroad(self):
        """SK 5 % (books, medicines, basic food) -> DE 7 %."""
        oss_tag = self.env.ref("l10n_eu_oss.tag_oss")
        domestic_5 = self.env["account.tax"].search([
            ("company_id", "=", self.company.id), ("type_tax_use", "=", "sale"),
            ("amount", "=", 5.0),
        ]).filtered(lambda t: not (t.invoice_repartition_line_ids.tag_ids
                                   & oss_tag))
        self.assertTrue(domestic_5)
        de7 = self._oss_tax(self.de, 7.0)
        self.assertTrue(de7.original_tax_ids & domestic_5)
        # ... without taking DE 7 % away from SK 19 %, which maps there too
        domestic_19 = self.env["account.tax"].search([
            ("company_id", "=", self.company.id), ("type_tax_use", "=", "sale"),
            ("amount", "=", 19.0),
        ]).filtered(lambda t: not (t.invoice_repartition_line_ids.tag_ids
                                   & oss_tag))
        self.assertTrue(de7.original_tax_ids & domestic_19)
        # every domestic 5 % variant, not just the first core met
        self.assertFalse(domestic_5 - self._oss_fpos(self.de).tax_ids
                         .original_tax_ids)

    def test_filer_must_have_a_slovak_ic_dph(self):
        self.company.with_context(no_vat_validation=True).vat = "CZ25663585"
        ret = self._oss_return(2026, 1)
        with self.assertRaisesRegex(UserError, "IČ DPH"):
            ret.action_export_xml()


@tagged("post_install", "-at_install")
class TestSkOssSchemaPins(TransactionCase):
    """The bundled schema must match data/SCHEMA_VERSION (see that file)."""

    def _pins(self):
        data = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        pins = {}
        with open(os.path.join(data, "SCHEMA_VERSION"), encoding="utf-8") as fh:
            for raw in fh:
                parts = raw.split()
                if len(parts) == 3 and parts[0].endswith(".xsd"):
                    pins[parts[0]] = (parts[1], int(parts[2]))
        return data, pins

    def test_bundled_schemas_match_the_pinned_digests(self):
        data, pins = self._pins()
        self.assertTrue(pins, "SCHEMA_VERSION lists no schemas")
        for name, (digest, size) in pins.items():
            with open(os.path.join(data, name), "rb") as fh:
                blob = fh.read()
            self.assertEqual(len(blob), size, "%s size moved" % name)
            self.assertEqual(hashlib.md5(blob).hexdigest(), digest,
                             "%s does not match its pin" % name)

    def test_every_bundled_schema_is_pinned(self):
        data, pins = self._pins()
        on_disk = {f for f in os.listdir(data) if f.endswith(".xsd")}
        self.assertEqual(on_disk, set(pins),
                         "unpinned schema(s): %s" % sorted(on_disk - set(pins)))

    def test_the_version_carries_the_pinned_schema(self):
        version = self.env.ref("l10n_sk_oss.sk_oss_version_dposs_eu01")
        data, pins = self._pins()
        blob = base64.b64decode(version.xml_schema_data)
        self.assertEqual(hashlib.md5(blob).hexdigest(),
                         pins[version.xml_schema_filename][0])
