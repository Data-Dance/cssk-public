# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import hashlib
from io import BytesIO
import json
import re

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import new_test_user
from odoo.tools import file_open
from odoo.tools.pdf import PdfReader

from ..models.official_pdf import render_official_form


@tagged("post_install", "-at_install")
class TestDppoOfficialPdf(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write({"name": "Syntetická firma", "l10n_sk_dic": "2020317068",
                           "company_registry": "36000001", "street": "Hlavná 12",
                           "city": "Bratislava", "zip": "81101", "country_id": cls.env.ref("base.sk").id,
                           "phone": "+421905111222", "email": "test@example.invalid"})
        cls.person = cls.env["res.partner"].create({
            "name": "Jana Skúšobná", "is_company": False,
            "street": "Dlhá 8", "city": "Bratislava", "zip": "81101",
            "country_id": cls.env.ref("base.sk").id, "company_id": cls.company.id,
            "phone": "+421905222333", "email": "person@example.invalid"})

    def _make(self):
        ret = self.env["cssk.income.tax.return"].create({
            "company_id": self.company.id,
            "version_id": self.env.ref("l10n_sk_dppo.dppo_version_2026").id,
            "statement_type_id": self.env.ref("l10n_sk_dppo.dppo_type_R_2026").id,
            "date_from": "2027-01-01", "date_to": "2027-12-31",
            "l10n_sk_form_legal_code": "112", "l10n_sk_form_nace": "62010",
            "l10n_sk_form_prepared_on": "2028-03-01",
            "l10n_sk_form_minimum_exemption": True,
            "l10n_sk_form_person_id": self.person.id,
            "l10n_sk_form_person_first": "Jana", "l10n_sk_form_person_last": "Skúšobná",
            "l10n_sk_form_person_relationship": "štatutárny orgán",
        })
        ret.action_compute_lines()
        self._set(ret, r100=1000, r560=1000, r810=0, r1110=100,
                  a06=12.34, b01=25, b02=20)
        return ret

    def _set(self, ret, **values):
        # This suite explicitly imports synthetic reviewed opening figures.
        # Keep Table F source evidence separate from tax-row overrides.
        if "r100" in values or "r560" in values:
            revenue = values.get("r560", ret.l10n_sk_f_revenue)
            profit = values.get("r100", ret.l10n_sk_f_revenue - ret.l10n_sk_f_cost)
            ret.write({"l10n_sk_f_manual": True, "l10n_sk_f_revenue": revenue,
                       "l10n_sk_f_cost": revenue - profit,
                       "l10n_sk_f_evidence": "Synthetic reviewed opening P&L figures"})
        for code, value in values.items():
            ret.line_ids.filtered(lambda line: line.code == code).write({
                "manual_value": value, "is_overridden": True})
        ret.action_compute_lines()

    def test_advance_tax_1110_uses_base_before_deductions(self):
        ret = self._make()
        row = ret.line_ids.filtered(lambda line: line.code == "r1110")
        row.write({"is_overridden": False, "manual_value": 0})
        self._set(ret, r500=1000, r501=200, r610=10)
        self.assertEqual(ret.line_ids.filtered(lambda line: line.code == "r600").value, 80)
        self.assertEqual(ret.line_ids.filtered(lambda line: line.code == "r1110").value, 90)
        self._set(ret, r1110=73)
        self.assertEqual(ret.line_ids.filtered(lambda line: line.code == "r1110").value, 73)

    def test_advance_tax_legacy_relief_requires_evidence_and_omits_field(self):
        ret = self._make()
        ret.line_ids.filtered(lambda row: row.code == "r1110").write({"is_overridden": False})
        ret.l10n_sk_legacy_advance_relief = True
        with self.assertRaisesRegex(UserError, "Review the legacy"):
            with self.env.cr.savepoint():
                ret.action_compute_lines()
        ret.l10n_sk_legacy_advance_evidence = "Reviewed historic relief decision"
        self._set(ret, r610=5)
        self.assertNotIn("r1110", ret._l10n_sk_dppo_pdf_payload()["rows"])
        self._set(ret, r1110=0)
        self.assertEqual(ret.line_ids.filtered(lambda row: row.code == "r1110").value, 0)

    def test_table_fl_reviewed_import_and_native_revenue_adjustment(self):
        ret = self._make()
        self._set(ret, r110=100, r210=30)
        Line = self.env["l10n.sk.dppo.table.l.line"]
        Line.create([{"return_id": ret.id, "description": "Reviewed increase",
                      "amount": 100, "return_row": "110", "evidence": "Reviewed income source"},
                     {"return_id": ret.id, "description": "Reviewed exclusion",
                      "amount": -30, "return_row": "210", "evidence": "Reviewed exemption"}])
        with self.assertRaisesRegex(UserError, "Apply the reviewed Table L"):
            ret._l10n_sk_dppo_pdf_payload()
        ret.action_apply_table_l_revenue()
        data = ret._l10n_sk_dppo_pdf_payload()["table_fl"]
        self.assertEqual((data["revenue"], data["cost"], data["profit"], data["taxable"]),
                         (1000, 0, 1000, 1070))
        self.assertEqual(ret.line_ids.filtered(lambda row: row.code == "r560").value, 1070)
        ret.l10n_sk_table_l_ids[0].amount = 90
        with self.assertRaisesRegex(UserError, "Apply the reviewed Table L"):
            ret.action_post_provision()
        ret.l10n_sk_f_cost = 1
        with self.assertRaisesRegex(UserError, "Table F revenue less costs"):
            ret.action_apply_table_l_revenue()
        self.assertEqual(ret.line_ids.filtered(lambda row: row.code == "r560").value, 1070)

    def test_table_fl_ledger_zero_and_long_adjustment_output(self):
        ret = self._make()
        self._set(ret, r100=0, r560=0, r110=28)
        ret.l10n_sk_f_manual = False
        self.assertEqual(ret._l10n_sk_dppo_pdf_payload()["table_fl"]["revenue"], 0)
        self.env["l10n.sk.dppo.table.l.line"].create([
            {"return_id": ret.id, "description": "Reviewed income %s" % number,
             "amount": 1, "return_row": "110", "evidence": "Reviewed source"}
            for number in range(28)])
        ret.action_apply_table_l_revenue()
        raw = ret._l10n_sk_dppo_official_pdf()
        reader = PdfReader(BytesIO(raw))
        self.assertEqual(len(reader.pages), 22)
        self.assertIn("28", reader.pages[10].extract_text())
        self.assertIn("29", reader.pages[-1].extract_text())
        self.assertEqual(ret._l10n_sk_dppo_pdf_payload()["annex_count"], 6)
        ret.l10n_sk_table_l_ids[0].return_row = "1109"
        self.assertEqual(ret.l10n_sk_table_l_ids[0].return_row, "1109")
        with self.assertRaisesRegex(UserError, "Review each Table L"):
            ret._l10n_sk_dppo_pdf_payload()

    def test_table_fl_manual_evidence_and_source_relation(self):
        ret = self._make()
        ret.l10n_sk_f_evidence = False
        with self.assertRaisesRegex(UserError, "Retain the reviewed"):
            ret._l10n_sk_dppo_pdf_payload()
        ret.l10n_sk_f_evidence = "Reviewed external P&L"
        ret.l10n_sk_f_revenue = 1100
        with self.assertRaisesRegex(UserError, "Table F revenue less costs"):
            ret._l10n_sk_dppo_pdf_payload()

    def _assets(self):
        with file_open("l10n_sk_dppo/static/forms/DPPOv26.pdf", "rb") as source:
            template = source.read()
        with file_open("l10n_sk_dppo/static/forms/DPPOv26-layout.json") as source:
            layout = json.load(source)
        return template, layout

    def _table_i_item(self, ret, **values):
        return self.env["l10n.sk.dppo.table.i.line"].create({
            "return_id": ret.id, "transaction_code": "16", "partner_id": self.person.id,
            "resident_country_code": "703", "tax_effect": -12000, **values})

    def _table_d_item(self, ret, **values):
        return self.env["l10n.sk.dppo.table.d.line"].create({
            "return_id": ret.id, "column": "4", "date_from": "2026-01-01",
            "date_to": "2026-12-31", "loss_amount": 1000,
            "subsequent_period_number": 1, "deducted": 100, **values})

    def test_table_d_first_loss_next_year_native_deduction(self):
        first = self._make()
        first.l10n_sk_form_micro_taxpayer = True
        self._set(first, r100=-1000, r560=0, r1110=0, a06=0, b01=0, b02=0)
        self.assertEqual(first.line_ids.filtered(lambda row: row.code == "r400").value, -1000)
        self.assertFalse(first._l10n_sk_dppo_pdf_payload()["table_d"]["items"])
        following = self._make()
        following.write({"date_from": "2028-01-01", "date_to": "2028-12-31",
                         "l10n_sk_form_prepared_on": "2029-03-01",
                         "l10n_sk_form_minimum_exemption": False,
                         "l10n_sk_form_controlled_transactions": True,
                         "l10n_sk_table_i_below_threshold": True})
        self._set(following, r100=2000, r560=2000, r810=340, a06=0, b01=0, b02=0)
        item = self._table_d_item(following, date_from="2027-01-01", date_to="2027-12-31",
                                  source_return_id=first.id, deducted=600)
        with self.assertRaisesRegex(UserError, "Apply the reviewed"):
            following._l10n_sk_dppo_pdf_payload()
        following.action_apply_table_d_deduction()
        self._set(following, r1110=140)
        self.assertEqual(following.line_ids.filtered(lambda row: row.code == "r410").value, 600)
        self.assertEqual(following.line_ids.filtered(lambda row: row.code == "r500").value, 1400)
        self.assertEqual(item.remaining, 400)
        raw = following._l10n_sk_dppo_official_pdf()
        self.assertEqual(len(PdfReader(BytesIO(raw)).pages), 21)
        following.action_apply_table_d_deduction()
        self.assertEqual(following._l10n_sk_dppo_official_pdf(), raw)
        self.assertEqual(first.line_ids.filtered(lambda row: row.code == "r400").value, -1000)

    def test_table_d_fifty_percent_and_current_micro_status(self):
        ret = self._make()
        item = self._table_d_item(ret, loss_amount=2000, deducted=600)
        with self.assertRaisesRegex(UserError, "50 percent"):
            ret.action_apply_table_d_deduction()
        ret.l10n_sk_form_micro_taxpayer = True
        ret.action_apply_table_d_deduction()
        self._set(ret, r1110=41.73)
        self.assertEqual(ret._l10n_sk_dppo_pdf_payload()["table_d"]["total"], 600)
        ret.l10n_sk_form_controlled_transactions = True
        with self.assertRaisesRegex(UserError, "micro-taxpayer status"):
            ret._l10n_sk_dppo_table_d_payload()
        ret.l10n_sk_form_controlled_transactions = False
        ret.write({"date_to": "2027-06-30"})
        with self.assertRaisesRegex(UserError, "micro-taxpayer status"):
            ret._l10n_sk_dppo_table_d_payload()
        self.assertEqual(item.deducted, 600)

    def test_table_d_all_columns_final_period_and_special_records(self):
        ret = self._make()
        for column in range(1, 9):
            year = 2018 + column if column >= 4 else 2020
            self._table_d_item(ret, column=str(column), date_from=f"{year}-01-01",
                date_to=f"{year}-12-31", loss_amount=100, prior_deducted=10,
                deducted=20, subsequent_period_number=9-column if column >= 4 else 1)
        # The oldest ordinary loss is in its fifth following tax period.
        first = ret.l10n_sk_table_d_ids.filtered(lambda item: item.column == "4")
        self.assertEqual(first.remaining, 0)
        self.assertEqual(first.expired, 70)
        ret.l10n_sk_form_notes = "Osobitný odpočet: overené zaradenie a výpočet podľa príslušného režimu."
        ret.action_apply_table_d_deduction()
        self._set(ret, r1110=85.73)
        self.assertEqual(ret._l10n_sk_dppo_pdf_payload()["table_d"]["total"], 160)
        reader = PdfReader(BytesIO(ret._l10n_sk_dppo_official_pdf()))
        self.assertIn("Osobitný odpočet", reader.pages[14].extract_text())
        self.assertEqual(len(reader.pages), 21)

    def test_table_d_bad_period_balance_and_native_source(self):
        ret = self._make()
        item = self._table_d_item(ret)
        for values in ({"prior_deducted": 1000}, {"deducted": -1},
                       {"subsequent_period_number": 6}, {"subsequent_period_number": 2},
                       {"date_to": "2027-01-01"},
                       {"date_from": "2019-01-01"}, {"source_return_id": ret.id}):
            old = {key: item[key].id if key == "source_return_id" else item[key] for key in values}
            item.write(values)
            with self.assertRaises(UserError):
                ret.action_apply_table_d_deduction()
            item.write(old)
        duplicate = self._table_d_item(ret)
        with self.assertRaisesRegex(UserError, "only once"):
            ret.action_apply_table_d_deduction()
        duplicate.unlink()
        self.assertEqual(item.remaining, 900)

    def test_table_d_apply_rechecks_changed_base_atomically(self):
        ret = self._make()
        self._table_d_item(ret, deducted=400)
        row = ret.line_ids.filtered(lambda line: line.code == "r100")
        row.manual_value = 100
        with self.assertRaisesRegex(UserError, "50 percent"):
            ret.action_apply_table_d_deduction()
        self.assertEqual(ret.line_ids.filtered(lambda line: line.code == "r410").value, 0)
        self.assertEqual(ret.line_ids.filtered(lambda line: line.code == "r100").manual_value, 100)

    def test_table_d_changed_facts_block_provision(self):
        ret = self._make()
        item = self._table_d_item(ret)
        ret.action_apply_table_d_deduction()
        item.deducted = 200
        with self.assertRaisesRegex(UserError, "Apply the reviewed"):
            ret.action_post_provision()
        self.assertFalse(ret.provision_move_id)

    def test_annex_batch_normalization_and_atomic_parent_epochs(self):
        first, second = self._make(), self._make()
        parents = first | second
        parents.flush_recordset(["write_date"])
        before = {parent.id: parent.write_date for parent in parents}
        Line = self.env["l10n.sk.dppo.table.i.line"]
        values = [{"return_id": parent.id, "transaction_code": "16",
                   "partner_id": self.person.id, "resident_country_code": "703"}
                  for parent in (second, first)]
        bad = [dict(value) for value in values]
        bad[1]["currency_id"] = self.env.ref("base.USD").id
        with self.assertRaisesRegex(UserError, "return's currency"):
            Line.create(bad)
        parents.invalidate_recordset(["write_date"])
        self.assertEqual({parent.id: parent.write_date for parent in parents}, before)
        self.assertFalse(parents.l10n_sk_table_i_ids)
        created = Line.create(values)
        self.assertEqual(len(created), 2)
        second.state = "submitted"
        before_count = Line.search_count([("return_id", "in", parents.ids)])
        with self.assertRaisesRegex(UserError, "Reset the unfiled"):
            Line.create(values)
        self.assertEqual(Line.search_count([("return_id", "in", parents.ids)]), before_count)

    def test_table_i_signed_transactions_and_loan_disclosure(self):
        ret = self._make()
        ret.l10n_sk_form_controlled_transactions = True
        self._table_i_item(ret, aggregated=True, permanent_establishment_link=True)
        self._table_i_item(ret, transaction_code="25", tax_effect=6000)
        self._table_i_item(ret, section="loan", transaction_code="01", tax_effect=0,
                           highest_principal=110000, closing_principal=70000)
        ret.l10n_sk_table_i_below_threshold = True
        data = ret._l10n_sk_dppo_pdf_payload()
        self.assertEqual(data["table_i"]["transactions"][0]["effect"], -12000)
        self.assertEqual(data["table_i"]["loans"][0]["highest"], 110000)
        reader = PdfReader(BytesIO(ret._l10n_sk_dppo_official_pdf()))
        self.assertEqual(len(reader.pages), 21)
        self.assertIn("Jana Skúšobná", reader.pages[8].extract_text())
        self.assertIn("Jana Skúšobná", reader.pages[9].extract_text())
        # Disclosure includes timing effects; it must not overwrite r400 or GL.
        self.assertEqual(ret.line_ids.filtered(lambda row: row.code == "r400").value, 1017.34)

    def test_table_i_below_threshold_only_and_declaration_relation(self):
        ret = self._make()
        ret.l10n_sk_form_controlled_transactions = True
        with self.assertRaisesRegex(UserError, "declaration must agree"):
            ret._l10n_sk_dppo_pdf_payload()
        ret.l10n_sk_table_i_below_threshold = True
        self.assertTrue(ret._l10n_sk_dppo_pdf_payload()["table_i"]["below_threshold"])
        ret.l10n_sk_form_controlled_transactions = False
        with self.assertRaisesRegex(UserError, "declaration must agree"):
            ret._l10n_sk_dppo_pdf_payload()

    def test_table_i_continuations_and_statutory_limit(self):
        ret = self._make()
        ret.l10n_sk_form_controlled_transactions = True
        for index in range(5):
            self._table_i_item(ret, sequence=index, tax_effect=100.01 + index)
        for index in range(6):
            self._table_i_item(ret, sequence=index, section="loan", transaction_code="01",
                               tax_effect=0, highest_principal=1000 + index, closing_principal=index)
        data = ret._l10n_sk_dppo_pdf_payload()
        self.assertEqual(data["annex_count"], 7)
        raw = ret._l10n_sk_dppo_official_pdf()
        reader = PdfReader(BytesIO(raw))
        self.assertEqual(len(reader.pages), 23)
        self.assertIn("pokračovanie", reader.pages[21].extract_text())
        self.assertIn("pokračovanie", reader.pages[22].extract_text())
        self.assertIn("Jana Skúšobná", reader.pages[21].extract_text())
        self.assertIn("Príloha 6", reader.pages[21].extract_text())
        self.assertIn("Príloha 7", reader.pages[22].extract_text())
        for index in range(94):
            self._table_i_item(ret)
        self.assertEqual(len(ret._l10n_sk_dppo_pdf_payload()["table_i"]["transactions"]), 99)
        self._table_i_item(ret)
        with self.assertRaisesRegex(UserError, "at most 99"):
            ret._l10n_sk_dppo_pdf_payload()

    def test_table_i_invalid_codes_cent_precision_and_loan_relationship(self):
        ret = self._make()
        ret.l10n_sk_form_controlled_transactions = True
        item = self._table_i_item(ret)
        for values in ({"transaction_code": "38"}, {"transaction_code": "370"},
                       {"transaction_code": "1"}, {"resident_country_code": "7039"},
                       {"resident_country_code": "SK"}, {"resident_country_code": "000"},
                       {"highest_principal": 1}):
            with self.env.cr.savepoint():
                old = {key: item[key] for key in values}
                item.write(values)
                with self.assertRaises(UserError):
                    ret._l10n_sk_dppo_pdf_payload()
                item.write(old)
        item.write({"section": "loan", "transaction_code": "01", "tax_effect": 0,
                    "highest_principal": 100, "closing_principal": 101})
        with self.assertRaisesRegex(UserError, "closing principal"):
            ret._l10n_sk_dppo_pdf_payload()

    def test_table_i_native_copy_parent_company_and_filed_guards(self):
        ret = self._make()
        ret.l10n_sk_form_controlled_transactions = True
        item = self._table_i_item(ret)
        copied = ret.copy()
        self.assertEqual(copied.l10n_sk_table_i_ids.tax_effect, -12000)
        self.assertEqual(copied.l10n_sk_table_i_ids.return_id, copied)
        with self.assertRaisesRegex(UserError, "cannot be reassigned"):
            item.write({"return_id": copied.id})
        ret.state = "submitted"
        for operation in (lambda: item.write({"tax_effect": -1}), lambda: item.unlink(),
                          lambda: self._table_i_item(ret)):
            with self.assertRaisesRegex(UserError, "Reset the unfiled"):
                operation()

    def test_table_i_ordinary_accountant_and_company_isolation(self):
        ret = self._make()
        ret.l10n_sk_form_controlled_transactions = True
        user = new_test_user(self.env, login="table.i.accountant", groups="account.group_account_user",
                             company_id=self.company.id, company_ids=[self.company.id])
        self.assertFalse(user.has_group("account.group_account_manager"))
        ordinary = ret.with_user(user).with_company(self.company)
        item = self.env["l10n.sk.dppo.table.i.line"].with_user(user).with_company(self.company).create({
            "return_id": ret.id, "transaction_code": "16", "partner_id": self.person.id,
            "resident_country_code": "703", "tax_effect": -12000})
        item.write({"tax_effect": -12500})
        self.assertEqual(ordinary._l10n_sk_dppo_pdf_payload()["table_i"]["transactions"][0]["effect"], -12500)
        self.assertIn("/web/content/", ordinary.action_export_official_pdf()["url"])
        other = self.env["res.company"].create({"name": "Other synthetic company"})
        foreign = ret.sudo().copy({"company_id": other.id, "l10n_sk_table_i_ids": [(5, 0, 0)]})
        foreign_person = self.env["res.partner"].sudo().create({"name": "Other synthetic person", "company_id": other.id})
        self.env["l10n.sk.dppo.table.i.line"].sudo().create({
            "return_id": foreign.id, "transaction_code": "16", "partner_id": foreign_person.id,
            "resident_country_code": "703", "tax_effect": -1})
        with self.assertRaises(AccessError):
            foreign.l10n_sk_table_i_ids.with_user(user).read(["tax_effect"])
        with self.assertRaisesRegex(UserError, "must belong"):
            self.env["l10n.sk.dppo.table.i.line"].with_user(user).create({
                "return_id": ret.id, "company_id": other.id,
                "transaction_code": "16", "partner_id": self.person.id,
                "resident_country_code": "703"})

    def test_native_body_tables_identity_and_all_original_pages(self):
        ret = self._make()
        template, layout = self._assets()
        before = hashlib.sha256(template).hexdigest()
        data = ret._l10n_sk_dppo_pdf_payload()
        self.assertEqual(data["rows"]["a06"], 12.34)
        self.assertEqual(data["rows"]["a17"], 12.34)
        self.assertEqual(data["rows"]["b06"], 20)
        raw = ret._l10n_sk_dppo_official_pdf()
        reader = PdfReader(BytesIO(raw))
        self.assertEqual(len(reader.pages), 21)
        self.assertFalse(reader.get_fields())
        self.assertEqual(reader.metadata["/SourceSHA256"], before)
        self.assertEqual(reader.metadata["/Subject"], "2027-01-01 — 2027-12-31")
        for page in reader.pages:
            self.assertIn("2020317068", re.sub(r"\s+", "", page.extract_text()))
            self.assertFalse(page.get("/Annots"))
        self.assertIn("SKÚŠOBNÁ", re.sub(r"\s+", "", reader.pages[15].extract_text()))
        self.assertEqual(self._assets()[0], template)
        self.assertEqual(len(layout["line_fields"]), 101)
        self.assertEqual(ret.state, "preview")
        self.assertFalse(ret.xml_attachment_id)

    def test_download_idempotency_and_original_identity_snapshot(self):
        ret = self._make()
        first = ret.action_export_official_pdf()
        identifier = int(first["url"].split("/")[-1].split("?")[0])
        attachment = self.env["ir.attachment"].browse(identifier)
        original = attachment.raw
        self.assertEqual(ret.action_export_official_pdf(), first)
        self.company.name = "Iný názov"
        second = ret.action_export_official_pdf()
        self.assertNotEqual(first["url"], second["url"])
        self.assertEqual(attachment.raw, original)
        self.assertEqual(ret.state, "preview")

    def test_null_zero_negative_and_official_digit_capacity(self):
        ret = self._make()
        template, layout = self._assets()
        data = ret._l10n_sk_dppo_pdf_payload()
        data["rows"] = {"r100": -123.45, "r810": 0, "r1110": 9999999999.99}
        self.assertTrue(render_official_form(template, layout, data).startswith(b"%PDF"))
        data["rows"]["r1110"] = 10000000000
        with self.assertRaisesRegex(ValueError, "does not fit"):
            render_official_form(template, layout, data)
        data["rows"] = {"r100": None, "r810": 0}
        self.assertTrue(render_official_form(template, layout, data).startswith(b"%PDF"))
        data["rows"] = {"r100": float("nan")}
        with self.assertRaisesRegex(ValueError, "finite"):
            render_official_form(template, layout, data)

    def test_proportional_half_minimum_and_declaration_relation(self):
        ret = self._make()
        ret.write({"date_from": "2027-07-01", "l10n_sk_form_minimum_exemption": False,
                   "l10n_sk_form_half_minimum": True})
        self._set(ret, r100=0, r560=40000, r810=85)
        self.assertTrue(ret._l10n_sk_dppo_official_pdf())
        ret.l10n_sk_form_half_minimum = False
        with self.assertRaisesRegex(UserError, "declaration must agree"):
            ret._l10n_sk_dppo_official_pdf()

    def test_identity_dates_and_stale_inputs_refuse_without_attachment(self):
        ret = self._make()
        ret.l10n_sk_form_prepared_on = "2027-03-01"
        with self.assertRaisesRegex(UserError, "declaration date"):
            ret.action_export_official_pdf()
        ret.l10n_sk_form_prepared_on = "2028-03-01"
        ret.l10n_sk_form_legal_code = "ABC"
        with self.assertRaisesRegex(UserError, "three-digit"):
            ret.action_export_official_pdf()
        ret.l10n_sk_form_legal_code = "112"
        ret.line_ids.filtered(lambda line: line.code == "r310").write({
            "is_overridden": True, "manual_value": 5})
        with self.assertRaisesRegex(UserError, "Recompute"):
            ret.action_export_official_pdf()
        self.assertFalse(self.env["ir.attachment"].search([
            ("res_model", "=", ret._name), ("res_id", "=", ret.id),
            ("mimetype", "=", "application/pdf")]))

    def test_template_pin_and_supplementary_date(self):
        ret = self._make()
        template, layout = self._assets()
        with self.assertRaisesRegex(ValueError, "template changed"):
            render_official_form(template + b"changed", layout, ret._l10n_sk_dppo_pdf_payload())
        ret.statement_type_id = self.env.ref("l10n_sk_dppo.dppo_type_D_2026")
        with self.assertRaisesRegex(UserError, "discovery date"):
            ret.action_export_official_pdf()

    def test_ordinary_accountant_can_download_without_xml_or_manager(self):
        ret = self._make()
        accountant = new_test_user(self.env, login="dppo_pdf_accountant",
            groups="account.group_account_user", company_id=self.company.id,
            company_ids=[(6, 0, [self.company.id])])
        action = ret.with_user(accountant).action_export_official_pdf()
        identifier = int(action["url"].split("/")[-1].split("?")[0])
        attachment = self.env["ir.attachment"].with_user(accountant).browse(identifier)
        self.assertTrue(attachment.raw.startswith(b"%PDF"))
        self.assertEqual(ret.state, "preview")
