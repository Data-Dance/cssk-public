from types import SimpleNamespace
from unittest.mock import patch

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.addons.l10n_sk_dppo.tests.test_dppo_tables import TestDppoTables, TestDppoTablesFromRegister


@tagged('post_install', '-at_install')
class TestDppoAnnexes(TestDppoTables):
    def workpaper(self, suffix='2025', year=2025):
        rec = self._return(suffix, year)
        rec.write({'l10n_sk_annexes_enabled': True, 'l10n_sk_annexes_reviewed': True,
            'l10n_sk_annexes_evidence': 'Synthetic reviewed itemised expenses',
            'l10n_sk_annex_a_ids': [Command.create({'row_code': 'a06', 'amount': 1000,
                'evidence': 'Synthetic non-deductible expense'})]})
        rec.action_compute_lines()
        return rec

    def test_itemised_native_rows_and_xml_for_supported_versions(self):
        for suffix, year in [('2013', 2013), ('2022', 2022), ('2024', 2024), ('2025', 2025)]:
            rec = self.workpaper(suffix, year)
            self.assertEqual(self._v(rec, 'a06'), 1000)
            self.assertEqual(self._v(rec, 'r130'), 1000)
            root = self._export(rec)
            self.assertEqual(root.findtext('.//tabA/r06'), '1000.00')
            self.assertFalse(root.findtext('.//tabB/r01'))
            self.assertTrue(rec.l10n_sk_annex_a_ids.row_caption)

    def test_native_amendment_changes_a_and_releases_generated_rows(self):
        original = self.workpaper()
        original.action_export_xml()
        attachment = original.xml_attachment_id
        raw = attachment.raw
        original.action_submit()
        amendment = self.env[original._name].browse(original.action_create_amendment()['res_id'])
        self.assertFalse(amendment.l10n_sk_annexes_reviewed)
        self.assertFalse(amendment.l10n_sk_annexes_evidence)
        self.assertEqual(amendment.l10n_sk_annex_a_ids.amount, 1000)
        with self.assertRaises(UserError):
            amendment.action_compute_lines()
        amendment.write({'l10n_sk_annexes_reviewed': True,
            'l10n_sk_annexes_evidence': 'Independent amendment review'})
        amendment.l10n_sk_annex_a_ids.amount = 1500
        amendment.action_compute_lines()
        self.assertEqual(self._v(amendment, 'r130'), 1500)
        amendment.l10n_sk_annexes_enabled = False
        amendment.action_compute_lines()
        self.assertEqual(self._v(amendment, 'a06'), 0)
        self.assertEqual(self._v(amendment, 'r130'), 0)
        self.assertEqual(attachment.raw, raw)
        self.assertEqual(self._v(original, 'r130'), 1000)

    def test_removed_item_does_not_leave_an_old_override(self):
        rec = self.workpaper()
        rec.l10n_sk_annex_a_ids.unlink()
        with self.assertRaises(UserError):
            rec.action_export_xml()
        rec.action_compute_lines()
        self.assertEqual(self._v(rec, 'r130'), 0)
        self.assertFalse(rec.line_ids.filtered(lambda row: row.code == 'a06').is_overridden)

    def test_unrelated_native_a_and_b_manual_rows_are_retained(self):
        rec = self.workpaper()
        self._set(rec, a01=75, b01=3345, b05=3000)
        self.assertEqual(self._v(rec, 'r130'), 1075)
        self.assertEqual(self._v(rec, 'r150'), 345)
        rec.l10n_sk_annexes_enabled = False
        rec.action_compute_lines()
        self.assertEqual(self._v(rec, 'r130'), 75)
        self.assertEqual(self._v(rec, 'r150'), 345)

    def test_chatter_attachment_and_exported_bytes_remain_accessible(self):
        rec = self.workpaper()
        rec.action_export_xml()
        attachment = rec.xml_attachment_id
        raw = attachment.raw
        self.company.city = 'Changed address'
        self.assertEqual(attachment.raw, raw)
        with patch('odoo.addons.base.models.ir_attachment.request',
                SimpleNamespace(db=self.cr.dbname)):
            attachment._to_http_stream()
        pdf = self.env['ir.attachment'].create({'name': 'Workpaper.pdf', 'raw': b'%PDF-1.4',
            'res_model': rec._name, 'res_id': rec.id})
        self.assertTrue(pdf.generate_access_token())
        pdf.write({'raw': b'%PDF-1.5'})

    def test_old_form_rejects_a16_total_as_an_expense_row(self):
        rec = self.workpaper('2013', 2013)
        rec.l10n_sk_annex_a_ids.row_code = 'a16'
        with self.assertRaises(UserError):
            rec.action_compute_lines()


@tagged('post_install', '-at_install')
class TestAnnexWithAssetRegister(TestDppoTablesFromRegister):
    def test_a_only_workpaper_preserves_native_asset_difference(self):
        self._asset(self._profile('022995'), 'Synthetic tangible asset')
        version = self.env.ref('l10n_sk_dppo.dppo_version_2025')
        rec = self.env['cssk.income.tax.return'].create({'company_id': self.company.id,
            'version_id': version.id,
            'statement_type_id': self.env.ref('l10n_sk_dppo.dppo_type_R_2025').id,
            'date_from': '2025-01-01', 'date_to': '2025-12-31'})
        rec.action_compute_lines()
        before = {line.code: line.value for line in rec.line_ids if line.code in ('r150', 'r250', 'b01', 'b02', 'b04', 'b05')}
        self.assertGreater(before['r250'], 0)
        rec.write({'l10n_sk_annexes_enabled': True, 'l10n_sk_annexes_reviewed': True,
            'l10n_sk_annexes_evidence': 'Table A only, register remains the depreciation source',
            'l10n_sk_annex_a_ids': [Command.create({'row_code': 'a06', 'amount': 100,
                'evidence': 'Synthetic non-deductible expense'})]})
        rec.action_compute_lines()
        self.assertEqual({line.code: line.value for line in rec.line_ids if line.code in before}, before)
        self.assertEqual(rec.line_ids.filtered(lambda row: row.code == 'r130').value, 100)
