import base64
from lxml import etree
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestVehicleTax(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env['res.company'].create({'name': 'Synthetic vehicle tax & company',
            'country_id': cls.env.ref('base.sk').id, 'currency_id': cls.env.ref('base.EUR').id,
            'street': 'Hlavná 1141/11', 'city': 'Bratislava', 'zip': '85110',
            'l10n_sk_dic': '2020991234'})
        cls.Return = cls.env['l10n.sk.vehicle.tax.return'].with_company(cls.company).with_context(
            allowed_company_ids=[cls.company.id], lang='en_US')
        cls.Line = cls.env['l10n.sk.vehicle.tax.line'].with_company(cls.company).with_context(
            allowed_company_ids=[cls.company.id], lang='en_US')

    def make_return(self, **values):
        data = {'company_id': self.company.id, 'year': 2026,
            'declaration_date': '2027-01-10', 'scope_reviewed': True,
            'scope_evidence': 'Synthetic complete Slovak taxable fleet; ordinary PO calendar year.',
            'advances_paid': 0, 'advances_evidence': 'Reviewed synthetic zero actual advances.',
            'projected_tax': 177.60, 'projection_evidence': 'Reviewed fleet and adjusted annual rate at 1 January2027.',
            'representative_surname': 'Test', 'representative_firstname': 'Ján'}
        data.update(values)
        rec = self.Return.create(data)
        self.Line.create({'return_id': rec.id, 'registration_number': 'TEST001', 'category': 'M1',
            'first_registered': '2020-04-17', 'liability_from': '2020-04-01', 'propulsion': 'hybrid',
            'engine_cm3': 2000, 'facts_reviewed': True, 'evidence': 'Synthetic technical certificate and holder status §3a.'})
        return rec

    def xml(self, rec):
        rec.action_compute_lines()
        rec.action_export_xml()
        raw = base64.b64decode(rec.xml_attachment_id.datas)
        rec._validate_against_schema(raw)
        return etree.fromstring(raw)

    def filed(self, rec):
        self.xml(rec)
        rec.write({'submission_reference': 'SYNTHETIC-LOCAL-ONLY',
                   'filing_evidence': 'Synthetic test of retention; no actual authority submission.'})
        rec.action_submit()
        return rec.xml_attachment_id

    def test_official_fs_hybrid_example_exact_form_and_floor(self):
        rec = self.make_return()
        root = self.xml(rec)
        self.assertEqual(rec.result['tax'], '86.95')
        self.assertEqual(root.findtext('telo/r36'), '86.95')
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r21dan1'), '20.35')
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r21dan2'), '66.60')
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r14zvysenieSadzby1_10'), '1')
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r14zvysenieSadzby2_20'), '1')
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r20aPocMesS1'), '3')
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r20aPocMesS2'), '9')
        self.assertEqual(root.findtext('hlavicka/sidlo/ulica'), 'Hlavná')
        self.assertEqual(root.findtext('hlavicka/sidlo/cislo'), '1141/11')
        self.assertEqual(root.findtext('hlavicka/poObchodneMeno/riadok'), self.company.name)
        self.assertFalse(root.findtext('telo/strana3/stlpec2/r03Kategoria'))
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r19sadzba1'), '81.40')
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r19sadzba2'), '88.80')
        self.assertEqual(root.findtext('telo/r41'), '1')
        self.assertFalse(self.company.vat)  # DIČ is sufficient for a non-VAT entity.

    def test_electric_and_three_vehicles_use_two_pages(self):
        rec = self.make_return()
        self.Line.create({'return_id': rec.id, 'registration_number': 'ELECTRIC', 'category': 'N1',
            'first_registered': '2026-06-15', 'liability_from': '2026-06-01', 'propulsion': 'electric',
            'power_kw': 100, 'weight_kg': 3000, 'axles': 2, 'facts_reviewed': True, 'evidence': 'EV technical facts'})
        self.Line.create({'return_id': rec.id, 'registration_number': 'ORDINARY', 'category': 'M1',
            'first_registered': '2026-01-15', 'liability_from': '2026-01-01', 'propulsion': 'combustion',
            'engine_cm3': 2000, 'facts_reviewed': True, 'evidence': 'Petrol technical facts'})
        root = self.xml(rec)
        self.assertEqual(root.findtext('telo/r35'), '3')
        self.assertEqual(root.findtext('telo/r41'), '2')
        self.assertEqual(root.findtext('telo/r36'), '234.95')
        self.assertEqual(root.findtext('telo/strana3/stlpec2/r09Hmotnost'), '3.0')
        self.assertEqual(root.findtext('telo/strana3/stlpec2/r22'), '0.00')
        self.assertEqual([p.findtext('oznacenie/aktualna') for p in root.findall('telo/strana3')], ['1', '2'])
        rec.action_reset_unfiled()
        rec.line_ids.filtered(lambda line: line.propulsion != 'electric').unlink()
        root = self.xml(rec)
        self.assertEqual(root.findtext('telo/r35'), '1')
        self.assertEqual(root.findtext('telo/r36'), '0.00')  # EV alone still produces a return.

    def test_partial_year_and_future_end_not_falsely_emitted(self):
        rec = self.make_return()
        rec.line_ids.write({'first_registered': '2026-05-15', 'liability_from': '2026-06-01',
                             'liability_to': '2027-02-28', 'propulsion': 'combustion'})
        root = self.xml(rec)
        self.assertEqual(rec.result['tax'], '86.33')
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r02vzniku'), '01.06.2026')
        self.assertFalse(root.findtext('telo/strana3/stlpec1/r02zaniku'))

    def test_advances_overpayment_and_small_unpaid_difference(self):
        rec = self.make_return(advances_paid=100)
        root = self.xml(rec)
        self.assertEqual(root.findtext('telo/r39'), '13.05')
        self.assertEqual(rec.result['overpayment'], '13.05')
        self.assertEqual(root.findtext('telo/vrateniePreplatku/vratit'), '0')
        rec.action_reset_unfiled()
        rec.write({'advances_paid': 82})
        root = self.xml(rec)
        self.assertEqual(root.findtext('telo/r38'), '4.95')  # Published return still states the difference.
        self.assertEqual(rec.result['amount_to_pay'], '0.00')  # §10(15) payment threshold.

    def test_generated_create_defaults_and_direct_state_cannot_bypass(self):
        for key, value in [('result', {'tax': '0.00'}), ('source_proof', {}), ('xml_digest', 'forged')]:
            with self.assertRaises(UserError), self.cr.savepoint():
                self.make_return(**{key: value})
            with self.assertRaises(UserError), self.cr.savepoint():
                self.Return.with_context(**{'default_'+key: value}).create({'year': 2026})
        rec = self.make_return()
        for values in ({'state': 'preview'}, {'state': 'exported'}, {'state': 'submitted'}, {'result': {}}):
            with self.assertRaises(UserError), self.cr.savepoint():
                rec.write(values)

    def test_review_scope_duplicate_and_invalid_technical_facts_block(self):
        rec = self.make_return(scope_reviewed=False)
        with self.assertRaises(UserError):
            rec.action_compute_lines()
        rec.scope_reviewed = True
        rec.line_ids.write({'category': 'N1', 'axles': 0, 'weight_kg': 4000})
        with self.assertRaises(UserError):
            rec.action_compute_lines()
        rec.line_ids.write({'category': 'M1'})
        rec.line_ids.copy({'return_id': rec.id})
        with self.assertRaises(UserError):
            rec.action_compute_lines()

    def test_line_edit_and_parent_write_block_after_compute(self):
        rec = self.make_return()
        rec.action_compute_lines()
        for operation in (lambda: rec.write({'advances_paid': 10}),
                          lambda: rec.line_ids.write({'engine_cm3': 3000}),
                          lambda: rec.line_ids.unlink(),
                          lambda: rec.line_ids.copy({'return_id': rec.id})):
            with self.assertRaises(UserError), self.cr.savepoint():
                operation()
        rec.action_reset_to_draft()
        rec.line_ids.write({'engine_cm3': 3000})
        rec.action_compute_lines()
        self.assertNotEqual(rec.result['tax'], '86.95')

    def test_master_data_staleness_blocks_export_and_download(self):
        rec = self.make_return()
        self.xml(rec)
        self.company.city = 'Changed city'
        with self.assertRaises(UserError):
            rec.action_export_xml()
        with self.assertRaises(UserError):
            rec.xml_attachment_id._to_http_stream()
        rec.action_reset_unfiled()
        self.xml(rec)
        rec._check_xml()

    def test_export_retry_has_no_accounting_or_duplicate_lines(self):
        rec = self.make_return()
        before = self.env['account.move'].search_count([('company_id', '=', self.company.id)])
        root = self.xml(rec)
        digest = rec.xml_digest
        rec.action_export_xml()
        self.assertEqual(rec.xml_digest, digest)
        self.assertEqual(len(rec.line_ids), 1)
        self.assertEqual(self.env['account.move'].search_count([('company_id', '=', self.company.id)]), before)
        self.assertFalse(rec.result['actual_payment'])
        self.assertFalse(rec.result['actual_submission'])

    def test_filed_xml_retained_and_separate_full_corrective(self):
        rec = self.make_return()
        attachment = self.filed(rec)
        original = attachment.datas
        for operation in (lambda: rec.action_reset_unfiled(), lambda: rec.unlink(),
                          lambda: rec.action_compute_lines(), lambda: attachment.unlink(),
                          lambda: attachment.write({'datas': base64.b64encode(b'<forged/>')}),
                          lambda: rec.write({'filing_evidence': 'replacement'})):
            with self.assertRaises(UserError), self.cr.savepoint():
                operation()
        corrected = self.Return.browse(rec.action_create_amendment()['res_id'])
        corrected.line_ids.write({'engine_cm3': 3000})
        root = self.xml(corrected)
        self.assertEqual(root.findtext('hlavicka/typDP/odp'), '1')
        self.assertEqual(root.findtext('hlavicka/typDP/rdp'), '0')
        self.assertEqual(root.findtext('telo/r36'), corrected.result['tax'])
        self.assertEqual(attachment.datas, original)
        self.assertIn(attachment, rec.filed_history_ids)
        self.company.city = 'Later master data'
        rec._check_xml()  # Filed proof is a snapshot, not today's master data.

    def test_mark_filed_requires_confirmation_and_exact_xml(self):
        rec = self.make_return()
        self.xml(rec)
        with self.assertRaises(UserError):
            rec.action_submit()
        rec.write({'submission_reference': 'SYNTHETIC', 'filing_evidence': 'Synthetic receipt'})
        rec.action_submit()
        stamp, history = rec.submitted_date, rec.filed_history_ids
        rec.action_submit()
        self.assertEqual(rec.submitted_date, stamp)
        self.assertEqual(rec.filed_history_ids, history)

    def test_additional_not_approximated_and_wrong_company_rejected(self):
        rec = self.make_return(filing_type='additional')
        with self.assertRaises(UserError):
            rec.action_compute_lines()
        other = self.env['res.company'].create({'name': 'Other vehicle company'})
        with self.assertRaises(UserError), self.cr.savepoint():
            self.Line.with_context(default_return_id=rec.id, default_company_id=other.id).create({
                'registration_number': 'BAD', 'first_registered': '2025-01-01',
                'liability_from': '2025-01-01', 'evidence': 'Wrong company'})
        with self.assertRaises(UserError), self.cr.savepoint():
            rec.with_context(allowed_company_ids=[other.id]).action_compute_lines()

    def test_version_used_by_calculation_cannot_be_rewritten(self):
        rec = self.make_return()
        rec.action_compute_lines()
        with self.assertRaises(UserError):
            rec.version_id.write({'schedule': {}})

    def test_proof_independent_of_ui_language(self):
        rec = self.make_return()
        self.xml(rec)
        rec.with_context(lang='sk_SK')._check_xml()

    def additional(self, original):
        rec = self.Return.browse(original.action_create_additional()['res_id'])
        rec.write({'declaration_date': '2027-03-15', 'discovery_date': '2027-03-01',
                   'correction_evidence': 'Synthetic complete additional-return grounds and filing eligibility review.'})
        return rec

    def test_additional_full_return_signed_differences_and_unchanged_vehicle(self):
        original = self.make_return()
        original.line_ids.write({'propulsion': 'combustion'})
        self.Line.create({'return_id': original.id, 'registration_number': 'KEEP', 'category': 'M1',
            'first_registered': '2026-01-15', 'liability_from': '2026-01-01', 'propulsion': 'combustion',
            'engine_cm3': 2000, 'facts_reviewed': True, 'evidence': 'Unchanged synthetic vehicle'})
        filed = self.filed(original)
        raw = filed.datas
        rec = self.additional(original)
        rec.line_ids.sorted('id')[0].write({'propulsion': 'hybrid'})
        root = self.xml(rec)
        self.assertEqual(root.findtext('hlavicka/typDP/ddp'), '1')
        self.assertEqual(root.findtext('hlavicka/zdanovacieObdobie/datumDDP'), '01.03.2027')
        self.assertEqual(root.findtext('telo/r35'), '2')
        self.assertEqual(root.findtext('telo/r36'), '321.90')
        self.assertEqual(root.findtext('telo/r43'), '234.95')
        self.assertEqual(root.findtext('telo/r44'), '-86.95')
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r23'), '173.90')
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r24'), '86.95')
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r25'), '-86.95')
        self.assertEqual(root.findtext('telo/strana3/stlpec2/r25'), '0.00')
        self.assertEqual(rec.result['overpayment'], '86.95')
        self.assertEqual(filed.datas, raw)

    def test_second_additional_uses_latest_filed_and_preserves_advance_schedule(self):
        original = self.make_return(projected_tax=1000)
        self.filed(original)
        rec = self.additional(original)
        rec.line_ids.write({'propulsion': 'combustion'})
        rec.projected_tax = 500  # A corrected row40 does not retroactively change advance obligations.
        self.filed(rec)
        self.assertEqual(rec.result['next_year_advance_frequency'], 'quarterly')
        self.assertEqual(rec.result['next_year_advance_amount'], '250.00')
        next_rec = self.additional(rec)
        next_rec.line_ids.write({'propulsion': 'hybrid'})
        root = self.xml(next_rec)
        self.assertEqual(root.findtext('telo/r36'), '173.90')
        self.assertEqual(root.findtext('telo/r44'), '-86.95')
        stale = self.additional(original)
        with self.assertRaises(UserError):
            stale.action_compute_lines()

    def test_additional_cannot_omit_previous_vehicle_or_relabel_later_payment(self):
        original = self.make_return()
        self.filed(original)
        rec = self.additional(original)
        rec.line_ids.previous_line_id = False
        with self.assertRaises(UserError):
            rec.action_compute_lines()
        rec.line_ids.previous_line_id = original.line_ids
        rec.advances_paid = 10
        with self.assertRaises(UserError):
            rec.action_compute_lines()

    def test_corresponding_template_change_invalidates_unfiled_proof(self):
        rec = self.make_return()
        rec.action_compute_lines()
        view = self.env.ref('l10n_sk_vehicle_tax.template_dmv25_column')
        view.arch_db = view.arch_db.replace('<r12pism/>', '<r12pism>changed</r12pism>')
        with self.assertRaises(UserError):
            rec.action_export_xml()

    def test_additional_complete_removal_needs_review_and_zero_reconciles(self):
        original = self.make_return()
        self.filed(original)
        rec = self.additional(original)
        rec.line_ids.liability_to = '2025-12-31'
        with self.assertRaises(UserError):
            rec.action_compute_lines()
        rec.line_ids.write({'zero_liability_reviewed': True,
            'evidence': 'Synthetic reviewed sale to another holder before2026; original inclusion was erroneous.'})
        root = self.xml(rec)
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r23'), '86.95')
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r24'), '0.00')
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r25'), '-86.95')
        self.assertEqual(root.findtext('telo/r43'), '0.00')
        self.assertEqual(root.findtext('telo/r44'), '-86.95')
        self.assertEqual(rec.result['overpayment'], '86.95')

    def test_projection_suggestion_uses_january_annual_rate_and_requires_review(self):
        rec = self.make_return()
        rec.action_suggest_projected_tax()
        self.assertEqual(rec.projected_tax, 88.80)
        self.assertFalse(rec.projection_evidence)
        with self.assertRaises(UserError):
            rec.action_compute_lines()
        rec.projection_evidence = 'Reviewed full next January fleet; unchanged technical facts.'
        rec.line_ids.liability_to = '2026-12-31'
        rec.action_suggest_projected_tax()
        self.assertEqual(rec.projected_tax, 0)

    def test_refund_request_uses_company_iban_and_requires_actual_overpayment(self):
        rec = self.make_return(advances_paid=100)
        bank = self.env['res.partner.bank'].create({'partner_id': self.company.partner_id.id,
            'company_id': self.company.id, 'acc_number': 'SK3112000000198742637541'})
        rec.write({'refund_requested': True, 'refund_bank_id': bank.id,
            'refund_request_date': '2027-01-10', 'refund_evidence': 'Synthetic request reviewed; no actual repayment.'})
        root = self.xml(rec)
        self.assertEqual(root.findtext('telo/vrateniePreplatku/vratit'), '1')
        self.assertEqual(root.findtext('telo/vrateniePreplatku/sposobPlatby/ucet'), '1')
        self.assertEqual(root.findtext('telo/vrateniePreplatku/IBAN'), 'SK3112000000198742637541')
        self.filed(rec)
        correction = self.Return.browse(rec.action_create_amendment()['res_id'])
        self.assertFalse(correction.refund_requested)
        correction.advances_paid = 0
        correction.write({'refund_requested': True, 'refund_bank_id': bank.id,
            'refund_request_date': '2027-01-10', 'refund_evidence': 'Invalid request without overpayment'})
        with self.assertRaises(UserError):
            correction.action_compute_lines()

    def test_restricted_accountant_cannot_access_other_company(self):
        from odoo.tests.common import new_test_user
        from odoo.exceptions import AccessError
        rec = self.make_return()
        other = self.env['res.company'].create({'name': 'Other restricted company'})
        user = new_test_user(self.env, login='vehicle-accountant-test', groups='account.group_account_user',
            company_id=other.id, company_ids=[(6, 0, [other.id])])
        with self.assertRaises(AccessError):
            rec.with_user(user).with_context(allowed_company_ids=[other.id]).read(['result'])

    def test_accounting_manager_can_run_full_unfiled_workflow(self):
        from odoo.tests.common import new_test_user
        rec = self.make_return()
        user = new_test_user(self.env, login='vehicle-manager-test', groups='account.group_account_manager',
            company_id=self.company.id, company_ids=[(6, 0, [self.company.id])])
        scoped = rec.with_user(user)
        root = self.xml(scoped)
        self.assertEqual(root.findtext('telo/r36'), '86.95')
        scoped.action_reset_unfiled()
        scoped.line_ids.engine_cm3 = 3000
        scoped.action_compute_lines()
