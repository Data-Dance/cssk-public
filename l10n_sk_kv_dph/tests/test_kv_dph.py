import base64

from lxml import etree

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class TestSkKvDph(TransactionCase):
    """Smoke tests for the SK KV DPH country layer (run at install)."""

    def test_version_seeded(self):
        version = self.env.ref("l10n_sk_kv_dph.kvdph_version_2025v1")
        self.assertEqual(version.country_id.code, "SK")
        self.assertEqual(version.xml_root_element, "KVDPH_2025")
        self.assertEqual(len(version.section_code_ids), 10)
        codes = set(version.section_code_ids.mapped("code"))
        self.assertEqual(
            codes,
            {"A.1", "A.2", "B.1", "B.2", "B.3.1", "B.3.2",
             "C.1", "C.2", "D.1", "D.2"},
        )

    def test_section_models_exist(self):
        for code in ("a1", "a2", "b1", "b2", "b31", "b32", "c1", "c2", "d1", "d2"):
            self.assertIn(
                "l10n.sk.kv.dph.section.%s" % code, self.env,
                "Missing SK KV DPH section model %s" % code,
            )


class TestSkKvDphVintages(TransactionCase):
    """Two vzory, and a version claims only the periods whose schema we hold.

    `kv_dph_2023.xsd` says it applies to periods beginning on or after
    1. 7. 2023 and `kv_dph_2025.xsd` says the same of 1. 1. 2025. The two
    schemas are the same SHAPE — identical sections and field names — and
    differ in the root element and namespace, which is exactly what a
    submission is validated against: a 2023 period exported under KVDPH_2025
    carries correct figures and is rejected by the portal.
    """

    def test_the_two_vzory_meet_without_a_gap(self):
        old = self.env.ref("l10n_sk_kv_dph.kvdph_version_2023")
        new = self.env.ref("l10n_sk_kv_dph.kvdph_version_2025v1")
        self.assertEqual(str(old.valid_from), "2023-07-01")
        self.assertEqual(str(old.valid_to), "2024-12-31")
        self.assertEqual(str(new.valid_from), "2025-01-01")
        self.assertFalse(new.valid_to)

    def test_each_vzor_carries_its_own_root_and_schema(self):
        """The whole reason the 2023 record exists."""
        old = self.env.ref("l10n_sk_kv_dph.kvdph_version_2023")
        new = self.env.ref("l10n_sk_kv_dph.kvdph_version_2025v1")
        self.assertEqual(old.xml_root_element, "KVDPH_2023")
        self.assertEqual(new.xml_root_element, "KVDPH_2025")
        self.assertNotEqual(old.xml_template_ref_id, new.xml_template_ref_id)
        self.assertTrue(old.xml_schema_data, "the 2023 XSD is not loaded")
        self.assertNotEqual(
            old.xml_schema_data, new.xml_schema_data,
            "the two vzory must validate against their own schemas")

    def test_the_section_set_is_unchanged_between_them(self):
        """The 2023->2025 change is a binding change, not a structural one.

        Asserting it keeps someone from 'fixing' a difference that is not
        there — and would catch a real one if a future vzor moves a section.
        """
        old = self.env.ref("l10n_sk_kv_dph.kvdph_version_2023")
        new = self.env.ref("l10n_sk_kv_dph.kvdph_version_2025v1")
        self.assertEqual(
            set(old.section_code_ids.mapped("code")),
            set(new.section_code_ids.mapped("code")))

    def test_the_four_vzory_tile_without_gap_or_overlap(self):
        """2014 -> 2016 -> 2023 -> 2025, each starting the day after the last
        one ends. A gap means a period silently has no form; an overlap means
        two versions claim it and the winner is arbitrary."""
        vers = self.env["cssk.control.statement.version"].search(
            [("country_id.code", "=", "SK")], order="valid_from")
        self.assertEqual(
            [v.xml_root_element for v in vers],
            ["KVDPH", "KVDPH_2016", "KVDPH_2023", "KVDPH_2025"])
        for earlier, later in zip(vers, vers[1:]):
            self.assertTrue(earlier.valid_to, "%s must end" % earlier.name)
            self.assertEqual(
                (later.valid_from - earlier.valid_to).days, 1,
                "%s ends %s and %s starts %s"
                % (earlier.name, earlier.valid_to, later.name, later.valid_from))
        self.assertFalse(vers[-1].valid_to, "the current vzor stays open")

    def test_the_2016_vzor_starts_on_its_own_effective_date(self):
        """kv_dph_2016.xsd states "Ucinnost: 1.4.2016" and rf-elements-06
        pinned the same boundary independently from 231 filed runs. The form
        and the customer's filings agreeing without either being derived from
        the other is what makes the date safe."""
        v = self.env.ref("l10n_sk_kv_dph.kvdph_version_2016")
        self.assertEqual(str(v.valid_from), "2016-04-01")

    def test_the_b3_split_arrives_with_the_2016_vzor(self):
        """The one structural difference between the vintages.

        Before 1. 4. 2016 the form carried a single aggregate B.3 of every
        simplified invoice; from that date it splits into B.3.1 (below the
        limit, aggregated) and B.3.2 (at or above it, per supplier). Read off
        the schemas: `kv_dph_2014.xsd` has ref B3 maxOccurs="2" and no B31/B32
        at all.
        """
        v2014 = self.env.ref("l10n_sk_kv_dph.kvdph_version_2014")
        codes = set(v2014.section_code_ids.mapped("code"))
        self.assertIn("B.3", codes)
        self.assertNotIn("B.3.1", codes)
        self.assertNotIn("B.3.2", codes)
        for xmlid in ("kvdph_version_2016", "kvdph_version_2023",
                      "kvdph_version_2025v1"):
            later = set(self.env.ref("l10n_sk_kv_dph.%s" % xmlid)
                        .section_code_ids.mapped("code"))
            self.assertNotIn("B.3", later)
            self.assertIn("B.3.1", later)
            self.assertIn("B.3.2", later)

    def test_every_vzor_carries_its_own_schema_blob(self):
        """Four distinct schemas, all loaded. An empty blob is the failure
        that used to pass silently — the CZ side had a schema read 0 bytes
        under one --data-dir while validation reported nothing."""
        vers = self.env["cssk.control.statement.version"].search(
            [("country_id.code", "=", "SK")])
        blobs = []
        for v in vers:
            self.assertTrue(v.xml_schema_data, "%s has no schema" % v.name)
            blobs.append(v.xml_schema_data)
        self.assertEqual(len(set(blobs)), len(vers),
                         "each vzor must validate against its own schema")

    def test_periods_before_the_form_existed_resolve_to_nothing(self):
        """The kontrolný výkaz obligation began 1. 1. 2014 (§ 78a zákona
        č. 222/2004 Z. z.), so there is nothing to resolve before it — and
        nothing to reconstruct either.

        This assertion used to name 2016-06-30 and 2023-06-30, correctly, when
        those periods had no schema we held. They are covered now; the rule it
        encodes is unchanged and only its boundary moved.
        """
        Version = self.env["cssk.control.statement.version"]
        for day in ("2013-12-31", "2010-01-01"):
            found = Version.search([
                ("country_id.code", "=", "SK"),
                ("valid_from", "<=", day),
                "|", ("valid_to", "=", False), ("valid_to", ">=", day),
            ])
            self.assertFalse(
                found, "%s resolved to %s — the form did not exist yet"
                % (day, found.mapped("name")))


