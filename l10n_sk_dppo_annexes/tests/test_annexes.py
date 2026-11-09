import base64
from lxml import etree
from odoo import Command
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDppoAnnexes(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env['res.company'].create({'name': 'Synthetic DPPO annex company',
            'country_id': cls.env.ref('base.sk').id, 'currency_id': cls.env.ref('base.EUR').id,
            'vat': 'SK2023456787', 'street': 'Hlavná 11', 'city': 'Bratislava', 'zip': '85110'})
        cls.Return = cls.env['cssk.income.tax.return'].with_company(cls.company).with_context(
            allowed_company_ids=cls.company.ids, lang='en_US')

    def make_return(self):
        return self.Return.create({'company_id': self.company.id,
            'version_id': self.env.ref('l10n_sk_dppo.dppo_version_2025').id,
            'statement_type_id': self.env.ref('l10n_sk_dppo.dppo_type_R_2025').id,
            'date_from': '2027-01-01', 'date_to': '2027-12-31', 'l10n_sk_annexes_enabled': True,
            'l10n_sk_annexes_reviewed': True, 'l10n_sk_annexes_evidence': 'Synthetic full A/B workpaper review',
            'l10n_sk_annex_b_book': 3345, 'l10n_sk_annex_b_tax': 0, 'l10n_sk_annex_b_sale': 3000,
            'l10n_sk_annex_a_ids': [Command.create({'row_code': 'r16', 'amount': 10070,
                'evidence': 'Reviewed synthetic residual expense above deductible tax cost'})]})

    def test_tables_and_main_rows_export_without_inventing_other_annexes(self):
        rec = self.make_return()
        rec.action_compute_lines()
        values = {line.code: line.value for line in rec.line_ids}
        self.assertEqual(values['r130'], 10070)
        self.assertEqual(values['r150'], 345)
        self.assertEqual(values['r250'], 0)
        self.assertEqual(values['r200'], 10415)
        rec.invalidate_recordset()  # Check the real JSON roundtrip, not only Python's in-memory tuples.
        rec._check_annex_proof()
        rec.action_export_xml()
        raw = base64.b64decode(rec.xml_attachment_id.datas)
        rec._validate_against_schema(raw)
        root = etree.fromstring(raw)
        self.assertEqual(root.findtext('.//tabA/r16'), '10070.00')
        self.assertEqual(root.findtext('.//tabA/r17'), '10070.00')
        self.assertEqual(root.findtext('.//tabB/r02'), '0.00')
        self.assertEqual(root.findtext('.//tabB/r05'), '3000.00')
        self.assertEqual(root.findtext('.//tabB/r06'), '3000.00')
        self.assertFalse(root.findtext('.//tabC1/r01'))

    def test_changed_annex_and_main_row_are_stale(self):
        rec = self.make_return()
        rec.action_compute_lines()
        rec.l10n_sk_annex_a_ids.amount = 10000
        with self.assertRaises(UserError):
            rec.action_export_xml()
        rec.action_compute_lines()
        rec.line_ids.filtered(lambda line: line.code == 'r130').value = 1
        with self.assertRaises(UserError):
            rec.action_export_xml()

    def test_generated_defaults_and_wrong_company_refused(self):
        with self.assertRaises(UserError):
            self.Return.with_context(default_l10n_sk_annex_proof={}).create({})
        rec = self.make_return()
        other = self.env['res.company'].create({'name': 'Other annex company'})
        with self.assertRaises(UserError), self.cr.savepoint():
            self.env['l10n.sk.dppo.annex.a.line'].with_context(default_return_id=rec.id,
                default_company_id=other.id).create({'row_code': 'r16', 'amount': 10, 'evidence': 'Wrong company'})

    def test_formula_b_and_deduction_direction(self):
        rec = self.make_return()
        rec.write({'l10n_sk_annex_b_tax': 6000, 'l10n_sk_annex_b_rent': 1000,
            'l10n_sk_annex_b_suspended': 500, 'l10n_sk_annex_b_sale': 0})
        rec.action_compute_lines()
        values = {line.code: line.value for line in rec.line_ids}
        self.assertEqual(values['r150'], 0)
        self.assertEqual(values['r250'], 1155)

    def test_exported_inputs_and_submitted_copy_retained(self):
        rec = self.make_return()
        rec.action_compute_lines()
        rec.action_export_xml()
        attachment = rec.xml_attachment_id
        original = attachment.datas
        with self.assertRaises(UserError):
            rec.l10n_sk_annex_a_ids.amount = 2
        rec.action_submit()
        self.assertIn(str(attachment.id), rec.l10n_sk_annex_filed_proofs)
        with self.assertRaises(UserError):
            attachment.write({'datas': base64.b64encode(b'<changed/>')})
        self.assertEqual(attachment.datas, original)
        rec.action_reset_to_draft()
        with self.assertRaises(UserError):
            rec.unlink()

    def test_late_posted_ledger_change_requires_recalculation(self):
        rec = self.make_return()
        rec.action_compute_lines()
        journal = self.env['account.journal'].create({'company_id': self.company.id,
            'name': 'Synthetic late entry', 'code': 'ALAT', 'type': 'general'})
        accounts = [self.env['account.account'].create({'name': name, 'code': code,
            'account_type': kind, 'company_ids': [Command.set(self.company.ids)]}) for name, code, kind in (
                ('Synthetic bank', '221999', 'asset_cash'), ('Synthetic income', '648999', 'income'))]
        move = self.env['account.move'].create({'journal_id': journal.id, 'company_id': self.company.id,
            'date': '2027-12-31', 'line_ids': [Command.create({'account_id': accounts[0].id, 'debit': 100}),
                Command.create({'account_id': accounts[1].id, 'credit': 100})]})
        move.action_post()
        with self.assertRaises(UserError):
            rec.action_export_xml()
        rec.action_compute_lines()
        self.assertEqual(rec.line_ids.filtered(lambda line: line.code == 'r100').value, 100)
        other = self.env['res.company'].create({'name': 'Another active company'})
        # account.account.code is company-dependent in Odoo 19. A download
        # must use the return company even if another company is primary.
        rec.with_company(other)._check_annex_proof()

    def test_accounting_manager_can_export_without_sudo(self):
        from odoo.tests.common import new_test_user
        rec = self.make_return()
        user = new_test_user(self.env, login='annex-manager-test', groups='account.group_account_manager',
            company_id=self.company.id, company_ids=[Command.set(self.company.ids)])
        rec = rec.with_user(user)
        rec.action_compute_lines()
        rec.action_export_xml()
        self.assertTrue(rec.xml_attachment_id)

    def test_retained_evidence_cannot_be_disabled_or_reassigned(self):
        rec = self.make_return()
        rec.action_compute_lines()
        with self.assertRaises(UserError):
            rec.l10n_sk_annexes_enabled = False
        rec.action_export_xml()
        with self.assertRaises(UserError):
            rec.date_to = '2027-06-30'

    def test_recompute_replaces_previous_generated_override_but_not_user_conflict(self):
        rec = self.make_return()
        rec.action_compute_lines()
        rec.l10n_sk_annex_a_ids.amount = 9000
        rec.action_compute_lines()
        line = rec.line_ids.filtered(lambda row: row.code == 'r130')
        self.assertEqual(line.value, 9000)
        self.assertTrue(line.is_overridden)
        line.write({'manual_value': 7000, 'value': 7000})
        with self.assertRaises(UserError):
            rec.action_compute_lines()

    def test_filing_state_does_not_bypass_current_source_check(self):
        rec = self.make_return()
        rec.action_compute_lines()
        rec.company_id.city = 'Changed after calculation'
        rec.state = 'submitted'
        with self.assertRaises(UserError):
            rec._check_annex_proof()
