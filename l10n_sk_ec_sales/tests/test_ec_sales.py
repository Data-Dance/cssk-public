import base64

from lxml import etree

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class TestSkEcSales(TransactionCase):
    """Smoke tests for the SK Súhrnný výkaz country layer (run at install)."""

    def test_version_seeded(self):
        version = self.env.ref("l10n_sk_ec_sales.sdv_version_2025")
        self.assertEqual(version.country_id.code, "SK")
        self.assertEqual(version.xml_root_element, "dokument")
        self.assertTrue(version.xml_schema_data, "SDV XSD not loaded")
        self.assertEqual(len(version.statement_type_ids), 3)


@tagged("post_install", "-at_install")
class TestSkEcSalesCompute(AccountTestInvoicingCommon):
    """Functional: post an intra-EU supply, compute + export the Súhrnný výkaz."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        # Identification fields the official svdph20 schema needs.
        cls.company.write({
            "vat": "SK2023456787", "city": "Bratislava",
            "country_id": cls.env.ref("base.sk").id,
        })

        # EU customer (Belgium) with a real, valid BE VAT.
        cls.partner_eu = cls.env["res.partner"].create({
            "name": "Kunde BE", "country_id": cls.env.ref("base.be").id,
            "vat": "BE0477472701",
        })
        # Intra-community goods supply tax (0 %), tagged for the EC sales list.
        cls.tax_ic_goods = cls.env["account.tax"].create({
            "name": "Intra-EU goods 0%", "amount": 0.0,
            "amount_type": "percent", "type_tax_use": "sale",
            "company_id": cls.company.id,
            "country_id": cls.company.account_fiscal_country_id.id,
            "tax_group_id": cls.tax_sale_a.tax_group_id.id,
            "cssk_ec_summary_code": "0",
        })
        cls.version = cls.env.ref("l10n_sk_ec_sales.sdv_version_2025")

    def _make_statement(self):
        return self.env["cssk.ec.summary.statement"].create({
            "company_id": self.company.id,
            "version_id": self.version.id,
            "date_from": "2026-06-01",
            "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": self.version.statement_type_ids[0].id,
        })

    def test_compute_and_export(self):
        self.init_invoice(
            "out_invoice", partner=self.partner_eu,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_ic_goods, post=True,
        )
        st = self._make_statement()
        st.action_compute_lines()
        self.assertEqual(len(st.line_ids), 1)
        line = st.line_ids
        self.assertEqual(line.partner_country_code, "BE")
        self.assertEqual(line.partner_vat, "BE0477472701")
        self.assertEqual(line.transaction_code, "0")
        self.assertAlmostEqual(line.total_amount, 1000.0, places=2)

        # Validates against the OFFICIAL svdph20.xsd (root 'dokument', eForm
        # grid of 12-record pages).
        st.action_export_xml()
        self.assertEqual(st.state, "exported")
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).localname, "dokument")
        stranas = root.findall(".//telo/strana")
        self.assertEqual(len(stranas), 1)
        zaznamy = stranas[0].findall("zaznam")
        self.assertEqual(len(zaznamy), 12)  # fixed 12-record page
        first = zaznamy[0]
        self.assertEqual(first.findtext("kodStatu"), "BE")
        self.assertEqual(first.findtext("idCislo"), "0477472701")
        self.assertEqual(first.findtext("hodnota"), "1000")  # whole euros (SVDPHv20)
        # goods are reported BEZ KÓDU — kód column is blank (poučenie SVDPHv20),
        # even though the internal grouping/kontrola code stays "0".
        self.assertEqual(first.findtext("kod") or "", "")

    def test_a_2019_period_exports_the_2010_vzor(self):
        """The whole point of the split: a pre-2020 period files the old shape.

        Validated against the OFFICIAL svdph2010.xsd, so this fails if the
        template drifts toward the 2020 structure — 27 records to a page, an
        `oznacenie` page counter, `pocet2Stran` in the hlavicka, a structured
        fax, and NO `zaznamCast2` (§ 8a call-off stock did not exist yet).
        """
        old_version = self.env.ref("l10n_sk_ec_sales.sdv_version_2010")
        self.init_invoice(
            "out_invoice", partner=self.partner_eu,
            invoice_date="2019-06-10", amounts=[1000.0],
            taxes=self.tax_ic_goods, post=True,
        )
        st = self.env["cssk.ec.summary.statement"].create({
            "company_id": self.company.id,
            "version_id": old_version.id,
            "date_from": "2019-06-01",
            "date_to": "2019-06-30",
            "period_type": "month",
            "statement_type_id": old_version.statement_type_ids[0].id,
        })
        st.action_compute_lines()
        self.assertEqual(len(st.line_ids), 1)
        st.action_export_xml()
        self.assertEqual(st.state, "exported")

        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).localname, "dokument")
        self.assertIsNotNone(root.find(".//hlavicka/pocet2Stran"))
        # tel is structured in this vzor, and fax still exists
        self.assertIsNotNone(root.find(".//adresa/tel/cislo"))
        self.assertIsNotNone(root.find(".//adresa/fax"))
        self.assertIsNone(root.find(".//adresa/email"))

        stranas = root.findall(".//telo/strana")
        self.assertEqual(len(stranas), 1)
        self.assertEqual(stranas[0].findtext("oznacenie/aktualna"), "1")
        self.assertEqual(stranas[0].findtext("oznacenie/celkovo"), "1")
        self.assertEqual(len(stranas[0].findall("zaznam")), 27)
        self.assertEqual(stranas[0].findall("zaznamCast2"), [])
        first = stranas[0].findall("zaznam")[0]
        self.assertEqual(first.findtext("kodStatu"), "BE")
        self.assertEqual(first.findtext("idCislo"), "0477472701")
        self.assertEqual(first.findtext("hodnota"), "1000")

    def test_a_legacy_vykaz_compares_against_a_fresh_computation(self):
        """End to end, through the real entry point.

        Until the row comparator existed this form answered "does not support
        comparison" — honest and useless. It now diffs per counterparty, and
        a supply the filing reports differently from what the ledger produces
        names the trading partner rather than a figure.
        """
        self.init_invoice(
            "out_invoice", partner=self.partner_eu,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_ic_goods, post=True,
        )
        legacy = self._make_statement()
        legacy.write({"legacy": True, "legacy_source": "PREMIER"})
        # what "was filed": the same counterparty at a different figure, plus
        # one the ledger has no trace of
        self.env["cssk.ec.summary.statement.line"].create([
            {"statement_id": legacy.id, "partner_country_code": "BE",
             "partner_vat": "BE0477472701", "transaction_code": "0",
             "total_amount": 900.0},
            {"statement_id": legacy.id, "partner_country_code": "DE",
             "partner_vat": "DE811907980", "transaction_code": "0",
             "total_amount": 40.0},
        ])
        result = legacy._cssk_compare_to_computed()
        self.assertTrue(result["comparable"], result["reason"])
        by_status = {}
        for row in result["rows"]:
            by_status.setdefault(row["status"], []).append(row["code"])
        self.assertIn("differs", by_status, result["rows"])
        self.assertTrue(any("BE0477472701" in c for c in by_status["differs"]))
        self.assertIn("only_filed", by_status)
        self.assertTrue(any("DE811907980" in c for c in by_status["only_filed"]))
        # the scratch statement must not survive the comparison
        self.assertEqual(
            self.env["cssk.ec.summary.statement"].search_count(
                [("company_id", "=", self.company.id),
                 ("date_from", "=", legacy.date_from)]),
            1, "a scratch statement was left behind")

    def test_a_legacy_vykaz_says_cannot_rather_than_zero(self):
        """The distinction the coded comparator makes, kept for rows.

        A period with no imported ledger behind it is not a period where
        every counterparty differs by its whole value.
        """
        version = self.env.ref("l10n_sk_ec_sales.sdv_version_2010")
        legacy = self.env["cssk.ec.summary.statement"].create({
            "company_id": self.company.id, "version_id": version.id,
            "date_from": "2014-06-01", "date_to": "2014-06-30",
            "period_type": "month",
            "statement_type_id": version.statement_type_ids[0].id,
            "legacy": True, "legacy_source": "PREMIER",
        })
        self.env["cssk.ec.summary.statement.line"].create({
            "statement_id": legacy.id, "partner_country_code": "BE",
            "partner_vat": "BE0477472701", "transaction_code": "0",
            "total_amount": 900.0,
        })
        result = legacy._cssk_compare_to_computed()
        self.assertFalse(result["comparable"])
        self.assertIn("never imported", result["reason"])
        self.assertEqual(result["rows"], [])

    def test_negative_total_rounds_half_up_away_from_zero(self):
        """A negative per-partner total (corrections exceed supplies) must
        round half-up AWAY from zero: −9.70 → −10 in both hodnota and
        celkovaHodnota. The old int(x + 0.5) idiom truncated to −9."""
        self.init_invoice(
            "out_invoice", partner=self.partner_eu,
            invoice_date="2026-06-10", amounts=[0.30],
            taxes=self.tax_ic_goods, post=True,
        )
        self.init_invoice(
            "out_refund", partner=self.partner_eu,
            invoice_date="2026-06-12", amounts=[10.0],
            taxes=self.tax_ic_goods, post=True,
        )
        st = self._make_statement()
        st.action_compute_lines()
        self.assertEqual(len(st.line_ids), 1)
        self.assertAlmostEqual(st.line_ids.total_amount, -9.70, places=2)

        st.action_export_xml()
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        first = root.findall(".//telo/strana/zaznam")[0]
        self.assertEqual(first.findtext("hodnota"), "-10")
        self.assertEqual(root.findtext(".//hlavicka/celkovaHodnota"), "-10")

    def test_preflight_implausible_vat_prefix(self):
        """Master-data preflight: the svdph20 zaznam splits the customer VAT
        into kodStatu + idCislo by its 2-letter prefix — a VAT with an
        implausible prefix blocks the export early, naming the line."""
        self.init_invoice(
            "out_invoice", partner=self.partner_eu,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_ic_goods, post=True,
        )
        st = self._make_statement()
        st.action_compute_lines()
        st.line_ids.partner_vat = "QQ0477472701"  # 'QQ' is no country code
        with self.assertRaises(UserError) as cm:
            st.action_export_xml()
        self.assertIn("QQ0477472701", str(cm.exception))
        self.assertEqual(st.state, "preview", "fail-early: nothing exported")

        # EL (Greece) and XI (Northern Ireland) are legitimate VAT prefixes
        # even though they are not ISO country codes — the preflight accepts
        # them (the VIES gate then judges EU membership separately).
        st.line_ids.partner_vat = "EL123456789"
        st._cssk_preflight_export()  # must not raise
        st.line_ids.partner_vat = "XI123456789"
        st._cssk_preflight_export()  # must not raise

    def test_kontroly_kod(self):
        """kód plnenia must be one of {0,1,2}: clean on a goods supply, and an
        invalid code is a hard block (SV_KOD)."""
        self.init_invoice(
            "out_invoice", partner=self.partner_eu,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_ic_goods, post=True,
        )
        st = self._make_statement()
        st.action_compute_lines()
        self.assertEqual(st.check_kontroly(), [], "kód '0' must be accepted")

        st.line_ids.transaction_code = "9"  # not a valid súhrnný-výkaz kód
        codes = [v["code"] for v in st.check_kontroly()]
        self.assertIn("SV_KOD", codes, "kontroly must reject an invalid kód")


class TestSkEcSalesVintages(TransactionCase):
    """Two vzory, and a period must reach the right one.

    FS SR publishes one XSD per vzor and keeps the old ones, so a period is
    filed in the structure in force AT THE TIME. Until 19.0.1.2.0 this module
    shipped only the 2020 one and offered it back to 2010, which would have
    filed a 2019 period in a structure that did not exist then — 12+12 records
    a page against the 27 the vzor wants, plus an element (`zaznamCast2`) the
    2019 schema does not define at all.
    """

    def test_both_vintages_are_seeded(self):
        for xmlid, schema in (("sdv_version_2010", "svdph2010.xsd"),
                              ("sdv_version_2025", "svdph20.xsd")):
            version = self.env.ref("l10n_sk_ec_sales.%s" % xmlid)
            self.assertEqual(version.country_id.code, "SK")
            self.assertEqual(version.xml_root_element, "dokument")
            self.assertTrue(version.xml_schema_data, "%s XSD not loaded" % xmlid)
            self.assertEqual(version.xml_schema_filename, schema)
            self.assertEqual(len(version.statement_type_ids), 3)

    def test_the_vintages_meet_at_the_quick_fixes(self):
        """1. 1. 2020, and no period falls between them or into both."""
        old = self.env.ref("l10n_sk_ec_sales.sdv_version_2010")
        new = self.env.ref("l10n_sk_ec_sales.sdv_version_2025")
        self.assertEqual(str(old.valid_from), "2010-01-01")
        self.assertEqual(str(old.valid_to), "2019-12-31")
        self.assertEqual(str(new.valid_from), "2020-01-01")
        self.assertFalse(new.valid_to, "the current vzor is open-ended")

    def test_a_period_resolves_to_exactly_one_vintage(self):
        """The domain the statement uses, exercised at the boundary.

        A gap and an overlap look identical from the form — the version field
        just offers a different list — so this checks the dates the way the
        record does, not by reading them back.
        """
        for date_from, date_to, expected in (
            ("2019-12-01", "2019-12-31", "sdv_version_2010"),
            ("2020-01-01", "2020-01-31", "sdv_version_2025"),
            ("2014-04-01", "2014-06-30", "sdv_version_2010"),
            ("2026-01-01", "2026-01-31", "sdv_version_2025"),
        ):
            found = self.env["cssk.ec.summary.statement.version"].search([
                ("country_id", "=", self.env.ref("base.sk").id),
                ("valid_from", "<=", date_to),
                "|", ("valid_to", "=", False), ("valid_to", ">=", date_from),
            ])
            self.assertEqual(
                len(found), 1,
                "%s..%s resolves to %s versions, not one"
                % (date_from, date_to, len(found)))
            self.assertEqual(
                found, self.env.ref("l10n_sk_ec_sales.%s" % expected),
                "%s..%s reached the wrong vzor" % (date_from, date_to))

    def test_the_2010_vzor_has_no_call_off_stock_register(self):
        """What actually separates the two, asserted on the schemas we ship.

        `zaznamCast2` is the § 8a call-off-stock register the Quick Fixes
        brought in on 1. 1. 2020. If it ever appears in the earlier schema,
        either the file was replaced or the vintages have been mixed up.
        """
        old = self.env.ref("l10n_sk_ec_sales.sdv_version_2010")
        new = self.env.ref("l10n_sk_ec_sales.sdv_version_2025")
        old_xsd = base64.b64decode(old.xml_schema_data).decode()
        new_xsd = base64.b64decode(new.xml_schema_data).decode()
        self.assertNotIn("zaznamCast2", old_xsd)
        self.assertIn("zaznamCast2", new_xsd)
        self.assertIn('minOccurs="27"', old_xsd)
        self.assertIn('minOccurs="12"', new_xsd)


@tagged("post_install", "-at_install")
class TestSkEcSalesSchemaPins(TransactionCase):
    """The bundled schemas must match data/SCHEMA_VERSION.

    Not a check that our copies are CURRENT — nothing local can answer that,
    and these two are the awkward case: svdph2010.xsd carries no vintage and no
    revision at all, and svdph20.xsd stamps a vintage only. A file revised in
    place validates exactly as before and says nothing about it. What this
    checks is that the bundled bytes are the ones somebody verified against the
    published copy on a stated date.
    """

    def _pins(self, data):
        import os
        pins = {}
        with open(os.path.join(data, "SCHEMA_VERSION"), encoding="utf-8") as fh:
            for raw in fh:
                parts = raw.split()
                if len(parts) == 3 and parts[0].endswith(".xsd"):
                    pins[parts[0]] = (parts[1], int(parts[2]))
        return pins

    def _data_dir(self):
        import os
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(here, "data")

    def test_bundled_schemas_match_the_pinned_digests(self):
        import hashlib
        import os
        data = self._data_dir()
        pins = self._pins(data)
        self.assertTrue(pins, "SCHEMA_VERSION lists no schemas")
        for name, (digest, size) in pins.items():
            path = os.path.join(data, name)
            self.assertTrue(os.path.exists(path), "%s is pinned but missing" % name)
            blob = open(path, "rb").read()
            self.assertEqual(len(blob), size, "%s size moved" % name)
            self.assertEqual(
                hashlib.md5(blob).hexdigest(), digest,
                "%s does not match its pin — if this is a deliberate refresh, "
                "update data/SCHEMA_VERSION and re-run the export tests" % name)

    def test_every_bundled_schema_is_pinned(self):
        """A schema added without a pin is the gap this file exists to close."""
        import os
        data = self._data_dir()
        on_disk = {f for f in os.listdir(data) if f.endswith(".xsd")}
        pinned = set(self._pins(data))
        self.assertEqual(on_disk, pinned,
                         "unpinned schema(s): %s" % sorted(on_disk - pinned))