@tagged("post_install", "-at_install")
class TestSkKvDphCompute(AccountTestInvoicingCommon):
    """Functional tests: post invoices, compute the statement, check rows."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        # Identification fields required by the official KVDPH schema.
        cls.company.write({
            "vat": "SK2023456787", "city": "Bratislava",
            "country_id": cls.env.ref("base.sk").id,
        })
        cls.partner_a.country_id = cls.env.ref("base.sk")
        cls.partner_a.vat = "SK2023456787"

        # SK chart taxes (correct country/group); assertions are computed from
        # their actual rate, so they hold whatever the SK chart ships.
        cls.tax_sale = cls.tax_sale_a
        cls.tax_purchase = cls.tax_purchase_a
        cls.rate_s = cls.tax_sale.amount
        cls.rate_p = cls.tax_purchase.amount
        cls.version = cls.env.ref("l10n_sk_kv_dph.kvdph_version_2025v1")

    def _make_statement(self):
        return self.env["cssk.control.statement"].create({
            "company_id": self.company.id,
            "version_id": self.version.id,
            "date_from": "2026-06-01",
            "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": self._sk_type("R").id,
        })

    def _sk_type(self, fa_xml_value):
        """The Slovak submission type by its XML value.

        Looked up by COUNTRY rather than through the version: the three types
        are declared once for Slovakia and served every vzor from 2014 to
        2025, so there is no per-version set to index into any more.
        """
        return self.env["cssk.control.statement.type"].search([
            ("country_id", "=", self.env.ref("base.sk").id),
            ("fa_xml_value", "=", fa_xml_value),
        ])

    def _statement_for(self, version, date_from, date_to):
        return self.env["cssk.control.statement"].create({
            "company_id": self.company.id,
            "version_id": version.id,
            "date_from": date_from, "date_to": date_to,
            "period_type": "month",
            "statement_type_id": self._sk_type("R").id,
        })

    def test_sale_side_reverse_charge_reports_in_a2(self):
        """A §69 ods. 12 issued supply — 0 % sale tax flagged reverse-charge —
        reports its base in KV oddiel A.2, the counterpart to received reverse
        charge in B.1. Before this tax the SK chart shipped only the received
        side, so an issued §69/12 supply had nothing to carry it into A.2.
        """
        tax = self.env["account.tax"].search([
            ("company_id", "=", self.company.id),
            ("type_tax_use", "=", "sale"),
            ("cssk_control_is_reverse_charge", "=", True)], limit=1)
        self.assertTrue(
            tax, "the SK chart must ship a sale-side reverse-charge tax")
        self.assertEqual(tax.amount, 0.0, "the supplier applies 0 %")
        self.assertFalse(
            tax._cssk_self_assesses(),
            "the supplier does not self-assess — the recipient does")
        move = self.env["account.move"].with_company(self.company).create({
            "move_type": "out_invoice", "partner_id": self.partner_a.id,
            "invoice_date": "2026-06-15",
            "invoice_line_ids": [Command.create({
                "name": "§69/12 supply", "quantity": 1, "price_unit": 1000.0,
                "tax_ids": [Command.set(tax.ids)]})],
        })
        move.action_post()
        self.assertEqual(move.invoice_line_ids[0]._cssk_resolve_section_code(), "A.2")
        self.assertEqual(move.amount_tax, 0.0)
        self.assertEqual(move.amount_untaxed, 1000.0)

    def _rc_sale_tax(self):
        return self.env["account.tax"].search([
            ("company_id", "=", self.company.id),
            ("type_tax_use", "=", "sale"),
            ("cssk_control_is_reverse_charge", "=", True)], limit=1)

    def _rc_goods_invoice(self, lines):
        tax = self._rc_sale_tax()
        move = self.env["account.move"].with_company(self.company).create({
            "move_type": "out_invoice", "partner_id": self.partner_a.id,
            "invoice_date": "2026-06-15",
            "invoice_line_ids": [Command.create({
                "product_id": product.id, "quantity": qty,
                "product_uom_id": uom.id, "price_unit": price,
                "tax_ids": [Command.set(tax.ids)]})
                for product, qty, uom, price in lines],
        })
        move.action_post()
        return move

    def test_a2_reports_what_was_supplied_under_69_12(self):
        """TK / TD / Mn / MJ on A.2 — one row per commodity, units converted.

        Reported by an external accountant: every vzor has carried these
        attributes since 2014, and the template wrote none of them."""
        metal = self.env["product.product"].create({
            "name": "Plech", "l10n_sk_kv_rc_goods": "g",
            "l10n_sk_kv_cn_code": "7208"})
        phone = self.env["product.product"].create({
            "name": "Telefón", "l10n_sk_kv_rc_goods": "h"})
        gram = self.env.ref("uom.product_uom_gram")
        unit = self.env.ref("uom.product_uom_unit")
        move = self._rc_goods_invoice([
            (metal, 250000.0, gram, 0.004),   # 250 kg, filed in kg
            (phone, 10.0, unit, 150.0),
        ])
        st = self._make_statement()
        st.action_compute_lines()
        rows = st.sk_section_a2_ids
        self.assertEqual(len(rows), 2, "two commodities, two rows")
        self.assertEqual(set(rows.move_id.ids), {move.id})
        by = {r.rc_goods: r for r in rows}
        self.assertEqual(by["g"].goods_code, "7208")
        self.assertEqual(by["g"].uom_code, "kg")
        self.assertAlmostEqual(by["g"].quantity, 250.0, 2)
        self.assertAlmostEqual(by["g"].tax_base_amount, 1000.0, 2)
        self.assertEqual(by["h"].goods_kind, "MT")
        self.assertFalse(by["h"].goods_code)
        self.assertEqual(by["h"].uom_code, "ks")
        self.assertAlmostEqual(by["h"].quantity, 10.0, 2)

        st.action_export_xml()   # renders AND validates against the XSD
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        ns = {"k": "https://ekr.financnasprava.sk/Formulare/XSD/kv_dph_2025.xsd"}
        got = {
            (r.get("TK"), r.get("TD"), r.get("Mn"), r.get("MJ"))
            for r in root.findall(".//k:A2", ns)}
        self.assertEqual(got, {
            ("7208", None, "250.00", "kg"), (None, "MT", "10.00", "ks")})

    def test_a2_without_the_commodity_code_is_named_not_filed(self):
        metal = self.env["product.product"].create({
            "name": "Plech bez kódu", "l10n_sk_kv_rc_goods": "g"})
        self._rc_goods_invoice(
            [(metal, 5.0, self.env.ref("uom.product_uom_ton"), 200.0)])
        st = self._make_statement()
        st.action_compute_lines()
        self.assertEqual(st.sk_section_a2_ids.uom_code, "t")
        with self.assertRaisesRegex(UserError, "commodity code"):
            st.action_export_xml()

    def test_a2_other_69_12_supplies_carry_only_the_base(self):
        """Scrap, construction work: no category, no goods attributes."""
        service = self.env["product.product"].create({"name": "Stavebné práce"})
        self._rc_goods_invoice(
            [(service, 1.0, self.env.ref("uom.product_uom_unit"), 800.0)])
        st = self._make_statement()
        st.action_compute_lines()
        row = st.sk_section_a2_ids
        self.assertFalse(row.rc_goods or row.goods_code or row.uom_code)
        st.action_export_xml()
        a2 = etree.fromstring(
            base64.b64decode(st.xml_attachment_id.datas)).find(
            ".//{https://ekr.financnasprava.sk/Formulare/XSD/kv_dph_2025.xsd}A2")
        self.assertIsNone(a2.get("MJ"))

    def test_every_vzor_exports_xml_that_validates_against_its_own_schema(self):
        """The metadata tests prove the versions are wired; only an export
        proves the TEMPLATE is. Each vintage renders through its own QWeb
        template and is validated against its own XSD by the export pipeline,
        so a wrong root element, a stray attribute or a section the vzor does
        not have fails here rather than at the portal.
        """
        cases = [
            ("kvdph_version_2014", "KVDPH", "2015-06-01", "2015-06-30"),
            ("kvdph_version_2016", "KVDPH_2016", "2017-06-01", "2017-06-30"),
            ("kvdph_version_2023", "KVDPH_2023", "2023-09-01", "2023-09-30"),
            ("kvdph_version_2025v1", "KVDPH_2025", "2025-06-01", "2025-06-30"),
        ]
        for xmlid, root, date_from, date_to in cases:
            version = self.env.ref("l10n_sk_kv_dph.%s" % xmlid)
            st = self._statement_for(version, date_from, date_to)
            st.action_compute_lines()
            st.action_export_xml()
            self.assertEqual(st.state, "exported", xmlid)
            xml = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
            self.assertEqual(
                etree.QName(xml).localname, root,
                "%s must render <%s>" % (xmlid, root))

    def test_the_2014_vzor_renders_b3_and_never_b31(self):
        """A simplified receipt in a 2015 period lands in the single B.3
        aggregate. Asserted on the rendered XML rather than on the row,
        because the section a vzor does not have is exactly the kind of error
        that an optional attribute would let through silently."""
        version = self.env.ref("l10n_sk_kv_dph.kvdph_version_2014")
        st = self._statement_for(version, "2015-06-01", "2015-06-30")
        st.action_compute_lines()
        st.action_export_xml()
        xml = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        tags = {etree.QName(el).localname for el in xml.iter()}
        self.assertNotIn("B31", tags, "the B.3 split did not exist until 2016")
        self.assertNotIn("B32", tags)

    def test_a_tag_shared_by_several_rates_does_not_multiply_them(self):
        """A TAG DOES NOT IDENTIFY A TAX, and passing every candidate is not a
        conservative over-estimate — it is a multiplication.

        `compute_all` applies the whole set CUMULATIVELY. Measured on a real
        filing: a base line of 1 995.00 carrying tag '03' resolved to twelve
        taxes — 23 %, 23 % S, 23 % M and their 20 % historic clones, doubled
        because the lookup had no company filter — summing to 258 %. The KV row
        reported **5 147.10 of VAT against an actual 399.00**: schema-valid,
        plausible, and 12.9x the truth. A 23 % rate on an August 2024 supply is
        also impossible; that rate did not exist until 2025.

        Where the rate cannot be determined the row keeps its BASE and reports
        no tax — visibly incomplete, and named by the kontroly — because a
        guessed number is the worst outcome available here.
        """
        company = self.company
        tag = self.env["account.account.tag"].create({
            "name": "MULTI", "applicability": "taxes",
            "country_id": self.env.ref("base.sk").id,
        })
        rates = {}
        for amount in (20.0, 23.0):
            tax = self.env["account.tax"].create({
                "name": "Multi %g%%" % amount, "amount": amount,
                "amount_type": "percent", "type_tax_use": "sale",
                "company_id": company.id,
            })
            tax.invoice_repartition_line_ids.filtered(
                lambda r: r.repartition_type == "base"
            ).write({"tag_ids": [(6, 0, tag.ids)]})
            rates[amount] = tax

        move = self.env["account.move"].create({
            "move_type": "entry", "date": "2026-06-14",
            "journal_id": self.company_data["default_journal_misc"].id,
            "line_ids": [
                (0, 0, {"account_id": self.company_data["default_account_revenue"].id,
                        "debit": 0.0, "credit": 1995.0,
                        "tax_tag_ids": [(6, 0, tag.ids)]}),
                (0, 0, {"account_id": self.company_data["default_account_receivable"].id,
                        "debit": 1995.0, "credit": 0.0}),
            ],
        })
        move.action_post()
        line = move.line_ids.filtered("tax_tag_ids")[:1]

        self.assertGreater(
            len(line._cssk_taxes()), 1,
            "the fixture must be ambiguous — two rates share the tag")
        self.assertFalse(
            line._cssk_taxes_for_amounts(),
            "two different rates cannot be resolved to one, so nothing is "
            "computed rather than everything being summed")

        base, tax = line._cssk_base_and_tax_amounts()
        self.assertAlmostEqual(
            abs(base), 1995.0, places=2,
            msg="the BASE is known and the row must keep it")
        self.assertAlmostEqual(
            tax, 0.0, places=2,
            msg="the rate is not in the data; 258%% of the base certainly is "
                "not the answer")
        # ⚠️ And the RATE must go with the amount. Taking it from the full
        # classification set produced an exported row reading
        # D='0.00' S='23' Z='1995.00' — a supply at 23 % carrying no tax,
        # XSD-valid and false on its face, with 23 % impossible for the period
        # anyway. A row that cannot be described must not describe itself.
        self.assertEqual(
            line._cssk_tax_rate(), 0.0,
            "the rate must come from the same narrowed set as the amount, or "
            "the row declares a rate the amount logic refused to trust")

    def test_one_rate_across_variants_still_computes(self):
        """Ambiguity is about the RATE, not about how many taxes carry a tag.

        20 %, 20 % S and 20 % M compute the same tax on the same base, so the
        choice between them does not matter and the row must still report its
        tax. Without this the fix above would silently blank every tags-only
        row, which is a different way of being wrong.
        """
        company = self.company
        tag = self.env["account.account.tag"].create({
            "name": "ONERATE", "applicability": "taxes",
            "country_id": self.env.ref("base.sk").id,
        })
        for suffix in ("", " S", " M"):
            tax = self.env["account.tax"].create({
                "name": "Same 20%%%s" % suffix, "amount": 20.0,
                "amount_type": "percent", "type_tax_use": "sale",
                "company_id": company.id,
            })
            tax.invoice_repartition_line_ids.filtered(
                lambda r: r.repartition_type == "base"
            ).write({"tag_ids": [(6, 0, tag.ids)]})

        move = self.env["account.move"].create({
            "move_type": "entry", "date": "2026-06-15",
            "journal_id": self.company_data["default_journal_misc"].id,
            "line_ids": [
                (0, 0, {"account_id": self.company_data["default_account_revenue"].id,
                        "debit": 0.0, "credit": 1995.0,
                        "tax_tag_ids": [(6, 0, tag.ids)]}),
                (0, 0, {"account_id": self.company_data["default_account_receivable"].id,
                        "debit": 1995.0, "credit": 0.0}),
            ],
        })
        move.action_post()
        line = move.line_ids.filtered("tax_tag_ids")[:1]
        self.assertEqual(len(line._cssk_taxes_for_amounts()), 1)
        base, tax = line._cssk_base_and_tax_amounts()
        self.assertAlmostEqual(abs(base), 1995.0, places=2)
        self.assertAlmostEqual(
            abs(tax), 399.0, places=2,
            msg="one rate across three variants is not ambiguous")

    def test_the_document_reference_loses_its_whitespace_in_the_XML(self):
        """`\\S{1,32}` forbids whitespace outright; the form cannot carry it.

        So the choice is normalise or refuse the filing, and a real accepted
        filing settles it: the customer's KV row for `PGGR - 2024/05/110` went
        to the tax office as `PGGR-2024/05/110` and was accepted.

        The STORED reference keeps the source's spelling — it is what
        drill-down and every comparison match on. Only the XML view is
        normalised, because only the XML has the constraint.

        Found the first time a KV export was validated against a real schema
        instead of skipping it: 26 of 175 references over two years carry
        whitespace, so it blocked a large share of periods and did so silently.
        """
        Row = self.env["l10n.sk.kv.dph.section.b2"]
        self.assertEqual(
            Row._cssk_ref_for_xml("PGGR - 2024/05/110"), "PGGR-2024/05/110")
        self.assertEqual(
            Row._cssk_ref_for_xml("  a b\tc\n"), "abc",
            "every whitespace character, not just the space")
        self.assertEqual(Row._cssk_ref_for_xml(""), "")
        self.assertFalse(Row._cssk_ref_for_xml(False))
        self.assertEqual(
            Row._cssk_ref_for_xml("FA-2024/0001"), "FA-2024/0001",
            "a reference the form accepts must pass through untouched")

    def test_an_over_long_reference_is_named_rather_than_truncated(self):
        """The length half of the pattern cannot be fixed silently.

        Shortening a reference the tax office cross-matches against the
        supplier's own filing would break the match it exists for — so it is
        reported the way a missing IČ DPH is, instead of surfacing as an XSD
        pattern error against a line number.
        """
        Row = self.env["l10n.sk.kv.dph.section.b2"]
        long_ref = "X" * 40
        self.assertEqual(
            Row._cssk_ref_for_xml(long_ref), long_ref,
            "normalisation must not truncate — that is the kontrola's job")
        self.assertGreater(len(Row._cssk_ref_for_xml(long_ref)), 32)

    def test_a_received_document_with_no_counterparty_is_B3_not_B2(self):
        """Oddiel B.2 reports the supplier's IČ DPH per row.

        So a received document with NO counterparty at all cannot be a B.2 row
        — that is a property of the form, not a guess about the document, and
        it is what makes this safe to derive rather than waiting for an
        extractor to set `l10n_sk_kv_is_simplified`.

        Found by EXPORTING, not by comparing. On the MRP agenda 49 ledger
        receipts classified B.2 while the totals agreed with the filing to the
        cent — the accountant filed a B.3 aggregate of 2 113.25 and the
        comparison matched it, so the difference read as presentational. It was
        not: the export failed on "B.2 row(s) without the counterparty's IČ
        DPH" and no placeholder could fix it, because there was no counterparty
        to give one to.
        """
        # A ledger-built ENTRY, which is what these actually are: Odoo refuses
        # to post a vendor BILL with no counterparty, and a receipt imported
        # from a ledger has none to give. That refusal is itself the reason the
        # documents arrive as entries and land in B.2 by fallback.
        expense = self.company_data["default_account_expense"]
        payable = self.company_data["default_account_payable"]
        move = self.env["account.move"].create({
            "move_type": "entry",
            "date": "2026-06-12",
            "journal_id": self.company_data["default_journal_misc"].id,
            "line_ids": [
                (0, 0, {"account_id": expense.id, "debit": 12.0, "credit": 0.0,
                        "tax_ids": [(6, 0, self.tax_purchase.ids)]}),
                (0, 0, {"account_id": payable.id, "debit": 0.0, "credit": 12.0}),
            ],
        })
        move.action_post()
        line = move.line_ids.filtered(
            lambda l: l.tax_ids and not l.tax_line_id)[:1]
        self.assertTrue(line, "the fixture produced no taxed base line")
        self.assertFalse(move.partner_id, "the fixture must have no counterparty")
        self.assertEqual(
            line._cssk_resolve_section_code(), "B.3",
            "a received document with no counterparty cannot be a B.2 row")

    def test_a_received_invoice_with_a_supplier_is_still_B2(self):
        """The exclusion above must not swallow ordinary purchases.

        Without this the rule could be 'everything inbound is B.3', which
        would be far worse than the defect it fixes — B.2 is the bulk of any
        real statement.
        """
        supplier = self.env["res.partner"].create({
            "name": "Dodavatel s IC DPH", "vat": "SK2020317068",
            "country_id": self.env.ref("base.sk").id,
        })
        invoice = self.init_invoice(
            "in_invoice", partner=supplier, invoice_date="2026-06-13",
            amounts=[100.0], taxes=self.tax_purchase, post=True,
        )
        line = invoice.line_ids.filtered(
            lambda l: l.tax_ids and not l.tax_line_id)[:1]
        self.assertEqual(line._cssk_resolve_section_code(), "B.2")

    def test_install_assigns_the_section_on_lines_that_predate_the_resolver(self):
        """The stored section must not stay as the base module computed it.

        ``l10n_cssk_kv_kh_base`` creates the column and Odoo fills it for the
        existing rows right then — with the base resolver, which returns
        ``False``. On a database with history that left every line without a
        section and every statement empty. Reproduce that state in SQL (the
        ORM cannot produce it, which is the point) and run the hook's repair.
        """
        from odoo.addons.l10n_sk_kv_dph.hooks import _recompute_section_codes

        supplier = self.env["res.partner"].create({
            "name": "Dodavatel pred instalaciou", "vat": "SK2020317068",
            "country_id": self.env.ref("base.sk").id,
        })
        invoice = self.init_invoice(
            "in_invoice", partner=supplier, invoice_date="2026-01-13",
            amounts=[100.0], taxes=self.tax_purchase, post=True,
        )
        line = invoice.line_ids.filtered(
            lambda l: l.tax_ids and not l.tax_line_id)[:1]
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE account_move_line SET cssk_control_section_code = NULL "
            "WHERE move_id = %s", (invoice.id,))
        line.invalidate_recordset(["cssk_control_section_code"])
        self.assertFalse(line.cssk_control_section_code)

        self.assertGreaterEqual(
            _recompute_section_codes(self.env, "SK", "test"), 1)
        self.assertEqual(line.cssk_control_section_code, "B.2")

    def test_an_eu_customer_without_a_vat_number_is_not_an_intra_eu_supply(self):
        """Geography alone is not the test — the SUPPLY decides.

        "EU counterparty ⇒ intra-EU supply" holds only where the customer is
        VAT-registered in another member state: § 43 is exempt with credit
        precisely because the acquirer self-assesses. Supply to a NON-taxable
        EU person and the place of supply is Slovakia, Slovak VAT is charged,
        and it is an ordinary domestic taxable supply.

        Found by the MRP extractor on a Czech customer with no VAT number, in
        both years: 450.00 + 90.00 in 2024-09 and 100.00 + 23.00 in 2025-08,
        both reaching r03/r04 on the return correctly and vanishing from KV DPH
        entirely.

        The section is D.2, not A.1: a private person is not a taxable person
        whatever the country (confirmed by an accountant 2026-09-21, "Fyzické
        osoby nepodnikatelia idú do D2"). The MRP accountant had filed these
        two in A.1; that filing is the outlier.
        """
        czech = self.env["res.partner"].create({
            "name": "Romana bez IC DPH",
            "country_id": self.env.ref("base.cz").id,
        })
        invoice = self.init_invoice(
            "out_invoice", partner=czech, invoice_date="2026-06-10",
            amounts=[450.0], taxes=self.tax_sale, post=True,
        )
        line = invoice.line_ids.filtered(
            lambda l: l.tax_ids and not l.tax_line_id)[:1]
        self.assertTrue(line, "the fixture invoice carries no taxed base line")
        self.assertTrue(
            line._cssk_is_eu_counterparty(),
            "the partner is in the EU — the geography helper must still say so")
        self.assertEqual(
            line._cssk_resolve_section_code(), "D.2",
            "a private person from another member state taxed at Slovak rates "
            "is a D.2 supply, as a Slovak one is")

    def test_an_eu_business_without_a_vat_number_stays_in_a1(self):
        """The D.2 rule is about the customer, not the country: an EU business
        recorded with its registry number and no VAT number is a taxable
        person and stays in A.1, exactly as a Slovak neplatiteľ does."""
        firm = self.env["res.partner"].create({
            "name": "Firma bez DIC", "is_company": True,
            "country_id": self.env.ref("base.cz").id,
            "company_registry": "27082440",
        })
        invoice = self.init_invoice(
            "out_invoice", partner=firm, invoice_date="2026-06-10",
            amounts=[300.0], taxes=self.tax_sale, post=True,
        )
        line = invoice.line_ids.filtered(
            lambda l: l.tax_ids and not l.tax_line_id)[:1]
        self.assertEqual(line._cssk_resolve_section_code(), "A.1")

    def test_a_vat_registered_eu_customer_is_still_excluded(self):
        """The exclusion the fix must not break.

        A genuine § 43 supply is zero-rated and belongs to the EC sales list,
        not to KV DPH. Without this the test above would pass against a
        resolver that had simply stopped excluding intra-EU supplies at all.
        """
        eu = self.env["res.partner"].create({
            "name": "Odberatel s IC DPH",
            "country_id": self.env.ref("base.cz").id,
            "vat": "CZ24847658",
        })
        zero = self.env["account.tax"].search([
            ("company_id", "=", self.company.id), ("amount", "=", 0.0),
            # Percent, not merely amount 0: Odoo's test fixture `complex_tax`
            # is a GROUP (amount 0) with a 20 % child, and this search used to
            # pick it — passing only because the whole group was once treated
            # as deferred over its on-payment child.
            ("amount_type", "=", "percent"),
            ("type_tax_use", "=", "sale"),
            ("cssk_control_is_reverse_charge", "=", False),  # a PLAIN 0% supply
        ], limit=1)
        if not zero:
            self.skipTest("no zero-rated sale tax in this chart")
        invoice = self.init_invoice(
            "out_invoice", partner=eu, invoice_date="2026-06-11",
            amounts=[450.0], taxes=zero, post=True,
        )
        line = invoice.line_ids.filtered(
            lambda l: l.tax_ids and not l.tax_line_id)[:1]
        self.assertFalse(
            line._cssk_resolve_section_code(),
            "a zero-rated supply to a VAT-registered EU customer is a § 43 "
            "intra-EU supply and belongs to the EC sales list, not KV DPH")

    def test_a1_and_b2(self):
        out = self.init_invoice(
            "out_invoice", partner=self.partner_a,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_sale, post=True,
        )
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a,
            invoice_date="2026-06-12", amounts=[500.0],
            taxes=self.tax_purchase, post=True,
        )
        out_base = out.line_ids.filtered(lambda l: l.tax_ids)
        bill_base = bill.line_ids.filtered(lambda l: l.tax_ids)
        self.assertEqual(out_base.cssk_control_section_code, "A.1")
        self.assertEqual(bill_base.cssk_control_section_code, "B.2")

        st = self._make_statement()
        st.action_compute_lines()
        self.assertEqual(st.state, "preview")

        self.assertEqual(len(st.sk_section_a1_ids), 1)
        a1 = st.sk_section_a1_ids
        self.assertAlmostEqual(a1.tax_base_amount, 1000.0, places=2)
        self.assertAlmostEqual(a1.tax_amount, 1000.0 * self.rate_s / 100.0, 2)
        self.assertAlmostEqual(a1.tax_rate, self.rate_s, places=2)
        self.assertEqual(a1.partner_vat_stripped, "2023456787")

        self.assertEqual(len(st.sk_section_b2_ids), 1)
        b2 = st.sk_section_b2_ids
        self.assertAlmostEqual(b2.tax_base_amount, 500.0, places=2)
        self.assertAlmostEqual(b2.tax_amount, 500.0 * self.rate_p / 100.0, 2)

    # ------------------------------------------------------------------
    # Odpočítaná daň (O / OR) — the field the XML files
    # ------------------------------------------------------------------
    def test_a_received_row_states_the_deduction_it_files(self):
        """``deducted_amount`` must carry the figure, not sit at 0.00.

        The template filed the full ``tax_amount`` as attribute ``O`` while
        the row's own ``deducted_amount`` stayed 0.00 — the record said one
        thing and the filing said another, and a comparison against a filed
        statement reported every B.1/B.2 row as a difference in that position
        with nothing actually wrong in the XML. The row now states what it
        files. Output rows have no deduction and keep 0.00.
        """
        self.init_invoice(
            "out_invoice", partner=self.partner_a,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_sale, post=True,
        )
        self.init_invoice(
            "in_invoice", partner=self.partner_a,
            invoice_date="2026-06-12", amounts=[500.0],
            taxes=self.tax_purchase, post=True,
        )
        st = self._make_statement()
        st.action_compute_lines()

        b2 = st.sk_section_b2_ids
        self.assertEqual(len(b2), 1)
        self.assertTrue(b2.tax_amount, "fixture: the bill must charge tax")
        self.assertAlmostEqual(b2.deducted_amount, b2.tax_amount, places=2)

        a1 = st.sk_section_a1_ids
        self.assertEqual(len(a1), 1)
        self.assertAlmostEqual(
            a1.deducted_amount, 0.0, places=2,
            msg="A.1 is output tax — there is nothing to deduct and the form "
                "has no column for it")

    def test_the_filed_O_follows_the_row_not_the_tax(self):
        """An overridden deduction must reach the XML.

        This is the half that makes the field worth having. A company on the
        § 50 koeficient deducts a fraction of the tax it was charged; the
        coefficient is a fact about the company, so the row is overridden by
        hand. If ``O`` were still rendered from ``tax_amount`` the override
        would be invisible in the filing — which is what it was.
        """
        self.init_invoice(
            "in_invoice", partner=self.partner_a,
            invoice_date="2026-06-12", amounts=[500.0],
            taxes=self.tax_purchase, post=True,
        )
        st = self._make_statement()
        st.action_compute_lines()
        b2 = st.sk_section_b2_ids
        self.assertEqual(len(b2), 1)
        full = b2.tax_amount
        self.assertTrue(full, "fixture: the bill must charge tax")
        b2.deducted_amount = round(full * 0.13, 2)

        st.action_export_xml()
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        ns = {"k": "https://ekr.financnasprava.sk/Formulare/XSD/"
                   "kv_dph_2025.xsd"}
        rows = root.findall(".//k:B2", ns)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].get("D"), "%.2f" % full,
                         "the tax charged is unchanged")
        self.assertEqual(rows[0].get("O"), "%.2f" % round(full * 0.13, 2),
                         "the filing must report the deduction claimed")

    def test_a_zero_rated_export_is_not_a_domestic_supply(self):
        """§ 47 export to a NON-EU customer must not land in A.1.

        A.1 reports a supply on which a tax liability arose under § 19,
        "okrem dodania, ktoré je oslobodené od dane". An export is exempt, and
        it reaches this branch because the intra-EU exclusion above does not
        catch it — the customer is not in the EU. The resolver used to return
        "A.1" unconditionally for any outbound non-reverse-charge line, so the
        export was reported as a domestic taxable supply.

        Found by the i6 extractor on real data: four `0% EXP` lines carrying
        97 999 of base in December 2024. The export belongs on the return
        (r15/r16) and nowhere in KV DPH.
        """
        swiss = self.env["res.partner"].create({
            "name": "Non-EU Customer", "country_id": self.env.ref("base.ch").id,
        })
        # NOT an EU-specific zero rate: an intra-EU supply is excluded a few
        # lines earlier by the counterparty test, which would make this pass
        # for the wrong reason. The export must be excluded on its RATE.
        zero_rated = self.env["account.tax"].search([
            ("company_id", "=", self.company.id), ("type_tax_use", "=", "sale"),
            ("amount", "=", 0.0), ("amount_type", "=", "percent"),
            ("name", "not like", "EU"),
            ("cssk_control_is_reverse_charge", "=", False),  # not the §69/12 A.2 tax
        ], limit=1)
        self.assertTrue(zero_rated, "the SK chart ships no zero-rated sale tax")

        export = self.init_invoice(
            "out_invoice", partner=swiss, invoice_date="2026-06-14",
            amounts=[97999.0], taxes=zero_rated, post=True,
        )
        base = export.line_ids.filtered(lambda l: l.tax_ids)
        self.assertTrue(base, "the export invoice has no taxed line")
        sections = base.mapped("cssk_control_section_code")
        self.assertFalse(
            [c for c in sections if c],
            "a zero-rated export was classified into %s" % (sections,),
        )

        st = self._make_statement()
        st.action_compute_lines()
        self.assertFalse(
            st.sk_section_a1_ids.filtered(
                lambda r: abs(r.tax_base_amount - 97999.0) < 0.01),
            "the export reached A.1 anyway",
        )

    def test_a_zero_rated_purchase_is_not_a_B2_row(self):
        """B.2 reports the tax deducted; a 0 % bill deducts none.

        Reported by an external accountant: a 0 % purchase tax put a row with
        D="0.00" into B.2, which FS SR rejects. The SK chart ships no 0 %
        purchase tax, so the test makes the one she had."""
        zero = self.tax_purchase.copy({"name": "0% purchase", "amount": 0.0})
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2026-06-12",
            amounts=[400.0], taxes=zero, post=True)
        self.assertFalse(
            [c for c in bill.line_ids.mapped("cssk_control_section_code") if c])
        simplified = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2026-06-12",
            amounts=[40.0], taxes=zero, post=False)
        simplified.l10n_sk_kv_is_simplified = True
        simplified.action_post()
        self.assertFalse(
            [c for c in simplified.line_ids.mapped("cssk_control_section_code")
             if c], "nor is it a B.3 receipt")
        st = self._make_statement()
        st.action_compute_lines()
        self.assertFalse(st.sk_section_b2_ids)
        self.assertFalse(st.sk_section_b31_ids)

    def test_a_domestic_reverse_charge_is_still_reported_though_zero_rated(self):
        """The exclusion must not empty A.2, which is zero-rated by design.

        A § 69 ods. 12 domestic reverse charge carries no tax on the supplier's
        side — that is the mechanism, not an exemption — so testing the rate
        there rather than only on the A.1 branch would silently delete the
        section that exists to report it.
        """
        # The flag is CONSTRUCTED rather than searched for. This chart ships
        # no outbound reverse-charge tax, so searching skips the test — and a
        # guard that never runs is exactly the thing it is guarding against.
        rc = self.env["account.tax"].search([
            ("company_id", "=", self.company.id), ("type_tax_use", "=", "sale"),
            ("amount", "=", 0.0), ("amount_type", "=", "percent"),
            ("name", "not like", "EU"),
        ], limit=1)
        self.assertTrue(rc, "the SK chart ships no zero-rated sale tax")
        rc.cssk_control_is_reverse_charge = True
        inv = self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-15",
            amounts=[2000.0], taxes=rc, post=True,
        )
        base = inv.line_ids.filtered(lambda l: l.tax_ids)
        sections = [c for c in base.mapped("cssk_control_section_code") if c]
        self.assertEqual(
            sections, ["A.2"],
            "a domestic reverse charge is zero-rated and still belongs in "
            "A.2; got %s" % (sections,),
        )

    def test_a_correction_posted_as_an_entry_reaches_c1(self):
        """An imported credit note is often a journal ENTRY, not a refund.

        The resolver decides C.1 and C.2 from `move_type in ('out_refund',
        'in_refund')`, which an entry does not satisfy — so a correction
        imported as a ledger entry reported as an ordinary supply and oddiel
        C.1/C.2 could not be reached at all. Measured: the i6 agenda is 16 926
        entries against 4 invoices, and the Money import demotes 22 credit
        notes. `cssk_vat_correction` lets the document declare what its move
        type cannot say.
        """
        account = self.company_data["default_account_revenue"]
        move = self.env["account.move"].create({
            "move_type": "entry",
            "date": "2026-06-20",
            "partner_id": self.partner_a.id,
            "cssk_vat_direction": "sale",
            "cssk_vat_correction": "yes",
            "line_ids": [
                (0, 0, {"name": "oprava", "account_id": account.id,
                        "credit": 500.0, "partner_id": self.partner_a.id,
                        "tax_ids": [(6, 0, self.tax_sale.ids)]}),
                (0, 0, {"name": "contra", "account_id": account.id,
                        "debit": 500.0, "partner_id": self.partner_a.id}),
            ],
        })
        move.action_post()
        base = move.line_ids.filtered(lambda l: l.tax_ids)
        sections = [c for c in base.mapped("cssk_control_section_code") if c]
        self.assertEqual(
            sections, ["C.1"],
            "a declared correction on an entry must reach C.1; got %s"
            % (sections,),
        )

    def test_an_undeclared_entry_still_falls_back_to_its_move_type(self):
        """Declaring is optional: an invoice already knows what it is."""
        inv = self.init_invoice(
            "out_refund", partner=self.partner_a, invoice_date="2026-06-21",
            amounts=[300.0], taxes=self.tax_sale, post=True,
        )
        self.assertFalse(
            inv.cssk_vat_correction,
            "nothing should set the flag on an ordinary refund",
        )
        base = inv.line_ids.filtered(lambda l: l.tax_ids)
        self.assertEqual(
            [c for c in base.mapped("cssk_control_section_code") if c], ["C.1"],
            "a real out_refund must still reach C.1 without the declaration",
        )

    def test_a_zero_rated_correction_is_not_a_C1_row(self):
        """C.1 corrects what A.1 reported, so it inherits A.1's exclusion.

        A supply bearing no tax is not a taxable supply — that is why A.1 has a
        rate test — and a correction of one is not a correction to report. The
        branch was an unguarded catch-all in exactly the way A.1 was.

        Measured on the i6 agenda: C.1 produced 138 rows against 38 filed, and
        97 of the 100 extra were zero-rated with no reverse charge.
        """
        zero = self.env["account.tax"].search([
            ("company_id", "=", self.company.id), ("type_tax_use", "=", "sale"),
            ("amount", "=", 0.0), ("amount_type", "=", "percent"),
            ("name", "not like", "EU"),
        ], limit=1)
        self.assertTrue(zero, "the SK chart ships no zero-rated sale tax")
        credit = self.init_invoice(
            "out_refund", partner=self.partner_a, invoice_date="2026-06-18",
            amounts=[500.0], taxes=zero, post=True,
        )
        base = credit.line_ids.filtered(lambda l: l.tax_ids)
        self.assertFalse(
            [c for c in base.mapped("cssk_control_section_code") if c],
            "a zero-rated credit note must not reach C.1",
        )

    def test_a_rated_correction_still_reaches_C1(self):
        """The guard must not empty the section it protects."""
        credit = self.init_invoice(
            "out_refund", partner=self.partner_a, invoice_date="2026-06-19",
            amounts=[500.0], taxes=self.tax_sale, post=True,
        )
        base = credit.line_ids.filtered(lambda l: l.tax_ids)
        self.assertEqual(
            [c for c in base.mapped("cssk_control_section_code") if c], ["C.1"],
            "an ordinary rated credit note is exactly what C.1 reports",
        )

    def test_dodatocny_delta_kopr(self):
        """A dodatočný KV reports only the delta vs the original, tagged kód
        opravy: a forgotten invoice appears once with KOpr=2; unchanged rows are
        dropped. Mirrors the real DPH-2026_03 / KVDPH-2026_03-D case."""
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[100.0], taxes=self.tax_sale, post=True)
        orig = self._make_statement()
        orig.action_compute_lines()
        orig.action_export_xml()
        orig.action_submit()
        self.assertEqual(len(orig.sk_section_a1_ids), 1)

        action = orig.action_create_amendment()
        amend = self.env["cssk.control.statement"].browse(action["res_id"])
        ddp = self._sk_type("D")
        self.assertTrue(ddp, "dodatočný submission type missing")
        amend.statement_type_id = ddp[0].id

        # A forgotten invoice is discovered and booked into the same period.
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-20",
            amounts=[4380.0], taxes=self.tax_sale, post=True)
        amend.action_compute_lines()

        # Delta only: the forgotten invoice with KOpr=2; the unchanged original
        # row is NOT repeated.
        self.assertEqual(len(amend.sk_section_a1_ids), 1)
        row = amend.sk_section_a1_ids
        self.assertEqual(row.kod_opravy, "2")
        self.assertAlmostEqual(row.tax_base_amount, 4380.0, places=2)

        # Exports + validates against the official XSD, with Druh=D and KOpr=2.
        amend.action_export_xml()
        root = etree.fromstring(base64.b64decode(amend.xml_attachment_id.datas))
        ns = {"k": "https://ekr.financnasprava.sk/Formulare/XSD/kv_dph_2025.xsd"}
        a1 = root.findall(".//k:A1", ns)
        self.assertEqual(len(a1), 1)
        self.assertEqual(a1[0].get("KOpr"), "2")
        self.assertEqual(root.findtext(".//k:Identifikacia/k:Druh", namespaces=ns), "D")

    def test_dodatocny_chaining(self):
        """Chained dodatočné: the 2nd amendment diffs against the CUMULATIVE state
        of the 1st (not its delta), so it reports only the newly-added invoice —
        the 1st amendment's invoice is part of the baseline now, not repeated."""
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[100.0], taxes=self.tax_sale, post=True)
        orig = self._make_statement()
        orig.action_compute_lines()
        orig.action_export_xml()
        orig.action_submit()
        ddp = self._sk_type("D")[0]

        # 1st dodatočný — forgotten invoice B
        a1 = self.env["cssk.control.statement"].browse(
            orig.action_create_amendment()["res_id"])
        a1.statement_type_id = ddp.id
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-15",
            amounts=[4380.0], taxes=self.tax_sale, post=True)
        a1.action_compute_lines()
        self.assertEqual(len(a1.sk_section_a1_ids), 1)
        self.assertAlmostEqual(a1.sk_section_a1_ids.tax_base_amount, 4380.0, 2)
        a1.action_export_xml()
        a1.action_submit()

        # 2nd dodatočný — created FROM the 1st, another forgotten invoice C
        a2 = self.env["cssk.control.statement"].browse(
            a1.action_create_amendment()["res_id"])
        self.assertEqual(a2.original_return_id, a1)
        a2.statement_type_id = ddp.id
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-20",
            amounts=[200.0], taxes=self.tax_sale, post=True)
        a2.action_compute_lines()

        # Only invoice C, KOpr=2 — invoice B is NOT repeated.
        self.assertEqual(len(a2.sk_section_a1_ids), 1)
        row = a2.sk_section_a1_ids
        self.assertEqual(row.kod_opravy, "2")
        self.assertAlmostEqual(row.tax_base_amount, 200.0, places=2)

    def test_kontroly(self):
        """suma dane = základ × sadzba per detail row: clean on a normal sale,
        and a tampered daň is flagged (KV_RATE)."""
        self.init_invoice(
            "out_invoice", partner=self.partner_a,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_sale, post=True,
        )
        st = self._make_statement()
        st.action_compute_lines()
        self.assertEqual(
            st.check_kontroly(), [],
            "a correctly-taxed A.1 row must pass the rate kontroly")

        # Break daň on the A.1 row (rate no longer = suma/základ).
        st.sk_section_a1_ids.tax_amount = 1.0
        codes = [v["code"] for v in st.check_kontroly()]
        self.assertIn("KV_RATE", codes,
                      "kontroly must flag suma dane != základ × sadzba")

    def test_an_aggregate_row_names_the_documents_it_sums(self):
        """B.3.1 and D.2 name no document in the form, so the drill-down is
        the only way to see what they contain — asked for by an accountant
        who could see the B.3.1 total and not the receipts behind it."""
        receipt = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2026-06-05",
            amounts=[100.0], taxes=self.tax_purchase, post=False)
        receipt.l10n_sk_kv_is_simplified = True
        receipt.action_post()
        person = self.env["res.partner"].create({
            "name": "Jana Nováková", "country_id": self.env.ref("base.sk").id})
        sale = self.init_invoice(
            "out_invoice", partner=person, invoice_date="2026-06-07",
            amounts=[50.0], taxes=self.tax_sale, post=True)
        st = self._make_statement()
        st.action_compute_lines()
        b31 = st.sk_section_b31_ids
        self.assertEqual(b31.source_move_line_ids.move_id, receipt)
        self.assertTrue(b31.source_reconciles)
        self.assertEqual(
            b31.action_view_source_lines()["domain"],
            [("id", "in", b31.source_move_line_ids.ids)])
        d2 = st.sk_section_d2_ids
        self.assertEqual(d2.source_move_line_ids.move_id, sale)
        self.assertEqual(d2.row_count, 1)
        self.assertTrue(d2.source_reconciles)

    def test_supply_to_a_private_individual_goes_to_d2_not_a1(self):
        """A.1 is for invoiced supplies to taxable persons; D.2 aggregates the
        rest (§ 78a ods. 2 písm. d).

        Measured against 32 filed control statements of a Slovak s.r.o.: five
        supplies to private individuals, 731.48 in four periods, filed in D.2
        to the cent while our resolver put them in A.1.
        """
        person = self.env["res.partner"].create({"name": "Súkromná osoba"})
        self.assertFalse(person.vat or person.company_registry,
                         "premise: neither IČ DPH nor IČO")
        inv = self.init_invoice(
            "out_invoice", partner=person, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale, post=True)
        line = inv.line_ids.filtered("tax_ids")[:1]
        self.assertEqual(line.cssk_control_section_code, "D.2")

        st = self._make_statement()
        st.action_compute_lines()
        self.assertFalse(st.sk_section_a1_ids,
                         "nothing should reach the A.1 detail section")
        self.assertEqual(len(st.sk_section_d2_ids), 1)
        self.assertAlmostEqual(st.sk_section_d2_ids.total_tax_base, 1000.0, 2)

    def test_d2_warns_when_the_customer_looks_like_a_business(self):
        """The proxy fails invisibly in one direction; this is the alarm.

        A partner with no IČ DPH and no IČO reaches D.2 by design. But D.2 is a
        total — the customer never appears in the výkaz — so a business whose
        IČO was simply never recorded is aggregated away with no way for the
        filer to notice. Core hid ``company_registry`` on CZ/SK natural persons
        until l10n_cssk_core 7babaf6, so that data gap is real on any older
        database. Warning, not error: genuine retail D.2 must still export.
        """
        firm = self.env["res.partner"].create({
            "name": "Firma bez IČO", "is_company": True})
        self.assertFalse(firm.vat or firm.company_registry)
        self.init_invoice(
            "out_invoice", partner=firm, invoice_date="2026-06-10",
            amounts=[300.0], taxes=self.tax_sale, post=True)
        st = self._make_statement()
        st.action_compute_lines()
        self.assertTrue(st.sk_section_d2_ids, "premise: it lands in D.2")

        flagged = [v for v in st.check_kontroly()
                   if v["code"] == "KV_D2_BUSINESS"]
        self.assertTrue(flagged, "a company in D.2 must be flagged")
        self.assertEqual(flagged[0]["severity"], "warning",
                         "retail D.2 is normal — this must not block export")
        self.assertIn("Firma bez IČO", flagged[0]["detail"])

    def test_d2_is_quiet_for_a_genuine_private_individual(self):
        """The other half: the check must not cry wolf on ordinary retail."""
        person = self.env["res.partner"].create({"name": "Súkromná osoba"})
        self.init_invoice(
            "out_invoice", partner=person, invoice_date="2026-06-10",
            amounts=[300.0], taxes=self.tax_sale, post=True)
        st = self._make_statement()
        st.action_compute_lines()
        self.assertTrue(st.sk_section_d2_ids)
        self.assertFalse([v for v in st.check_kontroly()
                          if v["code"] == "KV_D2_BUSINESS"])

    def test_unregistered_business_stays_in_a1(self):
        """The trap the IČO test exists for.

        A živnostník or s.r.o. under the registration threshold holds no
        IČ DPH but IS a zdaniteľná osoba, so § 72 obliges an invoice and it
        belongs in A.1 — with ``Odb`` omitted, which A1/@Odb ``use="optional"``
        permits in every vzor. Keying the rule on "has no IČ DPH" instead of
        "has no IČO" would misfile this, and on the measured agenda it would
        have moved three real supplies (148.62) out of the section the
        accountant filed them in.
        """
        neplatitel = self.env["res.partner"].create({
            "name": "Neplatiteľ s.r.o.", "company_registry": "50832778"})
        self.assertFalse(neplatitel.vat, "premise: no IČ DPH")
        inv = self.init_invoice(
            "out_invoice", partner=neplatitel, invoice_date="2026-06-10",
            amounts=[500.0], taxes=self.tax_sale, post=True)
        line = inv.line_ids.filtered("tax_ids")[:1]
        self.assertEqual(line.cssk_control_section_code, "A.1")

        st = self._make_statement()
        st.action_compute_lines()
        self.assertEqual(len(st.sk_section_a1_ids), 1)
        self.assertFalse(st.sk_section_a1_ids.partner_vat,
                         "A.1 carries no IČ DPH here, and that is legal")
        self.assertFalse(st.sk_section_d2_ids)

    def test_b3_below_threshold_aggregates_in_b31(self):
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a,
            invoice_date="2026-06-05", amounts=[100.0],
            taxes=self.tax_purchase, post=False,
        )
        bill.l10n_sk_kv_is_simplified = True
        bill.action_post()
        self.assertEqual(
            bill.line_ids.filtered(
                lambda l: l.tax_ids
            ).cssk_control_section_code,
            "B.3",
        )
        st = self._make_statement()
        st.action_compute_lines()
        # Small VAT (< 3000) → single aggregate in B.3.1, nothing in B.3.2.
        self.assertEqual(len(st.sk_section_b31_ids), 1)
        self.assertEqual(len(st.sk_section_b32_ids), 0)
        self.assertAlmostEqual(
            st.sk_section_b31_ids.total_tax_amount,
            100.0 * self.rate_p / 100.0, 2,
        )

    def test_a_summary_row_with_no_tax_is_caught(self):
        """KV_NO_TAX must see an AGGREGATED base filed with no daň.

        The check guarded on ``"tax_rate" in row._fields`` and skipped every
        summary section wholesale (SK B.3.1, CZ A.5/B.3). So the one shape it
        exists to stop — a taxable base reporting no tax, which cannot be
        described and therefore cannot be filed — left the building whenever it
        was aggregated rather than itemised, in a schema-valid document that
        reported green.
        """
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a,
            invoice_date="2026-06-05", amounts=[100.0],
            taxes=self.tax_purchase, post=False,
        )
        bill.l10n_sk_kv_is_simplified = True
        bill.action_post()
        st = self._make_statement()
        st.action_compute_lines()
        row = st.sk_section_b31_ids
        self.assertEqual(len(row), 1, "premise: the aggregate exists")
        self.assertNotIn(
            "KV_NO_TAX", [v["code"] for v in st.check_kontroly()],
            "premise: as computed it carries its daň")

        row.total_tax_amount = 0.0
        flagged = [v for v in st.check_kontroly() if v["code"] == "KV_NO_TAX"]
        self.assertTrue(
            flagged, "an aggregated base with no daň must be caught too")
        self.assertEqual(flagged[0]["severity"], "error",
                         "it cannot be filed, so it blocks the export")

    def test_b3_above_threshold_lists_in_b32(self):
        # Pick a base whose VAT comfortably exceeds the 3 000 EUR threshold,
        # whatever the chart rate is.
        base = round(4000.0 * 100.0 / self.rate_p, 2)
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a,
            invoice_date="2026-06-07", amounts=[base],
            taxes=self.tax_purchase, post=False,
        )
        bill.l10n_sk_kv_is_simplified = True
        bill.action_post()
        st = self._make_statement()
        st.action_compute_lines()
        self.assertEqual(len(st.sk_section_b31_ids), 0)
        self.assertEqual(len(st.sk_section_b32_ids), 1)
        b32 = st.sk_section_b32_ids
        self.assertEqual(b32.partner_id, self.partner_a)
        self.assertGreaterEqual(b32.total_tax_amount, 3000.0)
        self.assertEqual(b32.row_count, 1)

    def test_price_included_tax_amounts(self):
        """Price-INCLUDED tax: the posted base-line balance is already NET, so
        the KV row must carry the invoice's actual base/tax — the engine must
        not re-extract an 'included' tax from an amount that no longer
        contains it (regression: understated base+tax on KV rows)."""
        tax_incl = self.tax_sale.copy({
            "name": "%s incl (test)" % self.rate_s,
            "price_include_override": "tax_included",
        })
        gross = round(1000.0 * (1 + self.rate_s / 100.0), 2)
        inv = self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[gross], taxes=tax_incl, post=True)
        self.assertAlmostEqual(inv.amount_untaxed, 1000.0, places=2)
        self.assertAlmostEqual(
            inv.amount_tax, 1000.0 * self.rate_s / 100.0, places=2)

        base_line = inv.line_ids.filtered(lambda l: l.tax_ids)
        base, tax = base_line._cssk_base_and_tax_amounts()
        self.assertAlmostEqual(base, inv.amount_untaxed, places=2)
        self.assertAlmostEqual(tax, inv.amount_tax, places=2)

        st = self._make_statement()
        st.action_compute_lines()
        self.assertEqual(len(st.sk_section_a1_ids), 1)
        a1 = st.sk_section_a1_ids
        self.assertAlmostEqual(a1.tax_base_amount, inv.amount_untaxed, places=2)
        self.assertAlmostEqual(a1.tax_amount, inv.amount_tax, places=2)

    def test_rc_and_normal_tax_mixed_line(self):
        """A line carrying one reverse-charge tax AND one normal tax: only the
        RC leg is replaced by the gross self-assessed amount (base × RC rate);
        the normal tax keeps its computed amount (regression: the RC branch
        used to replace the tax amount of ALL taxes on the line)."""
        tax_acc = self.company_data["default_account_tax_purchase"][:1]
        rc = self.env["account.tax"].create({
            "name": "RC 23 (test)",
            "amount": 23.0,
            "amount_type": "percent",
            "type_tax_use": "purchase",
            "cssk_control_is_reverse_charge": True,
            "repartition_line_ids": [
                Command.create({"document_type": "invoice",
                                "repartition_type": "base"}),
                Command.create({"document_type": "invoice",
                                "repartition_type": "tax",
                                "factor_percent": 100.0,
                                "account_id": tax_acc.id}),
                Command.create({"document_type": "invoice",
                                "repartition_type": "tax",
                                "factor_percent": -100.0,
                                "account_id": tax_acc.id}),
                Command.create({"document_type": "refund",
                                "repartition_type": "base"}),
                Command.create({"document_type": "refund",
                                "repartition_type": "tax",
                                "factor_percent": 100.0,
                                "account_id": tax_acc.id}),
                Command.create({"document_type": "refund",
                                "repartition_type": "tax",
                                "factor_percent": -100.0,
                                "account_id": tax_acc.id}),
            ],
        })
        # Sanity: the RC tax nets to 0 in the posted document (self-assessed
        # output + its deduction).
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2026-06-12",
            amounts=[1000.0], taxes=rc + self.tax_purchase, post=True)
        self.assertAlmostEqual(
            bill.amount_tax, 1000.0 * self.rate_p / 100.0, places=2)

        base_line = bill.line_ids.filtered(lambda l: l.tax_ids)
        base, tax = base_line._cssk_base_and_tax_amounts()
        self.assertAlmostEqual(base, 1000.0, places=2)
        # RC leg: gross self-assessed 23 %; normal leg: its computed amount.
        self.assertAlmostEqual(
            tax, 1000.0 * (23.0 + self.rate_p) / 100.0, places=2)

    def test_an_optional_counterparty_vat_does_not_block_the_export(self):
        """A.1 does NOT require the counterparty's IČ DPH and must not be
        guarded as though it did.

        `Odb` is `use="optional"` on A.1 in all four vzory, and `IcDphType` is
        a union including `IcDphTretichStranType` — a third-country member
        exists precisely because a counterparty may hold no EU VAT number. So
        a row without one is ordinary, not defective.

        This assertion is the REVERSE of the one it replaces, which blocked
        here and was wrong. Recording why, because the failure mode is the
        interesting part: the strict guard blocked all 150 periods of one
        agenda, and the obvious way past it was to backfill the 98 partners it
        named — of which only 47 hold a real VAT number, the rest carrying the
        literal "0", a bare country code, or the word "IRELAND". The guard
        would have been satisfied by writing 51 invented VAT numbers into a
        customer's partner master. **A guard stricter than its form does not
        fail safe; it pushes the person past it into falsifying the data it
        was protecting.**
        """
        self.init_invoice(
            "out_invoice", partner=self.partner_a,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_sale, post=True,
        )
        st = self._make_statement()
        st.action_compute_lines()
        st.sk_section_a1_ids.partner_vat = False
        st.action_export_xml()
        self.assertEqual(st.state, "exported")
        xml = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        # The document is namespaced, so match on the local name.
        a1 = next((el for el in xml.iter()
                   if etree.QName(el).localname == "A1"), None)
        self.assertIsNotNone(a1, "expected an A1 row in the export")
        self.assertIsNone(
            a1.get("Odb"),
            "an absent optional attribute is omitted, never emitted empty — "
            "an empty Odb fails the IcDphType pattern")

    def test_a_foreign_counterparty_vat_in_a_domestic_section_blocks(self):
        """A.2, B.2 and B.3.2 are typed `IcDphSkType` (SK+10 digits) in every
        vzor, so they report domestic supplies only and a foreign number there
        is unfilable by construction — not missing data, a misclassification.

        Found by EXPORTING rather than comparing: 22 of 27 periods on one
        agenda failed with "value 'CZ27082440' is not accepted by the pattern
        'SK\\d{10}'", from a single partner carrying a Czech VAT with a Slovak
        country. The comparison had been scoring those rows as merely
        "differing" for hours. The XSD knew; nothing else did.
        """
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_purchase, post=True,
        )
        st = self._make_statement()
        st.action_compute_lines()
        rows = st.sk_section_b2_ids
        self.assertTrue(rows)
        rows.partner_vat = "CZ27082440"
        with self.assertRaises(UserError) as cm:
            st.action_export_xml()
        msg = str(cm.exception)
        self.assertIn("B.2", msg)
        self.assertIn(bill.name, msg, "the offending document must be named")
        self.assertNotIn("without the counterparty", msg,
                         "this is a classification problem, not a gap")
        self.assertEqual(st.state, "preview")

    def test_a_required_counterparty_vat_still_blocks(self):
        """B.2 DOES require it (`use="required"` in all four vzory), so the
        guard stays exactly there. The narrowing was of scope, not of rigour —
        and the over-strict version HID these, because B.1 refused first and
        the export never reached the sections where the requirement is real."""
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_purchase, post=True,
        )
        st = self._make_statement()
        st.action_compute_lines()
        rows = st.sk_section_b2_ids
        self.assertTrue(rows, "expected a B.2 row to guard")
        rows.partner_vat = False
        with self.assertRaises(UserError) as cm:
            st.action_export_xml()
        msg = str(cm.exception)
        self.assertIn("B.2", msg)
        self.assertIn(bill.name, msg, "the offending document must be named")
        self.assertEqual(st.state, "preview", "fail-early: nothing exported")

    def test_preflight_missing_supply_date_names_invoice(self):
        """Master-data preflight: a missing Den (XSD-required date) blocks the
        export early with the invoice number, instead of a cryptic XSD type
        error on an empty attribute."""
        inv = self.init_invoice(
            "out_invoice", partner=self.partner_a,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_sale, post=True,
        )
        st = self._make_statement()
        st.action_compute_lines()
        st.sk_section_a1_ids.supply_date = False
        with self.assertRaises(UserError) as cm:
            st.action_export_xml()
        msg = str(cm.exception)
        self.assertIn("Den", msg)
        self.assertIn(inv.name, msg, "the offending invoice must be named")

    def test_self_assessed_acquisition_booked_as_entry_reaches_b1(self):
        """A self-assessed acquisition is an internal document, not a bill.

        B.1 covers received supplies where the recipient is liable — including
        intra-EU goods acquisitions — so an entry carrying a reverse-charge
        purchase tax belongs there. Classifying only invoice-shaped moves drops
        it out of the statement silently.
        """
        # The flag is CONSTRUCTED, not searched for. Searching found nothing
        # in this chart and skipped — so this test, which covers the shape most
        # of a Slovak importer's purchase side takes, had never once executed.
        # A green suite containing a test that never runs is worse than a red
        # one: it actively discourages the next person from looking.
        rc_tax = self.env["account.tax"].search([
            ("company_id", "=", self.company.id),
            ("type_tax_use", "=", "purchase"),
            ("cssk_control_is_reverse_charge", "=", True),
        ], limit=1) or self.env["account.tax"].search([
            ("company_id", "=", self.company.id),
            ("type_tax_use", "=", "purchase"),
        ], limit=1)
        self.assertTrue(rc_tax, "the SK chart ships no purchase tax at all")
        rc_tax.cssk_control_is_reverse_charge = True
        account = self.company_data["default_account_expense"]
        move = self.env["account.move"].create({
            "move_type": "entry",
            "date": "2026-06-15",
            "partner_id": self.partner_a.id,
            "line_ids": [
                (0, 0, {"name": "acquisition", "account_id": account.id,
                        "debit": 1000.0, "partner_id": self.partner_a.id,
                        "tax_ids": [(6, 0, rc_tax.ids)]}),
                (0, 0, {"name": "contra", "account_id": account.id,
                        "credit": 1000.0, "partner_id": self.partner_a.id}),
            ],
        })
        move.action_post()
        base = move.line_ids.filtered(lambda line: line.tax_ids)
        sections = [c for c in base.mapped("cssk_control_section_code") if c]
        self.assertEqual(sections, ["B.1"], "got %s" % (sections,))

    def test_export_xml_validates_against_xsd(self):
        self.init_invoice(
            "out_invoice", partner=self.partner_a,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_sale, post=True,
        )
        st = self._make_statement()
        st.action_compute_lines()
        # The version ships an XSD, so this both renders and XSD-validates.
        self.assertTrue(st.version_id.xml_schema_data, "XSD not loaded")
        st.action_export_xml()
        self.assertEqual(st.state, "exported")
        self.assertTrue(st.xml_attachment_id)

        # Validates against the OFFICIAL kv_dph_2025.xsd (root KVDPH_2025,
        # namespaced, attribute-based rows).
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).localname, "KVDPH_2025")
        ns = {"k": "https://ekr.financnasprava.sk/Formulare/XSD/kv_dph_2025.xsd"}
        a1_rows = root.findall(".//k:A1", ns)
        self.assertEqual(len(a1_rows), 1)
        self.assertEqual(a1_rows[0].get("Z"), "1000.00")
        self.assertEqual(a1_rows[0].get("S"), str(int(round(self.rate_s))))
        self.assertEqual(root.findtext(".//k:Identifikacia/k:Obdobie/k:Rok", namespaces=ns), "2026")

    def _credit(self, **vals):
        credit = self.init_invoice(
            "out_refund", partner=self.partner_a, invoice_date="2026-06-19",
            amounts=[500.0], taxes=self.tax_sale)
        credit.write(vals)
        credit.action_post()
        return credit

    def _c1_fo(self, st):
        st.action_export_xml()
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        return [el.get("FO") for el in root.iter() if etree.QName(el).localname == "C1"]

    # --- C.1 / C.2: the invoice being corrected (FO) ------------------
    # Asked for by an accountant: "niekedy nie je možné vystaviť dobropis z
    # určitej faktúry, potom sa vytvára manuálne". Such a C.1 row used to file
    # the credit note's OWN number as FO, silently.

    def test_an_unlinked_credit_note_blocks_the_export(self):
        self._credit()
        st = self._make_statement()
        st.action_compute_lines()
        with self.assertRaisesRegex(UserError, "invoice being corrected"):
            st.action_export_xml()

    def test_a_number_of_spaces_is_no_number(self):
        self._credit(cssk_control_original_ref="   ")
        st = self._make_statement()
        st.action_compute_lines()
        with self.assertRaisesRegex(UserError, "invoice being corrected"):
            st.action_export_xml()

    def test_the_typed_number_is_filed_as_the_original(self):
        credit = self._credit(cssk_control_original_ref="FV2026/0042")
        st = self._make_statement()
        st.action_compute_lines()
        self.assertEqual(
            st._collect_sections_by_code()["C.1"].entry_ref_original,
            "FV2026/0042")
        self.assertEqual(self._c1_fo(st), ["FV2026/0042"])
        self.assertTrue(credit.name)

    def test_the_drill_down_shows_a_half_deduction(self):
        """Fuel at 50 %: one leg on the VAT account, one onto the expense.
        The drill-down columns show the whole VAT and the deducted half, so
        an accountant can see the split the row totals hide."""
        vat_leg = self.tax_purchase.invoice_repartition_line_ids.filtered(
            lambda r: r.repartition_type == "tax")[:1]

        def legs():
            return [
                Command.create({"repartition_type": "base"}),
                Command.create({"repartition_type": "tax", "factor_percent": 50,
                                "account_id": vat_leg.account_id.id,
                                "tag_ids": [Command.set(vat_leg.tag_ids.ids)]}),
                Command.create({"repartition_type": "tax", "factor_percent": 50}),
            ]
        half = self.tax_purchase.copy({
            "name": "%s PHM 50 %%" % self.tax_purchase.name,
            "invoice_repartition_line_ids": [Command.clear()] + legs(),
            "refund_repartition_line_ids": [Command.clear()] + legs(),
        })
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2026-06-12",
            amounts=[100.0], taxes=half, post=True)
        line = bill.invoice_line_ids
        rate = half.amount
        self.assertAlmostEqual(line.cssk_audit_base, 100.0)
        self.assertAlmostEqual(line.cssk_audit_rate, rate)
        self.assertAlmostEqual(line.cssk_audit_tax, rate)
        self.assertAlmostEqual(line.cssk_audit_deducted, rate / 2)

    def test_a_linked_original_wins_over_the_typed_number(self):
        invoice = self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-05",
            amounts=[500.0], taxes=self.tax_sale, post=True)
        credit = invoice._reverse_moves([{"invoice_date": "2026-06-19"}])
        credit.cssk_control_original_ref = "SOMETHING-ELSE"
        credit.action_post()
        st = self._make_statement()
        st.action_compute_lines()
        self.assertEqual(self._c1_fo(st), [invoice.name.replace(" ", "")])



