import base64

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class TestSkVatReturn(TransactionCase):
    """Smoke tests for the SK VAT return country layer (run at install)."""

    def test_version_seeded(self):
        version = self.env.ref("l10n_sk_vat_return.dph_version_2025")
        self.assertEqual(version.country_id.code, "SK")
        self.assertEqual(version.xml_root_element, "dokument")
        self.assertTrue(version.xml_schema_data, "DPH XSD not loaded")
        codes = set(version.line_def_ids.mapped("code"))
        self.assertIn("r03", codes)
        self.assertIn("r17", codes)


@tagged("post_install", "-at_install")
class TestSkVatReturnCompute(AccountTestInvoicingCommon):
    """Functional: post a standard-rate sale, compute + export the DPH return."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        # Identification fields the official dph2025 schema needs.
        cls.company.write({
            "vat": "SK2023456787", "city": "Bratislava",
            "country_id": cls.env.ref("base.sk").id,
        })
        cls.tax_sale = cls.tax_sale_a
        cls.version = cls.env.ref("l10n_sk_vat_return.dph_version_2025")

    def _make_return(self):
        return self.env["cssk.vat.return"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": self.version.statement_type_ids[0].id,
        })

    def test_compute_and_export(self):
        self.init_invoice(
            "out_invoice", partner=self.partner_a,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_sale, post=True,
        )
        ret = self._make_return()
        ret.action_compute_lines()
        vals = {line.code: line.value for line in ret.line_ids}
        # Output VAT total, and the NET-payable computation (mirrors l10n_sk):
        # sale only → 230 output, 0 deductions → own liability 230, excess 0.
        self.assertAlmostEqual(vals["r17"], 230.0, places=2)      # total output VAT
        self.assertAlmostEqual(vals["r_net"], 230.0, places=2)    # net
        self.assertAlmostEqual(vals["r32"], 230.0, places=2)      # own VAT liability
        self.assertAlmostEqual(vals["r33"], 0.0, places=2)        # excess deduction
        self.assertAlmostEqual(vals["r35"], 230.0, places=2)      # to be paid

        # Validates against the OFFICIAL dph2025.xsd (root 'dokument', eForm).
        ret.action_export_xml()
        self.assertEqual(ret.state, "exported")
        root = etree.fromstring(base64.b64decode(ret.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).localname, "dokument")
        self.assertEqual(root.findtext(".//telo/r17"), "230.00")
        self.assertEqual(root.findtext(".//telo/r32"), "230.00")
        self.assertEqual(root.findtext(".//telo/r35"), "230.00")
        self.assertEqual(root.findtext(".//hlavicka/zdanObd/rok"), "2026")

    def test_manual_journal_entry_matches_invoice(self):
        """A MANUAL misc-journal entry booking the same output VAT as an
        invoice must contribute to the return lines exactly like the invoice.

        Odoo 19 removed ``tax_tag_invert``: the tag data is unsigned and the
        core tax_tags engine sums RAW signed balances, applying only the
        formula-level '-' sign — which is precisely ``_eval_tags``'s contract.
        This guards that a misc entry (credit income + auto tax line) and an
        equivalent customer invoice produce identical r03/r04/r17 deltas."""
        rate = self.tax_sale.amount
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale, post=True)
        ret = self._make_return()
        ret.action_compute_lines()
        vals_inv = {line.code: line.value for line in ret.line_ids}

        entry = self.env["account.move"].create({
            "move_type": "entry",
            "date": "2026-06-15",
            "line_ids": [
                Command.create({
                    "account_id": self.company_data[
                        "default_account_receivable"].id,
                    "debit": round(1000.0 * (1 + rate / 100.0), 2),
                    "credit": 0.0,
                }),
                Command.create({
                    "account_id": self.company_data[
                        "default_account_revenue"].id,
                    "debit": 0.0, "credit": 1000.0,
                    "tax_ids": [Command.set(self.tax_sale.ids)],
                }),
            ],
        })
        entry.action_post()
        # The auto-created tax line and the tagged base line must feed the
        # return exactly like the invoice flow does.
        self.assertTrue(entry.line_ids.tax_tag_ids,
                        "the manual entry must carry tax tags")

        ret.action_compute_lines()
        vals = {line.code: line.value for line in ret.line_ids}
        self.assertAlmostEqual(
            vals["r03"], vals_inv["r03"] + 1000.0, places=2,
            msg="manual entry base must add like an invoice base")
        self.assertAlmostEqual(
            vals["r04"], vals_inv["r04"] + 1000.0 * rate / 100.0, places=2,
            msg="manual entry VAT must add like an invoice VAT")
        self.assertAlmostEqual(
            vals["r17"], vals_inv["r17"] + 1000.0 * rate / 100.0, places=2)

    def test_submit_lock_and_retention(self):
        """Submitting freezes the filed XML and locks the return; reset keeps
        the filed copy (the 'posledná známa daň' baseline)."""
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale, post=True)
        ret = self._make_return()
        ret.action_compute_lines()
        ret.action_export_xml()
        filed = ret.xml_attachment_id
        self.assertTrue(filed)

        ret.submission_reference = "FS-2026-0001"
        ret.action_submit()
        self.assertEqual(ret.state, "submitted")
        self.assertEqual(ret.submitted_attachment_id, filed)  # frozen filed copy
        self.assertTrue(ret.submitted_date)

        # A submitted return is locked against re-export and recompute.
        with self.assertRaises(UserError):
            ret.action_export_xml()
        with self.assertRaises(UserError):
            ret.action_compute_lines()

        # Reset is the explicit unlock; the filed copy survives it.
        ret.action_reset_to_draft()
        self.assertEqual(ret.state, "draft")
        self.assertEqual(ret.submitted_attachment_id, filed)

    def test_dodatocne_amendment_r36(self):
        """Create a dodatočné from a submitted original: it links back, and r36
        (rozdiel oproti poslednej známej dani) auto-fills from the original."""
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale, post=True)
        orig = self._make_return()
        orig.action_compute_lines()
        orig.action_export_xml()
        orig.action_submit()
        orig_net = (orig.line_ids.filtered(lambda l: l.code == "r32").value
                    - orig.line_ids.filtered(lambda l: l.code == "r33").value)

        action = orig.action_create_amendment()
        amend = self.env["cssk.vat.return"].browse(action["res_id"])
        self.assertEqual(amend.original_return_id, orig)
        self.assertEqual(amend.state, "draft")

        # A corrective sale of 500 is booked, then the dodatočné is recomputed.
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-20",
            amounts=[500.0], taxes=self.tax_sale, post=True)
        amend.action_compute_lines()
        new_net = (amend.line_ids.filtered(lambda l: l.code == "r32").value
                   - amend.line_ids.filtered(lambda l: l.code == "r33").value)
        r36 = amend.line_ids.filtered(lambda l: l.code == "r36").value
        # r36 = new − posledná známa daň = the daň on the extra 500 @ 23 %.
        self.assertAlmostEqual(r36, new_net - orig_net, places=2)
        self.assertAlmostEqual(r36, 500.0 * self.tax_sale.amount / 100.0, places=2)

        # As a dodatočné it carries the deň zistenia (datumZisteniaDdp), defaulted
        # to today on creation, and emits ddp=1 in the XML.
        self.assertTrue(amend.discovery_date)
        ddp = self.version.statement_type_ids.filtered(lambda t: t.fa_xml_value == "D")
        amend.statement_type_id = ddp[0].id
        amend.action_export_xml()
        root = etree.fromstring(base64.b64decode(amend.xml_attachment_id.datas))
        self.assertEqual(root.findtext(".//typDP/ddp"), "1")
        self.assertTrue(root.findtext(".//typDP/datumZisteniaDdp"),
                        "datumZisteniaDdp must be filled on a dodatočné")

    def test_kontroly(self):
        """daň = základ × sadzba content check: clean on a 23 % sale, and a
        mistuned daň row is flagged (DPH_RATE)."""
        self.init_invoice(
            "out_invoice", partner=self.partner_a,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_sale, post=True,
        )
        ret = self._make_return()
        ret.action_compute_lines()
        # r03 (základ 1000) / r04 (daň 230) -> implied 23 % == základná sadzba.
        self.assertEqual(
            ret.check_kontroly(), [],
            "a correctly-taxed 23 %% sale must pass the rate kontroly")

        # Force a wrong rate on r04 (daň 100 on základ 1000 -> 10 %, not 23/19/5).
        r04 = ret.line_ids.filtered(lambda line: line.code == "r04")
        r04.write({"is_overridden": True, "manual_value": 100.0})
        ret.action_compute_lines()
        codes = [v["code"] for v in ret.check_kontroly()]
        self.assertIn("DPH_RATE", codes,
                      "kontroly must flag daň that is not základ × platná sadzba")

    def test_settlement_codes_and_rate_pairs_from_version_data(self):
        """Task-4 regression: the r32/r33/r36 settlement + amendment codes
        and the daň = základ × sadzba pairing are version DATA (fields on the
        version record), not hardcoded — clearing rate_pairs removes the
        DPH_RATE rule."""
        self.assertEqual(self.version.own_tax_line_code, "r32")
        self.assertEqual(self.version.excess_line_code, "r33")
        self.assertEqual(self.version.diff_line_code, "r36")
        self.assertIn(["r03", "r04", 23.0], self.version.rate_pairs)
        self.assertIn(["r01a", "r02a", 5.0], self.version.rate_pairs)

        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale, post=True)
        ret = self._make_return()
        ret.action_compute_lines()
        # settlement codes drive to_pay (own liability 230, excess 0)
        self.assertAlmostEqual(ret.to_pay, 230.0, places=2)

        # mistune r04 → the data-driven rate rule flags it …
        r04 = ret.line_ids.filtered(lambda line: line.code == "r04")
        r04.write({"is_overridden": True, "manual_value": 100.0})
        ret.action_compute_lines()
        self.assertIn("DPH_RATE", [v["code"] for v in ret.check_kontroly()])
        # … and WITHOUT the version data the rule disappears (nothing left
        # hardcoded in the module)
        self.version.rate_pairs = False
        self.assertNotIn("DPH_RATE",
                         [v["code"] for v in ret.check_kontroly()])

    def test_manual_override_carryover(self):
        self.init_invoice(
            "out_invoice", partner=self.partner_a,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_sale, post=True,
        )
        ret = self._make_return()
        ret.action_compute_lines()
        vals = {line.code: line.value for line in ret.line_ids}
        self.assertAlmostEqual(vals["r35"], 230.0, places=2)  # no override yet

        # Override r34 (excess-deduction offset, a carryover line) = 50.
        r34 = ret.line_ids.filtered(lambda line: line.code == "r34")
        r34.write({"is_overridden": True, "manual_value": 50.0})
        ret.action_compute_lines()

        vals = {line.code: line.value for line in ret.line_ids}
        self.assertAlmostEqual(vals["r34"], 50.0, places=2)   # override applied
        self.assertAlmostEqual(vals["r35"], 180.0, places=2)  # 230 − 50 (flows through)

        # Override survives the recompute.
        r34 = ret.line_ids.filtered(lambda line: line.code == "r34")
        self.assertTrue(r34.is_overridden)
        self.assertAlmostEqual(r34.manual_value, 50.0, places=2)
