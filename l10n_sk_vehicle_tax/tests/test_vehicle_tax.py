import base64
from lxml import etree
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestVehicleTax(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, lang='en_US'))
        cls.company = cls.env['res.company'].create({'name': 'Synthetic vehicle tax & company',
            'country_id': cls.env.ref('base.sk').id, 'currency_id': cls.env.ref('base.EUR').id,
            'street': 'Hlavná 1141/11', 'city': 'Bratislava', 'zip': '85110',
            'l10n_sk_dic': '2020991234'})
        cls.Return = cls.env['l10n.sk.vehicle.tax.return'].with_company(cls.company).with_context(
            allowed_company_ids=[cls.company.id], lang='en_US')
        cls.Line = cls.env['l10n.sk.vehicle.tax.line'].with_company(cls.company).with_context(
            allowed_company_ids=[cls.company.id], lang='en_US')
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Synthetic tax brand'})
        cls.fleet_model = cls.env['fleet.vehicle.model'].create({'name': 'Synthetic tax model', 'brand_id': brand.id})

    def _fleet_values(self, values):
        names = {'registration_number': 'license_plate', 'category': 'l10n_sk_eu_category',
            'first_registered': 'l10n_sk_first_registration_date', 'liability_from': 'l10n_sk_liability_from_override',
            'liability_to': 'write_off_date', 'engine_cm3': 'l10n_sk_engine_cm3',
            'power_kw': 'power', 'weight_kg': 'l10n_sk_max_mass_kg', 'axles': 'l10n_sk_axles',
            'taxpayer': 'l10n_sk_dmv_taxpayer'}
        result = {names[key]: value for key, value in values.items() if key in names}
        if 'liability_from' in values:
            result['l10n_sk_liability_override_reason'] = 'Reviewed synthetic section 8 holding/use evidence.'
        if 'propulsion' in values:
            result['fuel_type'] = {'hybrid': 'full_hybrid', 'combustion': 'gasoline'}.get(
                values['propulsion'], values['propulsion'])
            result['l10n_sk_hybrid_documented'] = values['propulsion'] == 'hybrid'
        return result

    def add_vehicle(self, values):
        rec = self.Return.browse(values['return_id'])
        vehicle = self.env['fleet.vehicle'].create({'company_id': rec.company_id.id,
            'model_id': self.fleet_model.id, 'l10n_sk_registered_in_sk': True,
            **self._fleet_values(values)})
        source = vehicle._l10n_sk_vehicle_tax_facts()
        return self.Line.create({**{key: value for key, value in values.items() if key not in source},
                                'vehicle_id': vehicle.id})

    def change_vehicle(self, lines, values):
        # Source administration is separate from the accountant's filing role.
        for line in lines:
            line.vehicle_id.with_env(self.env).write(self._fleet_values(values))
        lines.action_refresh_vehicle()
        lines.write({'facts_reviewed': True})

    def make_return(self, **values):
        data = {'company_id': self.company.id, 'year': 2026,
            'declaration_date': '2027-01-10', 'scope_reviewed': True,
            'scope_evidence': 'Synthetic complete Slovak taxable fleet; ordinary PO calendar year.',
            'advances_paid': 0, 'advances_evidence': 'Reviewed synthetic zero actual advances.',
            'projected_tax': 177.60, 'projection_evidence': 'Reviewed fleet and adjusted annual rate at 1 January2027.',
            'representative_surname': 'Test', 'representative_firstname': 'Ján'}
        data.update(values)
        rec = self.Return.create(data)
        self.add_vehicle({'return_id': rec.id, 'registration_number': 'TEST001', 'category': 'M1',
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
        self.add_vehicle({'return_id': rec.id, 'registration_number': 'ELECTRIC', 'category': 'N1',
            'first_registered': '2026-06-15', 'liability_from': '2026-06-01', 'propulsion': 'electric',
            'power_kw': 100, 'weight_kg': 3000, 'axles': 2, 'facts_reviewed': True, 'evidence': 'EV technical facts'})
        self.add_vehicle({'return_id': rec.id, 'registration_number': 'ORDINARY', 'category': 'M1',
            'first_registered': '2026-01-15', 'liability_from': '2026-01-01', 'propulsion': 'combustion',
            'engine_cm3': 2000, 'facts_reviewed': True, 'evidence': 'Petrol technical facts'})
        root = self.xml(rec)
        self.assertEqual(root.findtext('telo/r35'), '3')
        self.assertEqual(root.findtext('telo/r41'), '2')
        self.assertEqual(root.findtext('telo/r36'), '234.95')
        self.assertEqual(root.findtext('telo/strana3/stlpec2/r09Hmotnost'), '3')
        self.assertEqual(root.findtext('telo/strana3/stlpec2/r22'), '0.00')
        self.assertEqual([p.findtext('oznacenie/aktualna') for p in root.findall('telo/strana3')], ['1', '2'])
        rec.action_reset_unfiled()
        rec.line_ids.filtered(lambda line: line.propulsion != 'electric').unlink()
        root = self.xml(rec)
        self.assertEqual(root.findtext('telo/r35'), '1')
        self.assertEqual(root.findtext('telo/r36'), '0.00')  # EV alone still produces a return.

    def test_partial_year_and_future_end_not_falsely_emitted(self):
        rec = self.make_return()
        self.change_vehicle(rec.line_ids, {'first_registered': '2026-05-15', 'liability_from': '2026-06-01',
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
        self.change_vehicle(rec.line_ids, {'category': 'N1', 'axles': 0, 'weight_kg': 4000})
        with self.assertRaises(UserError):
            rec.action_compute_lines()
        self.change_vehicle(rec.line_ids, {'category': 'M1'})
        rec.line_ids.copy({'return_id': rec.id})
        with self.assertRaises(UserError):
            rec.action_compute_lines()

    def test_line_edit_and_parent_write_block_after_compute(self):
        rec = self.make_return()
        rec.action_compute_lines()
        for operation in (lambda: rec.write({'advances_paid': 10}),
                          lambda: self.change_vehicle(rec.line_ids, {'engine_cm3': 3000}),
                          lambda: rec.line_ids.unlink(),
                          lambda: rec.line_ids.copy({'return_id': rec.id})):
            with self.assertRaises(UserError), self.cr.savepoint():
                operation()
        rec.action_reset_to_draft()
        self.change_vehicle(rec.line_ids, {'engine_cm3': 3000})
        rec.action_compute_lines()
        self.assertNotEqual(rec.result['tax'], '86.95')

    def test_stale_export_is_blocked_but_existing_snapshot_remains_readable(self):
        rec = self.make_return()
        self.xml(rec)
        exported = rec.xml_attachment_id.raw
        self.company.city = 'Changed city'
        with self.assertRaises(UserError):
            rec.action_export_xml()
        # Existing XML is a readable snapshot. A fresh export or recording
        # a filing still requires current inputs; archive access does not.
        from types import SimpleNamespace
        from unittest.mock import patch
        # Native filestore streaming needs the HTTP request's database;
        # financial inputs and attachment behavior remain real.
        with patch('odoo.addons.base.models.ir_attachment.request', SimpleNamespace(db=self.cr.dbname)):
            self.assertTrue(rec.xml_attachment_id._to_http_stream())
        self.assertEqual(rec.xml_attachment_id.raw, exported)
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
        self.assertNotEqual(corrected.name, rec.name)
        self.assertIn(self.company.name, corrected.name)
        self.change_vehicle(corrected.line_ids, {'engine_cm3': 3000})
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
        self.change_vehicle(original.line_ids, {'propulsion': 'combustion'})
        self.add_vehicle({'return_id': original.id, 'registration_number': 'KEEP', 'category': 'M1',
            'first_registered': '2026-01-15', 'liability_from': '2026-01-01', 'propulsion': 'combustion',
            'engine_cm3': 2000, 'facts_reviewed': True, 'evidence': 'Unchanged synthetic vehicle'})
        filed = self.filed(original)
        raw = filed.datas
        rec = self.additional(original)
        self.change_vehicle(rec.line_ids.sorted('id')[0], {'propulsion': 'hybrid'})
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
        self.change_vehicle(rec.line_ids, {'propulsion': 'combustion'})
        rec.projected_tax = 500  # A corrected row40 does not retroactively change advance obligations.
        self.filed(rec)
        self.assertEqual(rec.result['next_year_advance_frequency'], 'quarterly')
        self.assertEqual(rec.result['next_year_advance_amount'], '250.00')
        next_rec = self.additional(rec)
        self.change_vehicle(next_rec.line_ids, {'propulsion': 'hybrid'})
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
        self.change_vehicle(rec.line_ids, {'liability_to': '2025-12-31'})
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
        self.change_vehicle(rec.line_ids, {'liability_to': '2026-12-31'})
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
        self.change_vehicle(scoped.line_ids, {'engine_cm3': 3000})
        scoped.action_compute_lines()

    def test_accountant_can_file_but_cannot_configure_statutory_edition(self):
        from odoo.tests.common import new_test_user
        from odoo.exceptions import AccessError
        rec = self.make_return()
        user = new_test_user(self.env, login='vehicle-full-accountant', groups='account.group_account_user',
            company_id=self.company.id, company_ids=[(6, 0, self.company.ids)])
        rec = rec.with_user(user)
        self.filed(rec)
        self.assertEqual(rec.state, 'submitted')
        with self.assertRaises(AccessError):
            rec.version_id.write({'schedule': {}})

    def test_duplicate_regular_filing_refused_and_original_retry_is_idempotent(self):
        first, second = self.make_return(), self.make_return()
        self.filed(first)
        self.xml(second)
        second.write({'submission_reference': 'SYNTHETIC duplicate', 'filing_evidence': 'Synthetic receipt'})
        with self.assertRaisesRegex(UserError, '^A regular vehicle tax return is already filed'):
            second.action_submit()
        self.assertEqual(second.state, 'exported')
        history = first.filed_history_ids
        first.action_submit()
        self.assertEqual(first.filed_history_ids, history)

    def test_event_dates_normalized_and_full_year_month_count_exported(self):
        rec = self.make_return()
        self.change_vehicle(rec.line_ids, {'first_registered': '2026-01-15',
            'liability_from': '2026-01-15', 'liability_to': '2026-03-15', 'propulsion': 'combustion'})
        root = self.xml(rec)
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r02vzniku'), '01.01.2026')
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r02zaniku'), '31.03.2026')
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r20aPocMesS1'), '3')
        self.assertEqual(rec.tax_total, 37)
        rec.action_reset_unfiled()
        self.change_vehicle(rec.line_ids, {'liability_to': False})
        root = self.xml(rec)
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r20aPocMesS1'), '12')
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r07-ObjemValcov'), '2000')
        self.assertFalse(root.findtext('telo/strana3/stlpec1/r08-VykonMotora'))

    def test_fleet_action_includes_inactive_sold_vehicle_without_trip_log(self):
        rec = self.make_return()
        vehicle = rec.line_ids.vehicle_id
        rec.line_ids.unlink()
        vehicle.write({'active': False, 'write_off_date': '2026-03-15'})
        rec.action_add_fleet_vehicles()
        rec.action_add_fleet_vehicles()
        self.assertEqual(rec.line_ids.vehicle_id, vehicle)
        self.assertEqual(len(rec.line_ids), 1)
        self.assertFalse(rec.line_ids.facts_reviewed)
        rec.line_ids.facts_reviewed = True
        self.xml(rec)
        self.assertEqual(sum(part['month_count'] for part in rec.result['vehicles'][0]['segments']), 3)

    def test_changed_fleet_requires_explicit_refresh_and_preserves_filed_snapshot(self):
        rec = self.make_return()
        self.xml(rec)
        vehicle = rec.line_ids.vehicle_id
        vehicle.l10n_sk_engine_cm3 = 3000
        with self.assertRaises(UserError):
            rec.action_export_xml()
        rec.action_reset_unfiled()
        with self.assertRaisesRegex(UserError, '^The fleet source changed'):
            rec.action_compute_lines()
        rec.line_ids.action_refresh_vehicle()
        self.assertFalse(rec.line_ids.facts_reviewed)
        rec.line_ids.facts_reviewed = True
        raw = self.filed(rec).datas
        vehicle.l10n_sk_engine_cm3 = 3500
        self.assertEqual(rec._check_xml().datas, raw)

    def test_snapshot_cannot_be_injected_or_reassigned_via_defaults(self):
        rec = self.make_return()
        with self.assertRaises(UserError):
            rec.line_ids.vehicle_source = {}
        with self.assertRaises(UserError):
            self.Line.with_context(default_vehicle_source={}).create({'return_id': rec.id})
        with self.assertRaises(UserError):
            rec.line_ids.write({'vehicle_id': rec.line_ids.vehicle_id.id})

    def test_xml_storage_migration_and_unrelated_attachment_metadata(self):
        rec = self.make_return()
        attachment = self.filed(rec)
        original = attachment.raw
        attachment.write({'raw': original})
        attachment.generate_access_token()
        self.env['ir.config_parameter'].sudo().set_param('ir_attachment.location', 'db')
        attachment._migrate()
        attachment.invalidate_recordset()
        self.assertEqual(attachment.raw, original)
        self.assertFalse(attachment.store_fname)
        self.env['ir.config_parameter'].sudo().set_param('ir_attachment.location', 'file')
        attachment._migrate()
        self.assertEqual(attachment.raw, original)
        with self.assertRaises(UserError):
            attachment.write({'raw': b'<changed/>'})
        pdf = self.env['ir.attachment'].create({'name': 'Unrelated workpaper', 'datas': base64.b64encode(b'workpaper'),
            'res_model': rec._name, 'res_id': rec.id})
        pdf.generate_access_token()
        pdf.write({'raw': b'revised unrelated workpaper'})

    def test_l3e_category_and_n1_band_edges_have_exact_form_rows(self):
        rec = self.make_return()
        self.change_vehicle(rec.line_ids, {'category': 'L3e', 'engine_cm3': 125,
            'propulsion': 'combustion', 'first_registered': '2026-01-01', 'liability_from': '2026-01-01'})
        root = self.xml(rec)
        self.assertEqual(root.findtext('telo/strana3/stlpec1/r03Kategoria'), 'L3e')
        self.assertEqual(rec.tax_total, 50)
        for mass, expected in ((1000, 74), (1001, 133), (2000, 133), (2001, 212), (3500, 212)):
            with self.subTest(mass=mass):
                rec.action_reset_unfiled()
                self.change_vehicle(rec.line_ids, {'category': 'N1', 'weight_kg': mass, 'axles': 2})
                root = self.xml(rec)
                self.assertEqual(rec.tax_total, expected)
                self.assertFalse(root.findtext('telo/strana3/stlpec1/r07-ObjemValcov'))
                self.assertEqual(root.findtext('telo/strana3/stlpec1/r10PocetNaprav'), '2')
        rec.action_reset_unfiled()
        self.change_vehicle(rec.line_ids, {'weight_kg': 3501})
        with self.assertRaises(UserError):
            rec.action_compute_lines()

    def test_propulsion_reductions_are_documented_and_lpg_not_reduced(self):
        rec = self.make_return()
        for fuel, expected in (('cng', 86.95), ('lng', 86.95), ('hydrogen', 86.95), ('lpg', 173.90)):
            with self.subTest(fuel=fuel):
                self.change_vehicle(rec.line_ids, {'propulsion': fuel})
                root = self.xml(rec)
                self.assertEqual(rec.tax_total, expected)
                self.assertEqual(root.findtext('telo/strana3/stlpec1/r16plyn'), str(int(fuel in ('cng', 'lng'))))
                self.assertEqual(root.findtext('telo/strana3/stlpec1/r16vodik'), str(int(fuel == 'hydrogen')))
                rec.action_reset_unfiled()

    def test_payment_thresholds_and_computed_money_fields(self):
        rec = self.make_return(advances_paid=100)
        rec.action_compute_lines()
        self.assertEqual((rec.tax_total, rec.amount_to_pay, rec.overpayment), (86.95, 0, 13.05))
        for projected, frequency in ((700, 'none'), (700.01, 'quarterly'), (8300, 'quarterly'), (8300.01, 'monthly')):
            rec.action_reset_unfiled()
            rec.projected_tax = projected
            rec.action_compute_lines()
            self.assertEqual(rec.result['next_year_advance_frequency'], frequency)

    def test_deadline_weekend_and_wrong_correction_side(self):
        from ..models.vehicle_tax import ordinary_deadline
        from datetime import date
        self.assertEqual(ordinary_deadline(2026), date(2027, 2, 1))
        rec = self.make_return()
        self.filed(rec)
        correction = self.Return.browse(rec.action_create_amendment()['res_id'])
        correction.declaration_date = '2027-02-02'
        with self.assertRaises(UserError):
            correction.action_compute_lines()
        additional = self.additional(rec)
        additional.write({'declaration_date': '2027-02-01', 'discovery_date': '2027-02-01'})
        with self.assertRaises(UserError):
            additional.action_compute_lines()

    def test_modified_schema_edition_is_refused(self):
        rec = self.make_return()
        edition = rec.version_id.copy({'name': 'SYNTHETIC altered schema',
            'xml_schema_data': base64.b64encode(b'<altered/>')})
        rec.version_id = edition
        with self.assertRaises(UserError):
            rec.action_compute_lines()

    def test_statutory_capacity_edges_and_old_age_steps(self):
        from datetime import date
        from ..models.calculation import calculate_vehicle
        rec = self.make_return()
        def tax(cm3, first=date(2026, 1, 1)):
            return calculate_vehicle(year=2026, category='M1', first_registered=first,
                liability_from=date(2026, 1, 1), liability_to=None, propulsion='combustion',
                engine_cm3=cm3, power_kw=0, weight_kg=0, schedule=rec.version_id.schedule)
        for cm3, expected in ((150, '50.00'), (151, '62.00'), (900, '62.00'),
                (901, '80.00'), (3000, '180.00'), (3001, '218.00')):
            self.assertEqual(tax(cm3)['tax'], expected)
        for first, expected in ((date(2015, 1, 1), '192.40'),
                (date(2013, 1, 1), '207.20'), (date(2010, 1, 1), '222.00')):
            self.assertEqual(tax(2000, first)['tax'], expected)
        result = tax(1500, date(2014, 7, 1))
        self.assertEqual(result['tax'], '155.25')
        self.assertEqual([part['tax'] for part in result['segments']], ['74.75', '80.50'])

    def test_outside_scope_and_unreviewed_electric_facts_refused(self):
        rec = self.make_return()
        vehicle = rec.line_ids.vehicle_id
        vehicle.l10n_sk_dmv_taxpayer = 'e'
        with self.assertRaises(UserError):
            rec.line_ids.action_refresh_vehicle()
        vehicle.write({'l10n_sk_dmv_taxpayer': 'a', 'fuel_type': 'electric', 'power': 0})
        with self.assertRaises(UserError):
            rec.line_ids.action_refresh_vehicle()
        vehicle.write({'power': 100, 'power_unit': 'horsepower'})
        with self.assertRaises(UserError):
            rec.line_ids.action_refresh_vehicle()

    def test_schema_bytes_match_pin_and_no_schema_is_unpinned(self):
        import hashlib
        from pathlib import Path
        from odoo.modules.module import get_module_path
        data = Path(get_module_path('l10n_sk_vehicle_tax')) / 'data'
        fields = (data / 'SCHEMA_VERSION').read_text().splitlines()[0].split()
        name, md5, size = fields
        raw = (data / name).read_bytes()
        self.assertEqual(hashlib.md5(raw).hexdigest(), md5,
            'Schema bytes changed: preserve original CRLF when transferring patches and review SCHEMA_VERSION.')
        self.assertEqual(len(raw), int(size))
        self.assertEqual({path.name for path in data.glob('*.xsd')}, {name})

    def test_concurrent_regular_filing_also_has_database_uniqueness(self):
        from psycopg2 import IntegrityError
        from odoo.tools import mute_logger
        first, second = self.make_return(), self.make_return()
        self.filed(first)
        self.xml(second)
        self.env.flush_all()
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError), self.cr.savepoint():
            # Simulate a competing worker past its Python pre-check. The
            # partial unique index must still reject a second filed original.
            self.cr.execute("UPDATE l10n_sk_vehicle_tax_return SET state='submitted' WHERE id=%s", [second.id])

    def test_default_acquisition_date_cannot_shorten_long_held_liability(self):
        rec = self.make_return()
        rec.line_ids.unlink()
        self.env['fleet.vehicle'].search([('company_id', '=', self.company.id)]).unlink()
        # Deliberately omit acquisition_date, as in the native fleet UI.
        vehicle = self.env['fleet.vehicle'].create({'company_id': self.company.id,
            'model_id': self.fleet_model.id, 'license_plate': 'LONGHELD',
            'l10n_sk_registered_in_sk': True, 'l10n_sk_eu_category': 'M1',
            'l10n_sk_first_registration_date': '2018-01-15',
            'l10n_sk_engine_cm3': 2000, 'fuel_type': 'gasoline'})
        self.assertTrue(vehicle.acquisition_date)
        with self.assertRaisesRegex(UserError, 'reviewed business use / holding start'):
            vehicle._l10n_sk_vehicle_tax_facts()
        vehicle.write({'l10n_sk_liability_from_override': '2018-01-15',
                       'l10n_sk_liability_override_reason': 'Company register: held since 2018.'})
        rec.action_add_fleet_vehicles()
        self.assertEqual(rec.line_ids.vehicle_id, vehicle)
        rec.line_ids.facts_reviewed = True
        self.xml(rec)
        self.assertEqual(rec.tax_total, 177.60)
        self.assertEqual(sum(s['month_count'] for s in rec.result['vehicles'][0]['segments']), 12)

    def test_import_lists_every_unprepared_vehicle_and_imports_ready(self):
        rec = self.make_return()
        ready = rec.line_ids.vehicle_id
        rec.line_ids.unlink()
        variants = [
            ('MISSING', {'l10n_sk_first_registration_date': False}),
            ('NOSTART', {'l10n_sk_liability_from_override': False}),
            ('NOREASON', {'l10n_sk_liability_override_reason': ' '}),
            ('FUTURE', {'l10n_sk_liability_from_override': '2027-02-01'}),
            ('POOL', {'l10n_sk_dmv_taxpayer': 'e'}),
            ('EXEMPT', {'l10n_sk_tax_exempt': True, 'l10n_sk_not_taxable_reason': 'Reviewed exemption'}),
            ('NOEVIDENCE', {'l10n_sk_tax_exempt': True, 'l10n_sk_not_taxable_reason': False}),
            ('NOCOMPANY', {'company_id': False}),
            ('HEAVY', {'l10n_sk_eu_category': 'N3'}),
            ('NOCAPACITY', {'l10n_sk_engine_cm3': 0}),
        ]
        for plate, values in variants:
            ready.copy({'license_plate': plate, **values})
        action = rec.action_add_fleet_vehicles()
        self.assertEqual(rec.line_ids.vehicle_id, ready)
        message = action['params']['message']
        for plate, _values in variants:
            self.assertIn(plate + ':', message)
        self.assertIn('No company assigned', message)
        self.assertIn('exemption evidence missing', message)
        rec.action_add_fleet_vehicles()
        self.assertEqual(len(rec.line_ids), 1)

    def test_lng_model_default_survives_model_change(self):
        model = self.fleet_model.copy({'default_fuel_type': 'lng'})
        vehicle = self.env['fleet.vehicle'].create({'model_id': self.fleet_model.id})
        vehicle.model_id = model
        self.assertEqual(vehicle.fuel_type, 'lng')

    def test_historical_fleet_import_ignores_later_native_registration_date(self):
        rec = self.make_return()
        vehicle = rec.line_ids.vehicle_id
        rec.line_ids.unlink()
        vehicle.acquisition_date = '2027-02-01'
        rec.action_add_fleet_vehicles()
        self.assertEqual(rec.line_ids.vehicle_id, vehicle)
        self.assertEqual(str(rec.line_ids.liability_from), '2020-04-01')

    def test_import_propagates_fleet_and_schedule_access_errors(self):
        from unittest.mock import patch

        rec = self.make_return()
        vehicle = rec.line_ids.vehicle_id
        rec.line_ids.unlink()
        # AccessError inherits UserError in Odoo19. It is never an ordinary
        # missing-facts skip, even when raised inside the readiness check.
        with patch.object(type(vehicle), '_l10n_sk_vehicle_tax_facts',
                          side_effect=AccessError('Synthetic fleet source access denied')):
            with self.assertRaisesRegex(AccessError, 'fleet source access denied'):
                rec.action_add_fleet_vehicles()
        self.assertFalse(rec.line_ids)
        version = rec.version_id
        version.invalidate_recordset(['schedule'])
        with patch.object(type(version), '_fetch_field',
                          side_effect=AccessError('Synthetic schedule access denied')):
            with self.assertRaisesRegex(AccessError, 'schedule access denied'):
                rec.action_add_fleet_vehicles()
        self.assertFalse(rec.line_ids)