@tagged("post_install", "-at_install")
class TestSkKvDphRateResolution(AccountTestInvoicingCommon):
    """Which tax a tags-only line computes with, when the tag names several.

    A tag does not identify a tax. Two things can still settle it without
    guessing — the date the supply was taxed, and the rate the source document
    declares — and where neither does, the line reports its base and no tax.
    """

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.tag = cls.env["account.account.tag"].create({
            "name": "RATE-RESOLUTION", "applicability": "taxes",
            "country_id": cls.env.ref("base.sk").id,
        })

    def _tax(self, amount, **vals):
        # Archived AFTER the repartition is tagged, for the same reason the
        # clone generator does it in that order: creating a tax inactive makes
        # some of Odoo's own defaults skip, and the repartition has to exist
        # before it is hidden.
        active = vals.pop("active", True)
        tax = self.env["account.tax"].create(dict({
            "name": "Rate %g%%" % amount, "amount": amount,
            "amount_type": "percent", "type_tax_use": "sale",
            "company_id": self.company.id,
        }, **vals))
        tax.invoice_repartition_line_ids.filtered(
            lambda r: r.repartition_type == "base"
        ).write({"tag_ids": [(6, 0, self.tag.ids)]})
        if not active:
            tax.active = False
        return tax

    def _line(self, date, base=1995.0, **move_vals):
        """A posted entry with one tags-only base line, as an importer writes."""
        move = self.env["account.move"].create(dict({
            "move_type": "entry", "date": date,
            "journal_id": self.company_data["default_journal_misc"].id,
            "line_ids": [
                (0, 0, {
                    "account_id": self.company_data["default_account_revenue"].id,
                    "debit": 0.0, "credit": base,
                    "tax_tag_ids": [(6, 0, self.tag.ids)]}),
                (0, 0, {
                    "account_id": self.company_data["default_account_receivable"].id,
                    "debit": base, "credit": 0.0}),
            ],
        }, **move_vals))
        move.action_post()
        return move.line_ids.filtered("tax_tag_ids")[:1]

    def _requires_historic_rates(self):
        if "cssk_historic_valid_from" not in self.env["account.tax"]._fields:
            self.skipTest("l10n_cssk_vat_return_base is not installed")

    # ------------------------------------------------------------------
    # the date
    # ------------------------------------------------------------------
    def test_a_rate_not_yet_in_force_is_not_a_candidate(self):
        """Adding 23 % in 2025 must not stop 2016 computing.

        This is the regression the filter exists for: before the current rate
        existed the tag resolved to one rate and computed; adding it gave every
        standard-rate tag a second candidate, and the disagreement then refused
        EVERY earlier period retroactively.
        """
        self._requires_historic_rates()
        current = self._tax(23.0)
        self._tax(20.0, cssk_historic_valid_from="2011-01-01",
                  cssk_historic_valid_to="2024-12-31",
                  cssk_historic_source_tax_id=current.id, active=False)

        line = self._line("2016-08-31")
        self.assertGreater(
            len(line._cssk_taxes()), 1, "premise: the tag is ambiguous")
        resolved = line._cssk_taxes_for_amounts()
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved.amount, 20.0)
        base, tax = line._cssk_base_and_tax_amounts()
        self.assertAlmostEqual(abs(base), 1995.0, places=2)
        self.assertAlmostEqual(abs(tax), 399.0, places=2)

    def test_a_current_rate_is_bounded_by_the_clone_that_preceded_it(self):
        """The subtle half: 23 % states no window of its own.

        Its start is derivable all the same — the 20 % clone pointing at it ran
        until 2024-12-31, so 23 % began the day after. Without that the current
        rate is a candidate for every date in history.
        """
        self._requires_historic_rates()
        current = self._tax(23.0)
        self._tax(20.0, cssk_historic_valid_from="2011-01-01",
                  cssk_historic_valid_to="2024-12-31",
                  cssk_historic_source_tax_id=current.id, active=False)

        self.assertEqual(
            current._cssk_rate_window()[0].isoformat(), "2025-01-01",
            "a current rate starts where its predecessor stopped")
        self.assertEqual(
            self._line("2025-03-31")._cssk_taxes_for_amounts().amount, 23.0)

    def test_the_tax_point_decides_the_rate_not_the_accounting_date(self):
        """A December supply booked in January is taxed in December.

        The period basis and the rate basis are different questions, and this
        is the boundary where the difference is visible.
        """
        self._requires_historic_rates()
        current = self._tax(23.0)
        self._tax(20.0, cssk_historic_valid_from="2011-01-01",
                  cssk_historic_valid_to="2024-12-31",
                  cssk_historic_source_tax_id=current.id, active=False)

        line = self._line("2025-01-10", taxable_supply_date="2024-12-20")
        self.assertEqual(line.move_id._cssk_rate_date().isoformat(), "2024-12-20")
        self.assertEqual(line._cssk_taxes_for_amounts().amount, 20.0)

    def test_the_filter_never_creates_a_refusal(self):
        """It may remove ambiguity; it may not manufacture one.

        SK ships no 19 % standard clone for 2004-2010 by an explicit decision,
        so a document that old matches no window at all. Emptying the candidate
        set there would make a line that used to compute stop computing.
        """
        self._requires_historic_rates()
        current = self._tax(23.0)
        self._tax(20.0, cssk_historic_valid_from="2011-01-01",
                  cssk_historic_valid_to="2024-12-31",
                  cssk_historic_source_tax_id=current.id, active=False)

        line = self._line("2008-05-31")
        self.assertFalse(
            current._cssk_in_force_on(line.move_id._cssk_rate_date()),
            "premise: nothing in the chart was in force that far back")
        self.assertFalse(
            line._cssk_taxes_for_amounts(),
            "the unfiltered set still disagrees, so it still refuses — but on "
            "the old grounds, not because the filter emptied it")

    # ------------------------------------------------------------------
    # the declaration
    # ------------------------------------------------------------------
    def test_a_declared_rate_settles_what_no_date_can(self):
        """Rates in force AT ONCE cannot be separated by any date.

        SK ran 5 %, 10 % and 20 % concurrently before 2025, and the pre-2025
        reverse-charge band was a single line for all of them. Only the
        producer of the document knows which applied.
        """
        for amount in (5.0, 20.0, 23.0):
            self._tax(amount)
        line = self._line("2024-08-31")
        self.assertFalse(
            line._cssk_taxes_for_amounts(), "premise: undecidable on its own")

        line.cssk_control_rate_declared = 20.0
        resolved = line._cssk_taxes_for_amounts()
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved.amount, 20.0)
        base, tax = line._cssk_base_and_tax_amounts()
        self.assertAlmostEqual(abs(base), 1995.0, places=2)
        self.assertAlmostEqual(abs(tax), 399.0, places=2)
        self.assertAlmostEqual(line._cssk_tax_rate(), 20.0, places=2)

    def test_a_declared_rate_on_a_correction_keeps_its_sign(self):
        """Modelled on a real document, because C.1 is corrections.

        ``ICO1250005`` from the RF Elements i6 agenda: 2025-11-10, tag 24,
        base -31 353.00, source rate 23 %, expected tax -7 211.19. Tag 24
        reaches vy_tuz_5/19/23 and their 10 % and 20 % clones, so a 2025 date
        narrows five candidates to three and still cannot choose — only the
        declaration can. A negative base is the ordinary case in that section
        and nothing in the resolution may treat it as a special one.
        """
        self._requires_historic_rates()
        current = {}
        for amount in (5.0, 19.0, 23.0):
            current[amount] = self._tax(amount)
        self._tax(10.0, cssk_historic_valid_from="2007-01-01",
                  cssk_historic_valid_to="2024-12-31",
                  cssk_historic_source_tax_id=current[19.0].id, active=False)
        self._tax(20.0, cssk_historic_valid_from="2011-01-01",
                  cssk_historic_valid_to="2024-12-31",
                  cssk_historic_source_tax_id=current[23.0].id, active=False)

        line = self._line("2025-11-10", base=-31353.00)
        self.assertEqual(
            len(line._cssk_taxes()), 5, "premise: five rates share the tag")
        self.assertFalse(
            line._cssk_taxes_for_amounts(),
            "premise: 5, 19 and 23 were all in force in 2025")

        line.cssk_control_rate_declared = 23.0
        self.assertEqual(line._cssk_taxes_for_amounts().amount, 23.0)
        base, tax = line._cssk_base_and_tax_amounts()
        self.assertAlmostEqual(abs(base), 31353.00, places=2)
        self.assertAlmostEqual(abs(tax), 7211.19, places=2)
        self.assertEqual(
            (base < 0), (tax < 0),
            "base and tax must fall on the same side of zero")

    def test_a_declared_rate_matching_nothing_is_refused_not_computed(self):
        """The field selects among candidates; it is not a licence to compute.

        A rate the tag cannot reach means the producer mapped the line wrong.
        Applying it anyway would put a plausible number with nothing behind it
        on a filed form, which is the failure this whole area exists to avoid.
        """
        for amount in (5.0, 20.0, 23.0):
            self._tax(amount)
        line = self._line("2024-08-31")
        line.cssk_control_rate_declared = 12.0
        self.assertFalse(line._cssk_taxes_for_amounts())
        base, tax = line._cssk_base_and_tax_amounts()
        self.assertAlmostEqual(abs(base), 1995.0, places=2)
        self.assertAlmostEqual(tax, 0.0, places=2)

    def test_a_declared_rate_that_the_calendar_contradicts_is_refused(self):
        """Declared beats derived; it does not beat the calendar.

        A rate the tag can reach but that was not in force when the document
        was taxed is not a tie broken — it is two pieces of evidence
        disagreeing, and which one is wrong is what we do not know.
        """
        self._requires_historic_rates()
        current = self._tax(23.0)
        self._tax(20.0, cssk_historic_valid_from="2011-01-01",
                  cssk_historic_valid_to="2024-12-31",
                  cssk_historic_source_tax_id=current.id, active=False)

        line = self._line("2016-08-31")
        line.cssk_control_rate_declared = 23.0
        self.assertFalse(
            line._cssk_taxes_for_amounts(),
            "23 % did not exist in 2016; the declaration cannot make it")
        self.assertAlmostEqual(
            line._cssk_base_and_tax_amounts()[1], 0.0, places=2)

    def test_a_declaration_survives_where_no_window_is_known(self):
        """Intersecting with the in-force set must cost nothing when the
        chart says nothing about when its rates began."""
        for amount in (5.0, 20.0, 23.0):
            self._tax(amount)
        line = self._line("2016-08-31")
        line.cssk_control_rate_declared = 20.0
        self.assertEqual(line._cssk_taxes_for_amounts().amount, 20.0)

    def test_several_clones_of_one_rate_start_it_at_the_latest(self):
        """A merger of bands: the current rate begins when the LAST of the
        rates it replaced stopped. CZ 12 % is cloned from by 15 %, 14 %, 10 %,
        9 % and 5 %, and starts the day after the latest of them ends.
        """
        self._requires_historic_rates()
        current = self._tax(12.0)
        for rate, frm, to in (
            (15.0, "2013-01-01", "2023-12-31"),
            (14.0, "2012-01-01", "2012-12-31"),
            (10.0, "2010-01-01", "2023-12-31"),
            (9.0, "2008-01-01", "2009-12-31"),
        ):
            self._tax(rate, cssk_historic_valid_from=frm,
                      cssk_historic_valid_to=to,
                      cssk_historic_source_tax_id=current.id, active=False)
        self.assertEqual(
            current._cssk_rate_window()[0].isoformat(), "2024-01-01")
        # 2020: 15 % and 10 % were both in force and 12 % was not. Two rates
        # that really did coexist cannot be separated by any date.
        self.assertFalse(self._line("2020-06-30")._cssk_taxes_for_amounts())

    def test_a_real_tax_beats_a_declared_rate(self):
        """Where the line carries a tax, nothing is inferred and nothing is
        declared — the document already said it."""
        invoice = self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-13",
            amounts=[1000.0], taxes=self.tax_sale_a, post=True,
        )
        line = invoice.line_ids.filtered(
            lambda l: l.tax_ids and not l.tax_line_id)[:1]
        line.cssk_control_rate_declared = 5.0
        self.assertEqual(line._cssk_taxes_for_amounts(), line.tax_ids)


