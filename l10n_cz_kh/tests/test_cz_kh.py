# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from lxml import etree

from odoo import Command, fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools import date_utils


@tagged("post_install", "-at_install")
class TestCzKh(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.vat = "CZ25663585"
        # EPO requires the competent tax office (c_ufo); assign the seeded one.
        # FÚ pro hl. m. Prahu — seeded by l10n_cz_statutory's hook without an
        # xmlid (the old l10n_cssk_core.cz_ufo_* ids were removed in 1.2.0);
        # look it up by its stable submission code instead.
        cls.company.l10n_cssk_tax_authority_id = cls.env["cssk.tax.authority"].search(
            [("country_code", "=", "CZ"), ("submission_code", "=", "451")], limit=1)
        cls.partner = cls.env["res.partner"].create({
            "name": "Odber CZ", "country_id": cls.env.ref("base.cz").id,
            "vat": "CZ46342958",
        })
        vat1 = cls.env["account.account.tag"]._get_tax_tags(
            "VAT 1 Base", cls.env.ref("base.cz").id)
        cls.tax21 = cls.env["account.tax"].search([
            ("type_tax_use", "=", "sale"), ("amount", "=", 21.0),
            ("company_id", "=", cls.company.id),
            ("invoice_repartition_line_ids.tag_ids", "in", vat1.ids),
        ], limit=1)
        cls.version = cls.env.ref("l10n_cz_kh.cz_kh_version_2025")

    def _sale(self, amount):
        inv = self.env["account.move"].create({
            "move_type": "out_invoice", "partner_id": self.partner.id,
            "invoice_date": fields.Date.context_today(self.env.user),
            "invoice_line_ids": [Command.create({
                "name": "x", "quantity": 1, "price_unit": amount,
                "tax_ids": [Command.set(self.tax21.ids)]})],
        })
        inv.action_post()
        return inv

    def _statement(self):
        today = fields.Date.context_today(self.env.user)
        st = self.env["cssk.control.statement"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": today.replace(day=1), "date_to": date_utils.end_of(today, "month"),
            "period_type": "month",
            "statement_type_id": self.env.ref("l10n_cz_kh.cz_kh_type_B").id,
        })
        st.action_compute_lines()
        return st

    def test_threshold_split_and_export(self):
        self._sale(15000.0)   # > 10000 -> A4 detail
        self._sale(5000.0)    # <= 10000 -> A5 aggregate
        st = self._statement()
        self.assertEqual(len(st.cz_a4_ids), 1)
        self.assertAlmostEqual(st.cz_a4_ids.base_std, 15000.0, places=2)
        self.assertEqual(len(st.cz_a5_ids), 1)
        self.assertAlmostEqual(st.cz_a5_ids.base_std, 5000.0, places=2)

        st.action_export_xml()
        self.assertEqual(st.state, "exported")
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).localname, "Pisemnost")
        self.assertEqual(len(root.findall(".//VetaA4")), 1)
        self.assertEqual(len(root.findall(".//VetaA5")), 1)
        self.assertEqual(root.find(".//VetaA4").get("dic_odb"), "46342958")

    def test_preflight_missing_partner_vat_names_document(self):
        """Master-data preflight: an A4 row without the counterparty DIČ
        (XSD-required dic_odb) blocks the export early, naming the offending
        document instead of a cryptic XSD error."""
        inv = self._sale(15000.0)  # > 10 000 CZK -> A4 detail row
        st = self._statement()
        # master-data gap (partner_vat_stripped is what dic_odb renders)
        st.cz_a4_ids.write({"partner_vat": False, "partner_vat_stripped": False})
        with self.assertRaises(UserError) as cm:
            st.action_export_xml()
        msg = str(cm.exception)
        self.assertIn("A4", msg)
        self.assertIn(inv.name, msg, "the offending document must be named")
        self.assertEqual(st.state, "preview", "fail-early: nothing exported")

    def test_preflight_missing_supply_date_names_document(self):
        """Master-data preflight: a missing DUZP/DPPD (XSD-required date)
        blocks the export early with the document number."""
        inv = self._sale(15000.0)
        st = self._statement()
        st.cz_a4_ids.supply_date = False
        with self.assertRaises(UserError) as cm:
            st.action_export_xml()
        msg = str(cm.exception)
        self.assertIn("DUZP", msg)
        self.assertIn(inv.name, msg, "the offending document must be named")

    def test_a_tax_that_posted_nothing_reports_nothing(self):
        """An imported ledger can carry a document booked at a rate but with no
        VAT at all: the base line keeps the tax, and the tax line posts 0.00.

        Reporting compute_all's answer there states VAT the company never
        booked, and it does more than misstate a figure — base+tax decides the
        over/under-threshold split, so phantom tax moves a document between the
        detail section and the aggregate one. It also puts the control
        statement at odds with the VAT return, which reads tags and reports
        nothing for the same document.

        The companion guard — a tags-only line, which has NO tax line at all
        and must keep its computed tax — is asserted by the SK suite.
        """
        # An ORDINARY deductible purchase tax: a self-assessing one is excluded
        # deliberately, since its legs net to zero by design and its recovery
        # is a different mechanism entirely.
        purchase21 = self.env["account.tax"].search([
            ("type_tax_use", "=", "purchase"),
            ("company_id", "=", self.company.id), ("amount", "=", 21.0),
        ]).filtered(lambda t: not t._cssk_self_assesses())[:1]
        self.assertTrue(purchase21)
        bill = self.env["account.move"].create({
            "move_type": "in_invoice", "partner_id": self.partner.id,
            "invoice_date": fields.Date.context_today(self.env.user),
            "ref": "NO-VAT-BOOKED",
            "invoice_line_ids": [Command.create({
                "name": "x", "quantity": 1, "price_unit": 10000.0,
                "tax_ids": [Command.set(purchase21.ids)]})],
        })
        bill.action_post()
        # Force the shape an IMPORTED ledger has: the tax line exists and posts
        # nothing, because the source booked the document at a rate but with no
        # VAT. Written to the ledger directly — Odoo recomputes tax lines on
        # post, so it will not build this itself, which is precisely why the
        # reporting side has to cope with it.
        tax_lines = bill.line_ids.filtered("tax_line_id")
        payable = bill.line_ids.filtered(
            lambda x: x.account_id.account_type == "liability_payable")
        self.env.cr.execute(
            "UPDATE account_move_line SET debit = 0, credit = 0, balance = 0 "
            "WHERE id IN %s", (tuple(tax_lines.ids),))
        self.env.cr.execute(
            "UPDATE account_move_line SET credit = 10000, balance = -10000 "
            "WHERE id IN %s", (tuple(payable.ids),))
        self.env.invalidate_all()

        self.assertTrue(bill.line_ids.filtered("tax_line_id"),
                        "the tax line must EXIST and post nothing")
        self.assertAlmostEqual(
            sum(bill.line_ids.filtered("tax_line_id").mapped("balance")),
            0.0, places=2)
        line = bill.invoice_line_ids
        base, tax = line._cssk_base_and_tax_amounts()
        self.assertAlmostEqual(abs(base), 10000.0, places=2)
        self.assertAlmostEqual(abs(tax), 0.0, places=2,
                               msg="VAT that never posted must not be reported")

    def test_threshold_reads_the_document_not_the_taxable_part(self):
        """The 10 000 limit is a property of the DOKLAD — celková částka za
        plnění včetně daně — so an exempt line counts towards it even though it
        is reported nowhere.

        A mixed document is where the two readings diverge: taxable part under
        the limit, document over. Summing the bucket filed it as an aggregate
        when the accountant filed it as a detail row.
        """
        exempt = self.env["account.tax"].search([
            ("type_tax_use", "=", "sale"), ("amount", "=", 0.0),
            ("company_id", "=", self.company.id),
        ], limit=1)
        self.assertTrue(exempt)
        inv = self.env["account.move"].create({
            "move_type": "out_invoice", "partner_id": self.partner.id,
            "invoice_date": fields.Date.context_today(self.env.user),
            "invoice_line_ids": [
                Command.create({"name": "exempt", "quantity": 1,
                                "price_unit": 19000.0,
                                "tax_ids": [Command.set(exempt.ids)]}),
                Command.create({"name": "taxed", "quantity": 1,
                                "price_unit": 3492.0,
                                "tax_ids": [Command.set(self.tax21.ids)]}),
            ],
        })
        inv.action_post()
        st = self._statement()
        self.assertTrue(st.cz_a4_ids,
                        "document total 22 492 is over the limit -> detail row")
        self.assertFalse(st.cz_a5_ids.filtered(lambda r: r.base_std),
                         "and it must not also sit in the aggregate")
        # The REPORTED figure stays the taxable part; only the split moved.
        self.assertAlmostEqual(st.cz_a4_ids.base_std, 3492.0, places=2)

    def test_one_structure_serves_every_period(self):
        """CZ is NOT versioned per year, and the difference from the Slovak
        module is deliberate rather than an omission.

        Czech EPO publishes a single dphkh1_epo2.xsd and overwrites it in
        place; older structures are not published at all, and since
        1. 10. 2019 every KH must be filed in the then-current structure
        whatever period it covers. So there is exactly ONE open-ended version,
        and a follow-up KH for 2021 filed today goes in today's form.

        Asserted because the natural instinct — the one the SK module next
        door rewards — is to add a vintage per year, and here that would
        recreate the bug this replaced: a version dated from 2025 refused 66
        of 85 filed periods it was perfectly able to export.
        """
        versions = self.env["cssk.control.statement.version"].search(
            [("country_id.code", "=", "CZ")])
        self.assertEqual(len(versions), 1,
                         "CZ holds one structure, not a vintage per year")
        self.assertFalse(versions.valid_to, "the current structure stays open")

    def test_the_floor_is_the_form_s_own(self):
        """A document with DUZP before 1. 1. 2016 goes on Výpis z evidence
        (DPHEVD), a different form — not on an older kontrolní hlášení. The
        schema says so itself, so the floor is the form's and not ours."""
        Version = self.env["cssk.control.statement.version"]
        found = Version.search([
            ("country_id.code", "=", "CZ"),
            ("valid_from", "<=", "2015-12-31"),
            "|", ("valid_to", "=", False), ("valid_to", ">=", "2015-12-31"),
        ])
        self.assertFalse(found, "before 2016 the KH did not apply")
        covered = Version.search([
            ("country_id.code", "=", "CZ"),
            ("valid_from", "<=", "2021-03-01"),
            "|", ("valid_to", "=", False), ("valid_to", ">=", "2021-03-31"),
        ])
        self.assertTrue(covered, "a 2021 period must resolve the current form")

    def test_the_declared_structure_version_matches_the_pin(self):
        """`verzePis` is the one thing about the structure that NOTHING can
        check: the XSD declares it `xs:string` with no fixed value, so a stale
        literal validates exactly as cleanly as a current one. It was stale —
        03.01.10 against a published 03.01.14 — and only a hand-kept pin makes
        the drift visible. This ties the two together so they cannot part
        again silently."""
        import os
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pin = open(os.path.join(here, "data", "SCHEMA_VERSION"),
                   encoding="utf-8").readline().split()[1]
        template = open(os.path.join(here, "report",
                                     "l10n_cz_kh_templates.xml"),
                        encoding="utf-8").read()
        self.assertIn('verzePis="%s"' % pin, template,
                      "template declares a different structure version than "
                      "data/SCHEMA_VERSION pins")

    def _eu_tax(self):
        return self.env["account.tax"].search([
            ("type_tax_use", "=", "purchase"),
            ("company_id", "=", self.company.id),
            ("amount", "=", 21.0), ("name", "like", "EU G"),
        ], limit=1)

    def test_self_assessment_is_structural_not_the_flag(self):
        """``cssk_control_is_reverse_charge`` answers a narrower question than
        the amount logic needs, and the two must not be conflated.

        The flag marks the DOMESTIC § 92a reverse charge for the section
        resolver; the CZ module keeps intra-EU acquisitions out of it on
        purpose. But an EU acquisition nets its output and deduction legs on
        one line exactly as § 92a does, so the amount logic has to recognise it
        from the repartition instead.
        """
        eu = self._eu_tax()
        self.assertTrue(eu, "the CZ chart ships intra-EU acquisition taxes")
        self.assertFalse(eu.cssk_control_is_reverse_charge,
                         "unflagged BY DESIGN — the resolver wants A2, not B1")
        self.assertTrue(eu._cssk_self_assesses(),
                        "but it does self-assess, and the amount must say so")
        # An ordinary output tax has a single +100 tax leg and must not match,
        # or every ordinary row would have its tax invented twice over.
        self.assertFalse(self.tax21._cssk_self_assesses())

    def test_eu_acquisition_reports_its_self_assessed_tax(self):
        """oddíl A2 reports base AND tax (dan1). The self-assessed pair nets to
        ~0 through compute_all, so without the flat recovery the row exported
        with a base and no tax — XSD-valid, since dan1 is optional, and false.
        Asserted on the rendered XML rather than the row, because that is the
        artefact that would have been filed."""
        supplier = self.env["res.partner"].create({
            "name": "Dodavatel SK", "country_id": self.env.ref("base.sk").id,
            "vat": "SK2023907490",
        })
        eu = self._eu_tax()
        bill = self.env["account.move"].create({
            "move_type": "in_invoice", "partner_id": supplier.id,
            "invoice_date": fields.Date.context_today(self.env.user),
            "ref": "EU-ACQ-1",
            "invoice_line_ids": [Command.create({
                "name": "zboží z EU", "quantity": 1, "price_unit": 10000.0,
                "tax_ids": [Command.set(eu.ids)]})],
        })
        bill.action_post()
        line = bill.invoice_line_ids
        base, tax = line._cssk_base_and_tax_amounts()
        self.assertAlmostEqual(base, 10000.0, places=2)
        self.assertAlmostEqual(tax, 2100.0, places=2,
                               msg="self-assessed output recovered as base x rate")

        st = self._statement()
        row = st.cz_a2_ids
        self.assertTrue(row, "an EU acquisition belongs in oddíl A2")
        self.assertAlmostEqual(row.base_std, 10000.0, places=2)
        self.assertAlmostEqual(row.tax_std, 2100.0, places=2)

        st.action_export_xml()
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        veta = root.find(".//VetaA2")
        self.assertIsNotNone(veta)
        self.assertEqual(veta.get("zakl_dane1"), "10000")
        self.assertEqual(veta.get("dan1"), "2100",
                         "dan1 is optional in the XSD — absent exports clean")

    # The c_ufo preflight itself lives in l10n_cz_statutory, which has no
    # concrete statement to export — these exercise it through the real KH
    # export path, which is the only place it can actually be observed.
    def test_preflight_missing_tax_authority(self):
        """No finanční úřad on the company blocks the export by name.

        The templates emit ``c_ufo="…" or ''``, so an unset office renders an
        empty attribute and the user would otherwise get an XSD decimal error
        naming neither the field nor where to set it.
        """
        self._sale(15000.0)
        st = self._statement()
        self.company.l10n_cssk_tax_authority_id = False
        with self.assertRaises(UserError) as cm:
            st.action_export_xml()
        msg = str(cm.exception)
        self.assertIn("c_ufo", msg)
        self.assertIn(self.company.display_name, msg)
        self.assertEqual(st.state, "preview", "fail-early: nothing exported")

    def test_preflight_workplace_names_its_region(self):
        """A územní pracoviště is the likely wrong pick (214 of 229 seeded
        offices are workplaces), and its 4-digit code cannot be a c_ufo —
        xs:decimal totalDigits=3. The error must name the parent region as
        the fix rather than merely rejecting the value."""
        workplace = self.env["cssk.tax.authority"].search([
            ("country_code", "=", "CZ"),
            ("parent_authority_id", "!=", False),
        ], limit=1)
        self.assertTrue(workplace, "l10n_cz_statutory seeds územní pracoviště")
        self._sale(15000.0)
        st = self._statement()
        self.company.l10n_cssk_tax_authority_id = workplace
        with self.assertRaises(UserError) as cm:
            st.action_export_xml()
        msg = str(cm.exception)
        self.assertIn(workplace.parent_authority_id.display_name, msg,
                      "the regional office is the fix and must be named")
        self.assertEqual(st.state, "preview")

    def test_preflight_accepts_every_seeded_region(self):
        """Guard the check against the seed: each regional office (no parent)
        must satisfy it, so a future codelist refresh that widened a code
        fails here rather than at a customer's export."""
        regions = self.env["cssk.tax.authority"].search([
            ("country_code", "=", "CZ"), ("parent_authority_id", "=", False)])
        self.assertTrue(regions)
        bad = [a.display_name for a in regions
               if not ((a.submission_code or "").isdigit()
                       and len(a.submission_code) <= 3)]
        self.assertFalse(bad, "regional offices must render a valid c_ufo: %s" % bad)

    def test_detail_rows_use_base_drill_mixin(self):
        """The CZ rows inherit the base section mixin: partner_vat keeps the
        full snapshot, partner_vat_stripped the DIČ the XML renders, the
        source lines are linked and reconcile against the std/red split."""
        self._sale(15000.0)
        st = self._statement()
        row = st.cz_a4_ids
        self.assertEqual(row.partner_vat, "CZ46342958")
        self.assertEqual(row.partner_vat_stripped, "46342958")
        self.assertTrue(row.move_line_id)
        self.assertEqual(row.move_id, row.move_line_id.move_id)
        self.assertTrue(row.source_move_line_ids)
        self.assertTrue(row.source_reconciles,
                        "source lines must reconcile with base_std/tax_std")
        act = row.action_view_source_lines()
        self.assertEqual(act["res_model"], "account.move.line")
        self.assertEqual(act["domain"],
                         [("id", "in", row.source_move_line_ids.ids)])

    def test_aggregate_rows_carry_source_lines(self):
        """A5/B3 aggregates keep the ≤10k documents' move lines as their
        source, so the drill-down works and the reconcile check is meaningful
        (it used to be permanently 'failed' on empty source lines)."""
        inv1 = self._sale(5000.0)
        inv2 = self._sale(3000.0)
        st = self._statement()
        agg = st.cz_a5_ids
        self.assertEqual(len(agg), 1)
        self.assertAlmostEqual(agg.base_std, 8000.0, places=2)
        self.assertEqual(agg.row_count, 2)
        self.assertEqual(set(agg.source_move_line_ids.move_id.ids),
                         {inv1.id, inv2.id})
        self.assertTrue(
            agg.source_reconciles,
            "the aggregate's source lines must sum to its std/red totals")

    def test_sk_amendment_machinery_inert_for_cz(self):
        """The rows inherit kod_opravy/_kv_snapshot from the base mixin (SK
        dodatočný-KV flow) — they must stay inert for CZ: the country guard
        keeps _is_dodatocny() False even if a CZ type ever carried the SK
        fa_xml_value 'D', and a computed KH never sets kod_opravy."""
        self._sale(15000.0)
        st = self._statement()
        self.assertIn("kod_opravy", st.cz_a4_ids._fields)
        self.assertFalse(st.cz_a4_ids.kod_opravy)
        self.assertFalse(st._is_dodatocny())
        # even with the SK 'D' marker on the type, CZ never runs the SK delta
        st.statement_type_id.fa_xml_value = "D"
        self.assertFalse(st._is_dodatocny())

    def test_kv_vat_normalizer_strips_inner_whitespace(self):
        """_cssk_partner_vat_stripped goes through the shared normalize_vat:
        lowercase + inner spaces no longer leak into the statement rows."""
        inv = self._sale(15000.0)
        line = inv.invoice_line_ids[0]
        line.cssk_control_partner_vat_override = "cz 463 429 58"
        self.assertEqual(line._cssk_partner_vat_stripped(), "46342958")

    def test_credit_note_above_threshold_is_b2_detail(self):
        """A −50 000 CZK vendor credit note must be a B2 DETAIL row: the
        10 000 CZK per-document split compares the MAGNITUDE of the signed
        document total, so a large negative document must not hide in the B3
        aggregate. The threshold itself comes from the version record."""
        vat40 = self.env["account.account.tag"]._get_tax_tags(
            "VAT 40 Base", self.env.ref("base.cz").id)
        tax21p = self.env["account.tax"].search([
            ("type_tax_use", "=", "purchase"), ("amount", "=", 21.0),
            ("company_id", "=", self.company.id),
            ("invoice_repartition_line_ids.tag_ids", "in", vat40.ids),
        ], limit=1)
        self.assertTrue(tax21p, "domestic 21% purchase tax not found")
        # The version record is the authoritative threshold source.
        self.assertAlmostEqual(self.version.threshold_value, 10000.0, places=2)
        cn = self.env["account.move"].create({
            "move_type": "in_refund", "partner_id": self.partner.id,
            "invoice_date": fields.Date.context_today(self.env.user),
            "invoice_line_ids": [Command.create({
                "name": "storno", "quantity": 1, "price_unit": 50000.0,
                "tax_ids": [Command.set(tax21p.ids)]})],
        })
        cn.action_post()
        st = self._statement()
        self.assertEqual(
            len(st.cz_b2_ids), 1,
            "a -50 000 credit note is above-threshold -> B2 detail row")
        self.assertEqual(
            len(st.cz_b3_ids), 0,
            "the credit note must NOT land in the <=10k B3 aggregate")
        self.assertAlmostEqual(st.cz_b2_ids.base_std, -50000.0, places=2)
        self.assertAlmostEqual(st.cz_b2_ids.tax_std, -10500.0, places=2)


    def test_acquisition_recorded_as_an_entry_reaches_A2(self):
        """A self-assessed acquisition is an entry, not a bill.

        Source systems record intra-EU acquisitions as an internal document,
        and so does a hand-written self-assessment. Classifying only
        invoice-shaped moves drops them out of the statement silently — A2 came
        out empty against a filed 2.9M.
        """
        eu_tax = self.env["account.tax"].search([
            ("company_id", "=", self.company.id),
            ("type_tax_use", "=", "purchase"),
            ("cssk_control_is_reverse_charge", "=", False),
        ], limit=1)
        partner = self.env["res.partner"].create({
            "name": "DE supplier", "country_id": self.env.ref("base.de").id,
            "vat": "DE284625197",
        })
        account = self.company_data["default_account_expense"]
        move = self.env["account.move"].create({
            "move_type": "entry",
            "date": "2025-06-15",
            "partner_id": partner.id,
            "line_ids": [
                (0, 0, {"name": "acquisition base", "account_id": account.id,
                        "debit": 1000.0, "partner_id": partner.id,
                        "tax_ids": [(6, 0, eu_tax.ids)]}),
                (0, 0, {"name": "contra", "account_id": account.id,
                        "credit": 1000.0, "partner_id": partner.id}),
            ],
        })
        move.action_post()
        base = move.line_ids.filtered(lambda line: line.tax_ids)
        self.assertTrue(base.cssk_control_section_code,
                        "an acquisition booked as an entry got no KH section")
        self.assertEqual(base.cssk_control_section_code, "A2")

    def test_a_registration_used_decides_the_section_not_the_nationality(self):
        """A foreign supplier invoicing under a CZ registration supplies here.

        The section follows the VAT number the supply was **made under**, not
        where the counterparty is from. A German supplier registered for Czech
        VAT that invoices under its CZ number makes a domestic supply: it
        belongs in B2, and companies file it there. Reading the partner's
        country instead sent every such document to A2 — on one imported
        agenda that was 1.5 M of section B2 reported as intra-EU acquisitions.
        """
        eu_tax = self.env["account.tax"].search([
            ("company_id", "=", self.company.id),
            ("type_tax_use", "=", "purchase"),
            ("cssk_control_is_reverse_charge", "=", False),
        ], limit=1)
        partner = self.env["res.partner"].create({
            "name": "DE supplier with a CZ registration",
            "country_id": self.env.ref("base.de").id,
            "vat": "DE284625197",
        })
        account = self.company_data["default_account_expense"]
        move = self.env["account.move"].create({
            "move_type": "in_invoice",
            "invoice_date": "2025-06-15",
            "partner_id": partner.id,
            "invoice_line_ids": [
                (0, 0, {"name": "goods", "account_id": account.id,
                        "quantity": 1, "price_unit": 20000.0,
                        "tax_ids": [(6, 0, eu_tax.ids)]}),
            ],
        })
        base = move.invoice_line_ids
        move.action_post()
        self.assertEqual(base.cssk_control_section_code, "A2",
                         "with only the German number known it is an acquisition")

        # The document says the supply was invoiced under the CZ registration.
        base.cssk_control_partner_vat_override = "CZ686622235"
        base.invalidate_recordset(["cssk_control_section_code"])
        base._compute_cssk_control_section_code()
        self.assertEqual(base.cssk_control_section_code, "B2",
                         "invoiced under a CZ number, so a domestic supply")

    def test_a_no_vat_at_all_still_falls_back_to_the_country(self):
        """The partner's country remains the answer when no VAT is known."""
        eu_tax = self.env["account.tax"].search([
            ("company_id", "=", self.company.id),
            ("type_tax_use", "=", "purchase"),
            ("cssk_control_is_reverse_charge", "=", False),
        ], limit=1)
        partner = self.env["res.partner"].create({
            "name": "DE supplier without a VAT id",
            "country_id": self.env.ref("base.de").id,
        })
        account = self.company_data["default_account_expense"]
        move = self.env["account.move"].create({
            "move_type": "in_invoice",
            "invoice_date": "2025-06-15",
            "partner_id": partner.id,
            "invoice_line_ids": [
                (0, 0, {"name": "goods", "account_id": account.id,
                        "quantity": 1, "price_unit": 20000.0,
                        "tax_ids": [(6, 0, eu_tax.ids)]}),
            ],
        })
        move.action_post()
        self.assertEqual(move.invoice_line_ids.cssk_control_section_code, "A2")

    def test_a_document_carrying_no_vat_is_not_a_taxable_supply(self):
        """A4/A5 and B2/B3 report taxable supplies; a zero-VAT document is not one.

        Measured against 59 filed control statements: 52 documents produced a
        zero-tax row and 50 of them appear in no section of any filing.
        Reporting them added 2 702 504 to B2 and 439 917 to A4.

        The guard must not reach A1/B1, where a §92a reverse charge carries no
        VAT by design because the recipient self-assesses — those two sections
        agree with every filed statement and must stay that way.
        """
        zero = self.env["account.tax"].create({
            "name": "CZ 0% not taxable", "amount": 0.0, "amount_type": "percent",
            "type_tax_use": "purchase", "company_id": self.company.id,
        })
        partner = self.env["res.partner"].create({
            "name": "Domestic supplier", "vat": "CZ12345679",
            "country_id": self.env.ref("base.cz").id,
        })
        account = self.company_data["default_account_expense"]
        today = fields.Date.context_today(self.env.user)
        move = self.env["account.move"].create({
            "move_type": "in_invoice",
            "invoice_date": today.replace(day=15),
            "partner_id": partner.id,
            "invoice_line_ids": [(0, 0, {
                "name": "exempt purchase", "account_id": account.id,
                "quantity": 1, "price_unit": 50000.0,
                "tax_ids": [(6, 0, zero.ids)]})],
        })
        move.action_post()
        self.assertEqual(move.invoice_line_ids.cssk_control_section_code, "B2",
                         "the line still classifies; it is the ROW that is dropped")

        statement = self._statement()
        refs = statement.cz_b2_ids.mapped("entry_ref")
        self.assertNotIn(move.ref or move.name, refs,
                         "a document carrying no VAT produces no B2 row")
        self.assertFalse(
            statement.cz_b3_ids.filtered(lambda r: r.row_count),
            "nor does it fall into the below-threshold aggregate",
        )

    def test_an_exempt_line_does_not_swell_a_taxable_document(self):
        """The rule is per LINE, not per document.

        An invoice carrying a taxed line and an exempt one is filed for its
        taxable part alone. Seven documents of one agenda reported a base of
        67 476 against a filed 10 476 — and the TAX agreed to the cent on both
        sides, which is what gives the shape away: the 57 000 difference was an
        untaxed line riding along on a taxed document.
        """
        std = self.env["account.tax"].search([
            ("company_id", "=", self.company.id),
            ("type_tax_use", "=", "sale"),
            ("amount", "=", 21.0),
        ], limit=1)
        zero = self.env["account.tax"].create({
            "name": "CZ 0% exempt sale", "amount": 0.0, "amount_type": "percent",
            "type_tax_use": "sale", "company_id": self.company.id,
        })
        partner = self.env["res.partner"].create({
            "name": "Domestic customer", "vat": "CZ12345679",
            "country_id": self.env.ref("base.cz").id,
        })
        account = self.company_data["default_account_revenue"]
        today = fields.Date.context_today(self.env.user)
        move = self.env["account.move"].create({
            "move_type": "out_invoice",
            "invoice_date": today.replace(day=15),
            "partner_id": partner.id,
            "invoice_line_ids": [
                (0, 0, {"name": "taxed", "account_id": account.id,
                        "quantity": 1, "price_unit": 10476.0,
                        "tax_ids": [(6, 0, std.ids)]}),
                (0, 0, {"name": "exempt", "account_id": account.id,
                        "quantity": 1, "price_unit": 57000.0,
                        "tax_ids": [(6, 0, zero.ids)]}),
            ],
        })
        move.action_post()
        statement = self._statement()
        row = statement.cz_a4_ids.filtered(
            lambda r: r.entry_ref == (move.ref or move.name))
        self.assertTrue(row, "the taxed part still belongs in A4")
        self.assertAlmostEqual(
            (row.base_std or 0.0) + (row.base_red or 0.0), 10476.0, places=2,
            msg="the exempt line must not swell the reported base")

    def test_a_supply_to_someone_without_a_dic_stays_in_the_aggregate(self):
        """A4 identifies the customer by DIČ, so a customer with none cannot go there.

        Whatever it is worth. Across 59 filed control statements every
        disagreement about the split went one way — 12 documents the company
        filed in A5 were reported as A4 here, none the other way — and 13 of
        the 23 misplaced carried no counterparty VAT against 0.7 % of the 4 212
        agreed ones.

        The purchase side is deliberately NOT symmetric (see _cz_is_detailed):
        requiring a DIČ there moved B2 from 26 periods agreeing to 17.
        """
        std = self.env["account.tax"].search([
            ("company_id", "=", self.company.id),
            ("type_tax_use", "=", "sale"), ("amount", "=", 21.0)], limit=1)
        account = self.company_data["default_account_revenue"]
        today = fields.Date.context_today(self.env.user)

        def sale(partner, price):
            move = self.env["account.move"].create({
                "move_type": "out_invoice", "partner_id": partner.id,
                "invoice_date": today.replace(day=15),
                "invoice_line_ids": [(0, 0, {
                    "name": "goods", "account_id": account.id,
                    "quantity": 1, "price_unit": price,
                    "tax_ids": [(6, 0, std.ids)]})],
            })
            move.action_post()
            return move

        registered = self.env["res.partner"].create({
            "name": "Registered customer", "vat": "CZ12345679",
            "country_id": self.env.ref("base.cz").id})
        consumer = self.env["res.partner"].create({
            "name": "Private individual",
            "country_id": self.env.ref("base.cz").id})
        big_registered = sale(registered, 50000.0)
        big_consumer = sale(consumer, 50000.0)

        statement = self._statement()
        detail = statement.cz_a4_ids.mapped("entry_ref")
        self.assertIn(big_registered.ref or big_registered.name, detail,
                      "a large supply to a VAT-registered customer is A4 detail")
        self.assertNotIn(big_consumer.ref or big_consumer.name, detail,
                         "a customer with no DIČ cannot be named in A4, however "
                         "large the supply")
        self.assertTrue(statement.cz_a5_ids.filtered(lambda r: r.row_count),
                        "it belongs in the A5 aggregate instead")

    def test_mixed_direction_entry_is_left_unclassified(self):
        """Ambiguity is not resolved by guessing."""
        sale = self.env["account.tax"].search([
            ("company_id", "=", self.company.id),
            ("type_tax_use", "=", "sale")], limit=1)
        purchase = self.env["account.tax"].search([
            ("company_id", "=", self.company.id),
            ("type_tax_use", "=", "purchase")], limit=1)
        account = self.company_data["default_account_expense"]
        move = self.env["account.move"].create({
            "move_type": "entry",
            "date": "2025-06-15",
            "line_ids": [
                (0, 0, {"name": "a", "account_id": account.id, "debit": 100.0,
                        "tax_ids": [(6, 0, (sale | purchase).ids)]}),
                (0, 0, {"name": "b", "account_id": account.id, "credit": 100.0}),
            ],
        })
        move.action_post()
        mixed = move.line_ids.filtered(lambda line: len(line.tax_ids) > 1)
        self.assertFalse(mixed.cssk_control_section_code)


    def test_a_czech_row_keeps_whitespace_in_its_identity(self):
        """The Czech KH writes ``c_evid_dd`` as stored, so whitespace can tell
        two documents apart there. Only the Slovak form, which cannot carry
        it, identifies its rows without it."""
        Row = self.env["l10n.cz.kh.a4"]
        self.assertNotEqual(
            Row.new({"partner_vat": "CZ25856294", "entry_ref": "AB 12"})._kv_identity(),
            Row.new({"partner_vat": "CZ25856294", "entry_ref": "AB12"})._kv_identity())