class TestEveryVzorFilesTheDeductionField(TransactionCase):
    """No vzor may file the odpočítaná daň from the tax charged.

    The four vzory are near-copies of one another, so a fifth is written by
    copying the fourth — which is how ``O`` came to be rendered from
    ``tax_amount`` in all four while the row's own ``deducted_amount`` sat at
    0.00 and nothing said so. Reading the template rather than exercising it
    is the point: an export test only sees the vintage its fixture resolves
    to, and the copy-paste happens in the ones it does not.
    """

    def test_no_O_attribute_is_rendered_from_the_tax_charged(self):
        import os
        import re

        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(here, "report", "l10n_sk_kv_dph_templates.xml")
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        found = re.findall(r't-att-(OR?)="([^"]*)"', source)
        self.assertTrue(found, "the template renders no O/OR at all")
        wrong = [expr for _attr, expr in found if "deducted" not in expr]
        self.assertFalse(
            wrong,
            "odpočítaná daň must be filed from the row's deduction, not from "
            "the tax charged — the two differ under the § 50 koeficient: %s"
            % sorted(set(wrong)))


class TestSchemaPins(TransactionCase):
    """The bundled schemas must match data/SCHEMA_VERSION.

    Not a check that our copy is CURRENT — nothing local can answer that, which
    is the whole reason the pin file exists. This checks the weaker thing that
    is still worth having: that the bundled bytes are the ones somebody
    verified against the published copy on a stated date. Replacing a schema
    then has to be a deliberate two-file change rather than a silent one, and
    the refresh procedure lives next to the digest that would have to move.
    """

    def test_bundled_schemas_match_the_pinned_digests(self):
        import hashlib
        import os
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data = os.path.join(here, "data")
        pins = {}
        with open(os.path.join(data, "SCHEMA_VERSION"), encoding="utf-8") as fh:
            for raw in fh:
                parts = raw.split()
                if len(parts) == 3 and parts[0].endswith(".xsd"):
                    pins[parts[0]] = (parts[1], int(parts[2]))
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
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data = os.path.join(here, "data")
        on_disk = {f for f in os.listdir(data) if f.endswith(".xsd")}
        pinned = set()
        with open(os.path.join(data, "SCHEMA_VERSION"), encoding="utf-8") as fh:
            for raw in fh:
                parts = raw.split()
                if len(parts) == 3 and parts[0].endswith(".xsd"):
                    pinned.add(parts[0])
        self.assertEqual(on_disk, pinned,
                         "unpinned schema(s): %s" % sorted(on_disk - pinned))


@tagged("post_install", "-at_install")
class TestKvReportsTheInvoicedTax(AccountTestInvoicingCommon):
    """§ 78a reports the tax a document CHARGED, not one derived from its base.

    The two are not the same quantity and the difference is not a rounding
    direction. Measured against a real agenda: ten pokladničné doklady summed
    to a filed 152.98 where the tax derived from their summed base is 152.96,
    and one of them charged 1.27 on a base of 6.32 — base × 20 % is 1.264, so
    no rounding of a derived figure reaches the filed one. Only reading the
    document does.

    This reproduces the mechanism with the company on ``round_globally``,
    which is what that agenda uses: Odoo rounds the document's tax once, while
    deriving it per base line rounds once per line.
    """

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write({
            "vat": "SK2023456787", "city": "Bratislava",
            "country_id": cls.env.ref("base.sk").id,
            "tax_calculation_rounding_method": "round_globally",
        })
        cls.partner_a.write({"country_id": cls.env.ref("base.sk").id,
                             "vat": "SK2023456787"})

    def _two_line_invoice(self, first, second, tax):
        move = self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[first, second], taxes=tax, post=True)
        return move

    def test_the_row_reports_what_the_document_posted(self):
        """Two lines whose per-line rounding does not add up to the document's.

        6.32 and 21.62 at 20 %: per line that is 1.264 → 1.26 and 4.324 →
        4.32, summing to 5.58, where the document itself charges 20 % of 27.94
        = 5.588 → 5.59. The row must report 5.59, because that is what the
        invoice says and what the customer paid.
        """
        tax = self.tax_sale_a
        if tax.amount != 20.0:
            tax = tax.copy({"name": "SK 20% (test)", "amount": 20.0})
        move = self._two_line_invoice(6.32, 21.62, tax)

        posted = sum(move.line_ids.filtered("tax_line_id").mapped("balance"))
        base_lines = move.line_ids.filtered(
            lambda l: not l.tax_line_id and l.tax_ids)
        reported = sum(
            abs(l._cssk_base_and_tax_amounts()[1]) for l in base_lines)

        self.assertAlmostEqual(
            abs(posted), 5.59, places=2,
            msg="fixture: the document must round globally to 5.59")
        self.assertAlmostEqual(
            reported, abs(posted), places=2,
            msg="the KV must report the tax the document posted, not a "
                "re-derivation of it")

    def test_the_shares_add_back_to_the_document(self):
        """Apportionment must not lose or invent a cent.

        The posted tax is split across the base lines that share it, by base
        share, so a row aggregating them reports exactly what was charged.
        Any apportionment that rounded per line would reintroduce the very
        error this replaces.
        """
        tax = self.tax_sale_a
        if tax.amount != 20.0:
            tax = tax.copy({"name": "SK 20% (test)", "amount": 20.0})
        move = self._two_line_invoice(6.32, 21.62, tax)
        base_lines = move.line_ids.filtered(
            lambda l: not l.tax_line_id and l.tax_ids)
        self.assertEqual(len(base_lines), 2, "fixture: two base lines")
        shares = [abs(l._cssk_base_and_tax_amounts()[1]) for l in base_lines]
        posted = abs(sum(move.line_ids.filtered("tax_line_id").mapped("balance")))
        self.assertAlmostEqual(sum(shares), posted, places=6,
                               msg="the shares must reconstitute the total")

    def test_a_tags_only_line_keeps_its_derived_tax(self):
        """No tax line to read means the derivation stands.

        An imported ledger records VAT it booked itself as tax TAGS on a
        journal entry, with no tax line at all. Reading is impossible there and
        must fall back rather than report zero — zeroing it would silently
        empty every row of an imported agenda, which is the population this
        work exists to serve.
        """
        tax = self.tax_sale_a
        tag = tax.invoice_repartition_line_ids.filtered(
            lambda r: r.repartition_type == "base").tag_ids[:1]
        if not tag:
            self.skipTest("the sale tax carries no base tag to key on")
        move = self.env["account.move"].create({
            "move_type": "entry", "date": "2026-06-14",
            "journal_id": self.company_data["default_journal_misc"].id,
            "line_ids": [
                # TAGS ONLY, no tax_ids: setting tax_ids makes Odoo post a
                # tax line of its own, which is exactly the shape this test is
                # not about. An imported ledger carries the tag and nothing
                # else, because the source already booked the VAT.
                (0, 0, {"account_id": self.company_data["default_account_revenue"].id,
                        "debit": 0.0, "credit": 1000.0,
                        "tax_tag_ids": [(6, 0, tag.ids)]}),
                (0, 0, {"account_id": self.company_data["default_account_receivable"].id,
                        "debit": 1000.0, "credit": 0.0}),
            ],
        })
        move.action_post()
        line = move.line_ids.filtered("tax_tag_ids")[:1]
        self.assertIsNone(
            line._cssk_posted_tax_amount(line._cssk_taxes_for_amounts()),
            "with no tax line there is nothing to read")
        _base, computed = line._cssk_base_and_tax_amounts()
        self.assertAlmostEqual(
            abs(computed), 1000.0 * tax.amount / 100.0, places=2,
            msg="and the derived figure must survive")

    def test_a_fixed_amount_tax_beside_a_percent_one_survives(self):
        """Reading must SWAP what it read, not replace the whole figure.

        A fixed-amount tax is never read — there is no per-cent relation to
        read it against — so replacing the derived total outright dropped it
        silently. Under-reporting is the direction that goes unnoticed.
        """
        percent = self.tax_sale_a
        if percent.amount != 20.0:
            percent = percent.copy({"name": "SK 20% (test)", "amount": 20.0})
        fixed = self.env["account.tax"].create({
            "name": "Recyklačný poplatok (fixed)", "amount_type": "fixed",
            "amount": 3.0, "type_tax_use": "sale",
            "company_id": self.company.id,
            "country_id": self.company.account_fiscal_country_id.id,
            "tax_group_id": percent.tax_group_id.id,
        })
        move = self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[100.0], taxes=percent | fixed, post=True)
        line = move.line_ids.filtered(
            lambda l: not l.tax_line_id and l.tax_ids)[:1]
        _base, tax = line._cssk_base_and_tax_amounts()
        self.assertAlmostEqual(
            abs(tax), 23.0, places=2,
            msg="20 %% of 100 read from the document, PLUS the fixed 3.00 "
                "that cannot be read and must not vanish")

    def test_a_group_tax_does_not_defeat_the_reverse_charge_recovery(self):
        """`taxes - rc_flat` is a no-op when `taxes` holds a GROUP.

        A group is not equal to its children, so subtracting a flattened
        reverse-charge set from an unflattened one removes nothing, and the
        self-assessed legs would be read AND recovered — counted twice, or
        netted to nothing. Flattening before subtracting is what stops it.
        """
        rc = self.env["account.tax"].search([
            ("company_id", "=", self.company.id),
            ("cssk_control_is_reverse_charge", "=", True),
        ], limit=1)
        if not rc:
            self.skipTest("no reverse-charge tax flagged in this chart")
        flat = rc.flatten_taxes_hierarchy()
        self.assertTrue(
            (rc.flatten_taxes_hierarchy() - flat) == self.env["account.tax"],
            "flattening then subtracting must empty the set")

    def test_a_mixed_sign_document_keeps_the_derived_tax(self):
        """Apportioning by base share needs the shares to mean something.

        A document mixing signs for one tax — goods and a return line, or an
        invoice carrying a discount — can net to a figure that is a rounding
        artefact of two large opposite numbers, and a line's share of it then
        swings wildly. The shares would still sum to the document's total, so
        a row over the whole document stays right; one whose lines land in
        different sections would not. Refuse, and keep the stable figure.
        """
        tax = self.tax_sale_a
        if tax.amount != 20.0:
            tax = tax.copy({"name": "SK 20% (test)", "amount": 20.0})
        # 100.00 and -99.97: the net is 0.03, whose tax rounds to 0.01 where
        # 20 %% of 0.03 is 0.006. Apportioning by base share multiplies that
        # 0.004 by 100/0.03 — a share of 33.33 where the line's own tax is
        # 20.00. The numbers are chosen so the instability is visible rather
        # than theoretical; a net that rounds to no tax at all is caught
        # earlier and would not exercise this guard.
        move = self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[100.0, -99.97], taxes=tax, post=True)
        base_lines = move.line_ids.filtered(
            lambda l: not l.tax_line_id and l.tax_ids)
        self.assertEqual(len(base_lines), 2, "fixture: two opposing lines")
        posted = sum(move.line_ids.filtered("tax_line_id").mapped("balance"))
        self.assertFalse(
            self.company.currency_id.is_zero(posted),
            "fixture: the document must post a non-zero tax, or the guard is "
            "never reached")
        for line in base_lines:
            self.assertIsNone(
                line._cssk_posted_tax_amount(
                    line._cssk_taxes_for_amounts().flatten_taxes_hierarchy()),
                "a mixed-sign document must not be apportioned")
        # ...and each line still reports its own derived tax
        first = base_lines.filtered(lambda l: l.balance < 0)[:1]
        self.assertAlmostEqual(
            abs(first._cssk_base_and_tax_amounts()[1]),
            abs(first.balance) * 20.0 / 100.0, places=2)

    def test_a_sibling_carrying_the_GROUP_is_still_a_sibling(self):
        """The denominator must not shrink because a line holds the parent.

        `tax_ids` on a base line may carry a group while the tax LINES carry
        its children. Testing membership without flattening the sibling's own
        taxes drops that line from the denominator, and this line then takes
        more than its share of the document's tax — over-reporting on a filed
        statement.
        """
        child = self.tax_sale_a
        if child.amount != 20.0:
            child = child.copy({"name": "SK 20% child", "amount": 20.0})
        group = self.env["account.tax"].create({
            "name": "SK 20% (group)", "amount_type": "group",
            "type_tax_use": "sale", "company_id": self.company.id,
            "country_id": self.company.account_fiscal_country_id.id,
            "children_tax_ids": [(6, 0, child.ids)],
        })
        move = self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[100.0], taxes=group, post=True)
        line = move.line_ids.filtered(
            lambda l: not l.tax_line_id and l.tax_ids)[:1]
        flat = line.tax_ids.flatten_taxes_hierarchy().filtered(
            lambda t: t.amount_type == "percent" and t.amount)
        share = line._cssk_posted_tax_amount(flat)
        self.assertIsNotNone(share, "the group's child must be readable")
        posted = sum(move.line_ids.filtered("tax_line_id").mapped("balance"))
        self.assertAlmostEqual(
            abs(share), abs(posted), places=2,
            msg="one base line takes the whole of the document's tax, not a "
                "share inflated by a missing sibling")


@tagged("post_install", "-at_install")
class TestKvCashBasis(AccountTestInvoicingCommon):
    """A tax "Based on Payment" is reported when it is paid, once.

    Reported by an external accountant on a customs setup: the VAT of a
    customs document (and of an issued advance invoice) is due only on
    payment, so the taxes carry ``tax_exigibility = on_payment`` and a
    transition account (343620 DPH – neuplatnená). The statement reported the
    unpaid document straight away, and after payment reported Odoo's
    cash-basis entry AGAIN — in B.3.1, because that entry has no partner and
    a received document with no counterparty is a simplified invoice.
    """

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write({
            "vat": "SK2023456787", "city": "Bratislava",
            "country_id": cls.env.ref("base.sk").id,
            "tax_exigibility": True,
        })
        if not cls.company.tax_cash_basis_journal_id:
            cls.company.tax_cash_basis_journal_id = cls.env[
                "account.journal"].create({
                    "name": "Cash basis", "code": "CABA", "type": "general",
                    "company_id": cls.company.id})
        cls.partner_a.write({
            "country_id": cls.env.ref("base.sk").id, "vat": "SK2023456787"})
        cls.transition = cls.env["account.account"].create({
            "code": "343620", "name": "DPH - neuplatnená tuzemsko",
            "account_type": "liability_current", "reconcile": True,
        })
        cls.caba_sale = cls.tax_sale_a.copy({
            "name": "CABA sale", "tax_exigibility": "on_payment",
            "cash_basis_transition_account_id": cls.transition.id})
        cls.caba_purchase = cls.tax_purchase_a.copy({
            "name": "CABA purchase", "tax_exigibility": "on_payment",
            "cash_basis_transition_account_id": cls.transition.id})
        cls.version = cls.env.ref("l10n_sk_kv_dph.kvdph_version_2025v1")

    def _statement(self, date_from, date_to):
        st = self.env["cssk.control.statement"].create({
            "company_id": self.company.id,
            "version_id": self.version.id,
            "date_from": date_from, "date_to": date_to,
            "period_type": "month",
            "statement_type_id": self.env["cssk.control.statement.type"].search([
                ("country_id", "=", self.env.ref("base.sk").id),
                ("fa_xml_value", "=", "R")]).id,
        })
        st.action_compute_lines()
        return st

    def _pay(self, move, date, fraction=1.0):
        """Settle ``fraction`` of ``move`` by a bank entry dated ``date``."""
        term = move.line_ids.filtered(
            lambda l: l.account_type in ("asset_receivable", "liability_payable"))
        amount = move.currency_id.round(-term.balance * fraction)
        bank = self.company_data["default_journal_bank"]
        payment = self.env["account.move"].create({
            "move_type": "entry", "date": date, "journal_id": bank.id,
            "line_ids": [
                Command.create({
                    "account_id": term.account_id.id,
                    "partner_id": move.partner_id.id,
                    "balance": amount}),
                Command.create({
                    "account_id": bank.default_account_id.id,
                    "balance": -amount}),
            ],
        })
        payment.action_post()
        (payment.line_ids.filtered(
            lambda l: l.account_id == term.account_id) | term).reconcile()
        return self.env["account.move"].search(
            [("tax_cash_basis_origin_move_id", "=", move.id)],
            order="id desc", limit=1)

    @staticmethod
    def _sections(move):
        return set(move.line_ids.mapped("cssk_control_section_code")) - {False}

    def test_an_unpaid_cash_basis_bill_is_not_reported(self):
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.caba_purchase, post=True)
        self.assertFalse(self._sections(bill))
        st = self._statement("2026-06-01", "2026-06-30")
        self.assertFalse(st.sk_section_b2_ids)
        self.assertFalse(st.sk_section_b31_ids)

    def test_a_paid_cash_basis_bill_is_B2_under_its_supplier_not_B31(self):
        """The case as reported: B.3.1 was where the paid VAT turned up."""
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2026-05-20",
            amounts=[1000.0], taxes=self.caba_purchase, post=False)
        bill.ref = "JCD-2026-0042"
        bill.action_post()
        caba = self._pay(bill, "2026-06-15")
        self.assertTrue(caba, "Odoo posted no cash-basis entry")
        self.assertEqual(self._sections(caba), {"B.2"})
        self.assertFalse(self._sections(bill), "the bill itself stays out")

        may = self._statement("2026-05-01", "2026-05-31")
        self.assertFalse(may.sk_section_b2_ids,
                         "unpaid in May, so nothing is due in May")
        june = self._statement("2026-06-01", "2026-06-30")
        self.assertFalse(june.sk_section_b31_ids)
        self.assertFalse(june.sk_section_b32_ids)
        row = june.sk_section_b2_ids
        self.assertEqual(len(row), 1)
        self.assertEqual(row.entry_ref, "JCD-2026-0042")
        self.assertEqual(row.partner_vat_stripped, "2023456787")
        self.assertAlmostEqual(row.tax_base_amount, 1000.0, 2)
        self.assertAlmostEqual(
            row.tax_amount, 1000.0 * self.caba_purchase.amount / 100.0, 2)

    def test_a_paid_advance_is_A1_dated_by_the_payment(self):
        """Half paid, half reported — with the invoice's number and customer,
        the payment's date, and the sign of an issued document."""
        inv = self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-02",
            amounts=[1000.0], taxes=self.caba_sale, post=True)
        self.assertFalse(self._sections(inv))
        caba = self._pay(inv, "2026-06-18", fraction=0.5)
        self.assertEqual(self._sections(caba), {"A.1"})

        row = self._statement("2026-06-01", "2026-06-30").sk_section_a1_ids
        self.assertEqual(len(row), 1)
        self.assertEqual(row.entry_ref, inv.name)
        self.assertEqual(row.partner_id, self.partner_a)
        self.assertEqual(str(row.supply_date), "2026-06-18")
        self.assertAlmostEqual(row.tax_base_amount, 500.0, 2)
        self.assertAlmostEqual(
            row.tax_amount, 500.0 * self.caba_sale.amount / 100.0, 2)

    def test_an_ordinary_tax_is_untouched(self):
        """The exigibility test must not reach a tax due on the invoice."""
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[100.0], taxes=self.tax_purchase_a, post=True)
        self.assertEqual(self._sections(bill), {"B.2"})

    def test_the_upgrade_clears_a_section_the_old_resolver_left(self):
        """A database classified by the previous resolver holds a section on
        every unpaid cash-basis line, and nothing refreshes a stored value when
        only the code changed. The migration's recompute must."""
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.caba_purchase, post=True)
        base = bill.line_ids.filtered("tax_ids")
        self.env.cr.execute(
            "UPDATE account_move_line SET cssk_control_section_code = 'B.2'"
            " WHERE id IN %s", [tuple(base.ids)])
        base.invalidate_recordset(["cssk_control_section_code"])
        self.assertEqual(self._sections(bill), {"B.2"})
        changed = self.env["account.move.line"]\
            ._cssk_recompute_cash_basis_section_codes("SK")
        self.assertGreaterEqual(changed, len(base))
        self.assertFalse(self._sections(bill))

    def test_an_unreconciled_payment_files_nothing(self):
        """Odoo reverses the cash-basis entry when a payment is removed; the
        entry and its reversal must cancel, not file +x and -x."""
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.caba_purchase, post=True)
        caba = self._pay(bill, "2026-06-15")
        bill.line_ids.filtered(
            lambda l: l.account_type == "liability_payable").remove_move_reconcile()
        reversal = self.env["account.move"].search(
            [("reversed_entry_id", "=", caba.id)])
        self.assertTrue(reversal, "Odoo did not reverse the cash-basis entry")
        self.assertEqual(self._sections(reversal), {"B.2"})
        st = self._statement("2026-06-01", "2026-06-30")
        self.assertFalse(st.sk_section_b2_ids)
        self.assertFalse(st.sk_section_b31_ids)

    def test_a_group_that_is_partly_due_reports_the_due_part(self):
        """Odoo decides exigibility per CHILD of a group and tags each child on
        its own, so the statement must too: dropping the whole group because
        one child waits for payment loses the part that is already due.
        Raised by the second-opinion review of the cash-basis fix."""
        now, later = (self.tax_purchase_a.copy({
            "name": name, "amount": 10.0, "type_tax_use": "none",
            "tax_exigibility": exig,
            "cash_basis_transition_account_id": self.transition.id,
        }) for name, exig in (("10 now", "on_invoice"), ("10 later", "on_payment")))
        group = self.env["account.tax"].create({
            "name": "Half now, half later", "amount_type": "group",
            "type_tax_use": "purchase",
            "children_tax_ids": [Command.set((now | later).ids)],
        })
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=group, post=True)
        base = bill.line_ids.filtered("tax_ids")
        self.assertEqual(base._cssk_taxes(), now)
        self.assertEqual(self._sections(bill), {"B.2"})
        row = self._statement("2026-06-01", "2026-06-30").sk_section_b2_ids
        self.assertEqual(len(row), 1)
        self.assertAlmostEqual(row.tax_amount, 100.0, 2, "only the due half")

