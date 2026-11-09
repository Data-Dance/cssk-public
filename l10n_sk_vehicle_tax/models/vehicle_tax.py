# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Vehicle tax uses the common statutory export/retention pipeline.

Technical facts are a filing workpaper, not another asset/accounting ledger.
This first form edition supports ordinary calendar-year Slovak legal entities
and L/M1/N1 monthly liability. Unsupported exemptions/special periods are
explicitly excluded, never approximated as an ordinary vehicle.
"""
import base64
import hashlib
import json
import re
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal
from lxml import etree

from odoo import _, api, fields, models, Command
from odoo.exceptions import UserError
from odoo.tools import file_open
from odoo.tools.translate import LazyTranslate
from odoo.addons.l10n_cssk_core.tools import split_street

from .calculation import calculate_vehicle, cents, settle_return, validate_schedule

_lt = LazyTranslate(__name__)
SCHEMA_HASH = 'd1b154eb027c5d70ed4afaeef85add1612a74674960cfd4665be1cd476502b57'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


def dated(value):
    return value.strftime('%d.%m.%Y') if value else ''


def ordinary_deadline(year):
    value = date(year+1, 1, 31)
    while value.weekday() > 4:
        value += timedelta(days=1)
    return value  # No Slovak public holiday falls on 31 January / 1–2 February.


def default_schedule():
    with file_open('l10n_sk_vehicle_tax/data/schedule2025.json', 'r') as stream:
        return json.load(stream)


def template_digest(view):
    # Technical view source is administrator-only in Odoo19. Read only the
    # configured template metadata with sudo, never filing/company records.
    # Combined architecture also captures inherited template amendments.
    architecture = view.sudo().with_context(lang='en_US')._get_combined_arch()
    return hashlib.sha256(etree.tostring(architecture)).hexdigest()


class VehicleTaxVersion(models.Model):
    _name = 'l10n.sk.vehicle.tax.version'
    _description = 'Slovak vehicle tax form edition'
    _order = 'date_from desc, id desc'

    name = fields.Char(required=True)
    date_from = fields.Date(required=True)
    date_to = fields.Date()
    schedule = fields.Json(required=True, default=lambda self: default_schedule())
    xml_template_ref_id = fields.Many2one('ir.ui.view', required=True, ondelete='restrict')
    xml_root_element = fields.Char(required=True, default='dokument')
    xml_schema_data = fields.Binary(required=True, attachment=False)
    source_url = fields.Char(required=True)

    def write(self, values):
        self.check_access('write')
        if self:
            self.env.cr.execute('SELECT id FROM l10n_sk_vehicle_tax_version WHERE id IN %s ORDER BY id FOR UPDATE',
                                [tuple(self.ids)])
        if self.env['l10n.sk.vehicle.tax.return'].search_count([
                ('version_id', 'in', self.ids), ('state', '!=', 'draft')]):
            raise UserError(_('A calculated vehicle tax return retains this form edition. Create a new edition instead.'))
        return super().write(values)


class VehicleTaxReturn(models.Model):
    _name = 'l10n.sk.vehicle.tax.return'
    _inherit = ['mail.thread', 'cssk.statutory.submission.mixin']
    _description = 'Slovak motor vehicle tax return'
    _check_company_auto = True
    _order = 'year desc, id desc'
    _cssk_form_label = _lt('motor vehicle tax return')
    _cssk_xml_name_fallback = 'DMVv25'
    _one_regular_filing = models.UniqueIndex(
        "(company_id, year) WHERE filing_type = 'regular' AND state = 'submitted'",
        "A regular vehicle tax return is already filed for this company and year. Prepare a correction of that filing.")

    name = fields.Char(compute='_compute_name', store=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company,
                                  ondelete='restrict')
    currency_id = fields.Many2one(related='company_id.currency_id')
    year = fields.Integer(required=True, default=lambda self: fields.Date.context_today(self).year-1)
    date_from = fields.Date(compute='_compute_dates', store=True)
    date_to = fields.Date(compute='_compute_dates', store=True)
    version_id = fields.Many2one('l10n.sk.vehicle.tax.version', required=True,
                                default=lambda self: self.env.ref('l10n_sk_vehicle_tax.version_dmv25'))
    state = fields.Selection([('draft', 'Draft'), ('preview', 'Calculated'),
        ('exported', 'Exported'), ('submitted', 'Marked filed'), ('legacy', 'Historical filing')],
        default='draft', required=True, readonly=True, copy=False, tracking=True)
    filing_type = fields.Selection([('regular', 'Regular'), ('corrective', 'Corrective'),
        ('additional', 'Additional')], required=True, default='regular')
    original_return_id = fields.Many2one('l10n.sk.vehicle.tax.return', check_company=True,
                                         ondelete='restrict', copy=False)
    discovery_date = fields.Date()
    correction_evidence = fields.Text(string='Review of correction grounds and filing eligibility', copy=False)
    declaration_date = fields.Date(required=True, default=fields.Date.context_today)
    scope_reviewed = fields.Boolean(string='Ordinary calendar-year Slovak legal entity reviewed')
    scope_evidence = fields.Text(string='Fleet completeness, registration and taxpayer review')
    advances_paid = fields.Monetary(string='Actually paid advances')
    advances_evidence = fields.Text(string='Evidence of paid advances or reviewed zero')
    projected_tax = fields.Monetary(string='Projected tax at next 1 January',
        help='Reviewed annual adjusted rates for the vehicles taxable at next 1 January; not the prior-year tax.')
    projection_evidence = fields.Text(string='Next January fleet and annual rates review')
    refund_requested = fields.Boolean(string='Request repayment of the overpayment', copy=False)
    refund_bank_id = fields.Many2one('res.partner.bank', string='Company IBAN for repayment', check_company=True, copy=False)
    refund_request_date = fields.Date(copy=False)
    refund_evidence = fields.Text(string='Review of overpayment repayment request', copy=False)
    representative_surname = fields.Char()
    representative_firstname = fields.Char()
    representative_title = fields.Char()
    representative_capacity = fields.Selection([('statutory', 'Statutory representative')],
                                               default='statutory', required=True)
    notes = fields.Text()
    line_ids = fields.One2many('l10n.sk.vehicle.tax.line', 'return_id', copy=True)
    result = fields.Json(readonly=True, copy=False)
    source_proof = fields.Json(readonly=True, copy=False)
    tax_total = fields.Monetary(compute='_compute_totals')
    amount_to_pay = fields.Monetary(compute='_compute_totals')
    overpayment = fields.Monetary(compute='_compute_totals')
    xml_attachment_id = fields.Many2one('ir.attachment', readonly=True, copy=False, ondelete='restrict')
    xml_digest = fields.Char(readonly=True, copy=False)
    filing_evidence = fields.Text(copy=False, help='Actual filing confirmation; export alone does not prove delivery.')

    _generated = {'name', 'date_from', 'date_to', 'result', 'source_proof', 'xml_attachment_id',
        'xml_digest', 'submitted_attachment_id', 'filed_history_ids', 'submitted_date', 'legacy',
        'legacy_source', 'legacy_stated_codes', 'legacy_reference'}
    _inputs = {'company_id', 'year', 'version_id', 'filing_type', 'original_return_id',
        'discovery_date', 'correction_evidence', 'declaration_date', 'scope_reviewed', 'scope_evidence', 'advances_paid',
        'advances_evidence', 'projected_tax', 'projection_evidence', 'representative_surname',
        'representative_firstname', 'representative_title', 'representative_capacity', 'notes', 'line_ids',
        'refund_requested', 'refund_bank_id', 'refund_request_date', 'refund_evidence'}

    @api.depends('year', 'company_id', 'filing_type')
    def _compute_name(self):
        for rec in self:
            rec.name = 'DMVv25-%s-%s-%s-%s' % (rec.company_id.name, rec.year, rec.filing_type, rec.id)

    @api.depends('year')
    def _compute_dates(self):
        for rec in self:
            rec.date_from = date(rec.year, 1, 1) if 2025 <= rec.year <= 9998 else False
            rec.date_to = date(rec.year, 12, 31) if 2025 <= rec.year <= 9998 else False

    @api.constrains('year')
    def _check_year(self):
        if any(not 2025 <= rec.year <= 9998 for rec in self):
            raise UserError(_('This vehicle tax form requires a calendar year from 2025 to 9998.'))

    @api.depends('result')
    def _compute_totals(self):
        for rec in self:
            rec.tax_total = float((rec.result or {}).get('tax', 0))
            rec.amount_to_pay = float((rec.result or {}).get('amount_to_pay', 0))
            rec.overpayment = float((rec.result or {}).get('overpayment', 0))

    def _lock(self):
        if not self:
            return
        self.check_access('write')
        if any(rec.company_id.id not in self.env.companies.ids for rec in self):
            raise UserError(_('Select the vehicle tax return company before this operation.'))
        self.env.cr.execute('SELECT id FROM l10n_sk_vehicle_tax_return WHERE id IN %s ORDER BY id FOR UPDATE',
                            [tuple(self.ids)])
        self.invalidate_recordset()

    @api.model_create_multi
    def create(self, values_list):
        for values in values_list:
            if (self._generated & values.keys() or any('default_'+key in self.env.context for key in self._generated)
                    or values.get('state', 'draft') != 'draft'
                    or self.env.context.get('default_state', 'draft') != 'draft'):
                raise UserError(_('Vehicle tax results and filing archives are generated by the filing workflow.'))
        records = super().create(values_list)
        if any(rec.company_id.id not in self.env.companies.ids for rec in records):
            raise UserError(_('Select the vehicle tax return company before this operation.'))
        return records

    def write(self, values):
        if self._generated & values.keys():
            raise UserError(_('Vehicle tax results and filing archives are generated by the filing workflow.'))
        if {'filing_evidence', 'submission_reference'} & values.keys() and any(rec.state == 'submitted' for rec in self):
            raise UserError(_('The recorded vehicle tax filing confirmation is retained with its filed copy.'))
        if self._inputs & values.keys():
            self._lock()
            if 'company_id' in values and values['company_id'] not in self.env.companies.ids:
                raise UserError(_('Select the vehicle tax return company before this operation.'))
            if any(rec.state != 'draft' for rec in self):
                raise UserError(_('Reset the unfiled return to draft before changing vehicle tax facts.'))
        if 'state' in values:
            # The shared export pipeline changes state through write(). Its
            # transition is valid only with an exact, current validated export.
            if values['state'] != 'exported' or set(values) != {'state'}:
                raise UserError(_('Use the vehicle tax workflow actions to change the filing state.'))
            for rec in self:
                rec._check_xml()
                if rec.state not in ('preview', 'exported'):
                    raise UserError(_('Calculate the unfiled return before exporting.'))
        return super().write(values)

    def unlink(self):
        self._lock()
        if any(rec.filed_history_ids or rec.state == 'submitted' for rec in self):
            raise UserError(_('A retained vehicle tax filing cannot be deleted.'))
        return super().unlink()

    def _preflight(self):
        self.ensure_one()
        company = self.company_id
        if (company.country_id.code != 'SK' or company.currency_id.name != 'EUR'
                or not company.partner_id.is_company or not self.scope_reviewed or not self.scope_evidence):
            raise UserError(_('Review an ordinary Slovak legal-entity calendar-year return in EUR and the complete taxable fleet.'))
        if not (re.fullmatch(r'[0-9]{10}', company.l10n_sk_dic or '')
                and company.name and company.street and company.zip and company.city):
            raise UserError(_('Complete the company DIČ and registered address before calculating vehicle tax.'))
        if (not self.representative_surname or not self.representative_firstname
                or not self.advances_evidence or not self.projection_evidence):
            raise UserError(_('Review the representative, actual advances and next January projected tax, including zero amounts.'))
        if self.refund_requested:
            bank = self.refund_bank_id
            if (not bank or bank.partner_id != company.partner_id or bank.acc_type != 'iban'
                    or (bank.company_id and bank.company_id != company) or not self.refund_evidence
                    or not self.refund_request_date or self.refund_request_date > self.declaration_date):
                raise UserError(_('Review the overpayment request date, evidence and a valid IBAN belonging to the filing company.'))
        version = self.version_id
        if (version.date_from > self.date_from or (version.date_to and version.date_to < self.date_to)
                or version.xml_root_element != 'dokument'
                or hashlib.sha256(base64.b64decode(version.xml_schema_data or b'')).hexdigest() != SCHEMA_HASH):
            raise UserError(_('Select the reviewed DMVv25 edition and its original official XML schema for this year.'))
        previous = self.original_return_id
        if self.filing_type == 'regular' and previous:
            raise UserError(_('A regular return cannot replace another filing. Select the corrective filing type.'))
        if self.filing_type in ('corrective', 'additional'):
            if (not previous or previous == self or previous.company_id != company or previous.year != self.year
                    or previous.state != 'submitted'
                    or not previous.submitted_attachment_id or previous.submitted_attachment_id not in previous.filed_history_ids):
                raise UserError(_('Choose the retained filed return for the same company and year before preparing a correction.'))
            latest = self.search([('company_id', '=', company.id), ('year', '=', self.year),
                ('state', '=', 'submitted')], order='submitted_date desc, id desc', limit=1)
            if previous != latest:
                raise UserError(_('Base the correction on the latest retained filing for this company and year.'))
            previous._check_xml()
            if self.filing_type == 'corrective' and (previous.filing_type == 'additional'
                    or self.declaration_date > ordinary_deadline(self.year)):
                raise UserError(_('After the ordinary filing deadline use an additional return with the discovery date.'))
            if self.filing_type == 'additional':
                if (not self.discovery_date or not self.correction_evidence
                        or self.discovery_date > self.declaration_date
                        or self.declaration_date <= ordinary_deadline(self.year)):
                    raise UserError(_('Review the additional return discovery date, filing date and legal eligibility after the ordinary deadline.'))
                if cents(self.advances_paid) != cents(previous.advances_paid):
                    raise UserError(_('An additional return retains the original paid advances; later tax payments are not new advances.'))
                previous_ids = [line.previous_line_id.id for line in self.line_ids if line.previous_line_id]
                if (len(previous_ids) != len(set(previous_ids)) or set(previous_ids) != set(previous.line_ids.ids)):
                    raise UserError(_('Reconcile every previously filed vehicle exactly once in the additional full return.'))
                if any(line.previous_line_id and line.previous_line_id.return_id != previous for line in self.line_ids):
                    raise UserError(_('A vehicle difference must refer to the selected previous filed return.'))
        if not self.line_ids:
            raise UserError(_('Add the reviewed taxable vehicles, including electric vehicles with zero tax.'))
        plates = [re.sub(r'\s+', '', line.registration_number).upper() for line in self.line_ids]
        if len(plates) != len(set(plates)):
            raise UserError(_('Review duplicate vehicle registrations. Multiple liability intervals require an explicit reconciliation.'))
        if self.filing_type != 'additional' and self.line_ids.filtered('previous_line_id'):
            raise UserError(_('Previous vehicle difference links belong only to an additional return.'))
        try:
            validate_schedule(version.schedule, self.year)
            cents(self.advances_paid)
            cents(self.projected_tax)
        except (ValueError, TypeError, KeyError) as error:
            raise UserError(self._calculation_error(error)) from error

    def _calculation_error(self, error):
        # The pure financial engine deliberately has no Odoo dependency.
        # Literal extraction here keeps its user-facing failures translatable.
        messages = {
            'A tax measurement or amount cannot be a boolean.': _('A tax measurement or amount cannot be a boolean.'),
            'Supply a valid tax measurement or amount.': _('Supply a valid tax measurement or amount.'),
            'Tax measurements and amounts must be finite and nonnegative.': _('Tax measurements and amounts must be finite and nonnegative.'),
            'Supply monetary amounts in whole eurocents.': _('Supply monetary amounts in whole eurocents.'),
            'Supply the statutory bands for this vehicle.': _('Supply the statutory bands for this vehicle.'),
            'Invalid statutory rate band.': _('Invalid statutory rate band.'),
            'An unbounded statutory band must be last.': _('An unbounded statutory band must be last.'),
            'Statutory band ceilings must increase.': _('Statutory band ceilings must increase.'),
            'The measurement exceeds the reviewed statutory bands.': _('The measurement exceeds the reviewed statutory bands.'),
            'Supply the complete dated vehicle-tax schedule.': _('Supply the complete dated vehicle-tax schedule.'),
            'This statutory schedule does not cover the entire tax year.': _('This statutory schedule does not cover the entire tax year.'),
            'Review the dated payment and advance thresholds.': _('Review the dated payment and advance thresholds.'),
            'Invalid statutory ecological reduction.': _('Invalid statutory ecological reduction.'),
            'Supply a valid calendar tax year.': _('Supply a valid calendar tax year.'),
            'Review an L, M1 or N1 vehicle and its documented propulsion.': _('Review an L, M1 or N1 vehicle and its documented propulsion.'),
            'Use the first and last calendar days of the reviewed liability months.': _('Use the first and last calendar days of the reviewed liability months.'),
            'Liability dates must reconcile with first registration and their order.': _('Liability dates must reconcile with first registration and their order.'),
            'This vehicle has no reviewed taxable month in the return year.': _('This vehicle has no reviewed taxable month in the return year.'),
            'An electric vehicle requires its documented motor power.': _('An electric vehicle requires its documented motor power.'),
            'An L or M1 combustion/hybrid vehicle requires documented cylinder capacity.': _('An L or M1 combustion/hybrid vehicle requires documented cylinder capacity.'),
            'An N1 vehicle requires its documented maximum permissible mass.': _('An N1 vehicle requires its documented maximum permissible mass.'),
            'Review the statutory vehicle-age increase.': _('Review the statutory vehicle-age increase.'),
        }
        return messages.get(str(error), _('Review the dated vehicle tax rate edition and technical facts.'))

    def _source(self):
        self.ensure_one()
        self = self.with_context(lang='en_US')  # Proof identity is independent of the reader's UI language.
        company, version = self.company_id, self.version_id
        template = version.xml_template_ref_id
        return {'company': company.id, 'year': self.year,
            'company_facts': {'name': company.name, 'dic': company.l10n_sk_dic,
                'street': company.street, 'street2': company.street2 or '',
                'split_street': list(split_street(company)), 'zip': company.zip,
                'city': company.city, 'country': company.country_id.name,
                'country_code': company.country_id.code, 'currency': company.currency_id.name,
                'legal_entity': company.partner_id.is_company},
            'inputs': {key: (getattr(self, key).id if key.endswith('_id') else
                fields.Date.to_string(getattr(self, key)) if key in ('discovery_date', 'declaration_date', 'refund_request_date')
                else getattr(self, key)) for key in sorted(self._inputs - {'line_ids', 'year', 'company_id', 'version_id'})},
            'edition': {'id': version.id, 'from': str(version.date_from), 'to': str(version.date_to),
                'schema': hashlib.sha256(base64.b64decode(version.xml_schema_data)).hexdigest(),
                'schedule': version.schedule, 'template': template.id,
                'template_hash': template_digest(template),
                'column_hash': template_digest(self.env.ref('l10n_sk_vehicle_tax.template_dmv25_column'))},
            'vehicles': [line._facts() for line in self.line_ids.sorted('id')],
            'previous_filing': {'id': self.original_return_id.id,
                'xml_digest': self.original_return_id.xml_digest,
                'result_digest': digest(self.original_return_id.result)} if self.original_return_id else None,
            'refund_account': {'id': self.refund_bank_id.id, 'partner': self.refund_bank_id.partner_id.id,
                'company': self.refund_bank_id.company_id.id, 'type': self.refund_bank_id.acc_type,
                'iban': self.refund_bank_id.sanitized_acc_number} if self.refund_requested else None}

    def action_compute_lines(self):
        with self.env.cr.savepoint():
            for rec in self:
                rec._lock()
                if rec.state == 'submitted':
                    raise UserError(_('A filed return is immutable. Create a correction.'))
                self.env.cr.execute('SELECT id FROM l10n_sk_vehicle_tax_version WHERE id = %s FOR SHARE',
                                    [rec.version_id.id])
                rec._preflight()
                results = []
                for line in rec.line_ids.sorted('id'):
                    results.append(line._calculate())
                total = sum((Decimal(value['tax']) for value in results), Decimal(0))
                result = settle_return(total, rec.advances_paid, rec.projected_tax, rec.version_id.schedule)
                if rec.filing_type == 'additional':
                    previous = rec.original_return_id
                    previous_by_line = dict(zip(previous.line_ids.sorted('id').ids, previous.result['vehicles']))
                    for line, vehicle in zip(rec.line_ids.sorted('id'), results):
                        previous_tax = Decimal(previous_by_line[line.previous_line_id.id]['tax']) if line.previous_line_id else Decimal(0)
                        vehicle.update(previous_tax=f'{previous_tax:.2f}',
                            difference=f'{Decimal(vehicle["tax"])-previous_tax:.2f}')
                    difference = total-Decimal(previous.result['tax'])
                    result.update(previous_tax=previous.result['tax'], tax_difference=f'{difference:.2f}',
                        amount_to_pay=f'{difference if difference > Decimal(str(rec.version_id.schedule["payment_threshold"])) else Decimal(0):.2f}',
                        overpayment=f'{max(-difference, Decimal(0)):.2f}', advance_schedule_unchanged=True,
                        next_year_advance_frequency=previous.result['next_year_advance_frequency'],
                        next_year_advance_amount=previous.result['next_year_advance_amount'])
                result.update(vehicles=results, actual_submission=False, actual_payment=False)
                if rec.refund_requested and Decimal(result['overpayment']) <= 0:
                    raise UserError(_('An overpayment repayment request requires a positive calculated overpayment.'))
                source = rec._source()
                proof = {'policy': 'sk-dmv25-v1', 'source': source, 'result_digest': digest(result),
                         'source_digest': digest(source)}
                super(VehicleTaxReturn, rec).write({'result': result, 'source_proof': proof,
                    'state': 'preview', 'xml_attachment_id': False, 'xml_digest': False})
        return True

    def _check_proof(self):
        self.ensure_one()
        proof = self.source_proof or {}
        if (not self.result or proof.get('policy') != 'sk-dmv25-v1'
                or digest(proof.get('source')) != proof.get('source_digest')
                or digest(self.result) != proof.get('result_digest')
                or proof['source']['company'] != self.company_id.id or proof['source']['year'] != self.year):
            raise UserError(_('Recalculate the vehicle tax return to retain its source evidence.'))
        if self.state != 'submitted':
            self._preflight()
            if proof['source'] != self._source():
                raise UserError(_('The vehicle tax facts changed after calculation. Reset and recalculate the unfiled return.'))
        return proof

    def _cssk_preflight_export(self):
        # DzMV identifies the filer by DIČ. VAT registration is not required.
        self._check_proof()
        return True

    def _cssk_render_context(self):
        context = super()._cssk_render_context()
        self._check_proof()
        facts = self.source_proof['source']
        company, inputs = facts['company_facts'], facts['inputs']
        columns = []
        for vehicle in self.result['vehicles']:
            technical = vehicle['facts']
            start = fields.Date.to_date(technical['liability_from'])
            end = fields.Date.to_date(technical['liability_to'])
            start = start.replace(day=1)
            end = end.replace(day=monthrange(end.year, end.month)[1]) if end else None
            electric = technical['propulsion'] == 'electric'
            value = {'r01': dated(fields.Date.to_date(technical['first_registered'])),
                'r02vzniku': dated(start) if start.year == self.year else '',
                'r02zaniku': dated(end) if end and end.year == self.year else '',
                'r03Kategoria': technical['category'], 'r06-EVC': technical['registration_number'],
                'r07-ObjemValcov': str(int(technical['engine_cm3'])) if not electric and technical['category'] != 'N1' else '',
                'r08-VykonMotora': str(technical['power_kw']) if electric else '',
                'r09Hmotnost': str(Decimal(str(technical['weight_kg']))/1000) if technical['category'] == 'N1' else '',
                'r10PocetNaprav': str(technical['axles']) if technical['category'] == 'N1' else '',
                'r11pism': technical['taxpayer'], 'r13sadzba': str(int(Decimal(vehicle['annual_base']))),
                'r16hybrid': int(technical['propulsion'] == 'hybrid'),
                'r16plyn': int(technical['propulsion'] in ('cng', 'lng')),
                'r16vodik': int(technical['propulsion'] == 'hydrogen'), 'r22': vehicle['tax']}
            for index, segment in enumerate(vehicle['segments'], 1):
                value.update({f'r15rocnaSadzba_{index}': segment['annual_after_age'],
                    f'r17sadzba{index}': segment['annual_final'],
                    f'r19sadzba{index}': segment['annual_final'],
                    f'r20aPocMesS{index}': segment['month_count'],
                    f'r21dan{index}': segment['tax']})
                # MF/017488/2024-726: without combined-transport relief,
                # r19 repeats r17; blank is not a faithful completed form.
                for percent in (10, 20, 30, 40, 50):
                    value[f'r14zvysenieSadzby{index}_{percent}'] = int(Decimal(segment['increase_percent']) == percent)
            if self.filing_type == 'additional':
                value.update(r23=vehicle['previous_tax'], r24=vehicle['tax'], r25=vehicle['difference'])
            columns.append(value)
        pages = [(columns[index:index+2]+[{}])[:2] for index in range(0, len(columns), 2)]
        difference = Decimal(self.result['tax_difference'])
        data = {
            'company': company, 'inputs': inputs, 'regular': int(self.filing_type == 'regular'),
            'corrective': int(self.filing_type == 'corrective'), 'year': self.year,
            'additional': int(self.filing_type == 'additional'),
            'discovery_date': dated(self.discovery_date) if self.filing_type == 'additional' else '',
            'date_from': dated(self.date_from), 'date_to': dated(self.date_to),
            'declaration_date': dated(self.declaration_date), 'vehicle_count': len(columns),
            'page_count': len(pages), 'tax': self.result['tax'],
            'advances': self.result['paid_advances'], 'due_row': f'{max(difference, Decimal(0)):.2f}',
            'refund_row': self.result['overpayment'], 'projected': self.result['projected_next_year'],
            'previous_count': '', 'previous_tax': '', 'additional_difference': '', 'original_page_count': len(pages),
            'refund_requested': int(self.refund_requested),
            'refund_iban': facts['refund_account']['iban'] if self.refund_requested else '',
            'refund_date': dated(self.refund_request_date) if self.refund_requested else ''}
        if self.filing_type == 'additional':
            previous = self.original_return_id
            original_difference = Decimal(previous.result['tax'])-Decimal(previous.result['paid_advances'])
            data.update(previous_count=len(previous.line_ids), previous_tax=previous.result['tax'],
                additional_difference=self.result['tax_difference'], original_page_count='',
                due_row=f'{max(original_difference, Decimal(0)):.2f}',
                refund_row=f'{max(-original_difference, Decimal(0)):.2f}')
        context.update(d=data, pages=pages)
        return context

    def action_export_xml(self):
        with self.env.cr.savepoint():
            self._lock()
            self.env.cr.execute('SELECT id FROM l10n_sk_vehicle_tax_version WHERE id = %s FOR SHARE',
                                [self.version_id.id])
            return super().action_export_xml()

    def _attach_xml(self, xml_bytes):
        self.ensure_one()
        attachment = self.env['ir.attachment'].create({'name': self.name+'.xml',
            'datas': base64.b64encode(xml_bytes), 'mimetype': 'application/xml',
            'res_model': self._name, 'res_id': self.id, 'company_id': self.company_id.id})
        super(VehicleTaxReturn, self).write({'xml_attachment_id': attachment.id,
                                           'xml_digest': hashlib.sha256(xml_bytes).hexdigest()})

    def _check_xml(self):
        self._check_proof()
        attachment = self.xml_attachment_id
        if (not attachment or attachment.res_model != self._name or attachment.res_id != self.id
                or attachment.company_id != self.company_id
                or hashlib.sha256(base64.b64decode(attachment.datas or b'')).hexdigest() != self.xml_digest):
            raise UserError(_('Export the current validated vehicle tax XML before using this attachment.'))
        return attachment

    def action_submit(self):
        # Same shared retention fields, one atomic write for protected metadata.
        # This records an explicitly evidenced filing; it performs no transport.
        with self.env.cr.savepoint():
            self._lock()
            for rec in self:
                self.env.cr.execute('SELECT id FROM res_company WHERE id = %s FOR UPDATE', [rec.company_id.id])
                if rec.state == 'submitted':
                    rec._check_xml()
                    continue
                if rec.filing_type == 'regular' and self.search_count([
                        ('company_id', '=', rec.company_id.id), ('year', '=', rec.year),
                        ('filing_type', '=', 'regular'), ('state', '=', 'submitted'), ('id', '!=', rec.id)]):
                    raise UserError(_('A regular vehicle tax return is already filed for this company and year. Prepare a correction of that filing.'))
                if rec.state != 'exported' or not rec.submission_reference or not rec.filing_evidence:
                    raise UserError(_('Export first and record the actual filing confirmation and evidence.'))
                attachment = rec._check_xml()
                super(VehicleTaxReturn, rec).write({'submitted_attachment_id': attachment.id,
                    'filed_history_ids': [Command.link(attachment.id)], 'submitted_date': fields.Datetime.now(),
                    'state': 'submitted'})
                rec.message_post(body=_('Recorded filing confirmation. The exact vehicle tax XML is retained.'))
        return True

    def action_reset_to_draft(self):
        return self.action_reset_unfiled()

    def action_reset_unfiled(self):
        self._lock()
        if any(rec.state == 'submitted' or rec.filed_history_ids for rec in self):
            raise UserError(_('A filed vehicle tax return is immutable. Create a separate corrective return.'))
        super(VehicleTaxReturn, self).write({'state': 'draft', 'result': False, 'source_proof': False,
                                            'xml_attachment_id': False, 'xml_digest': False})
        return True

    def action_create_amendment(self):
        self.ensure_one()
        self._lock()
        if self.state != 'submitted':
            raise UserError(_('Choose a retained filed vehicle tax return before preparing a correction.'))
        self._check_xml()
        rec = self.copy({'filing_type': 'corrective', 'original_return_id': self.id,
                         'declaration_date': fields.Date.context_today(self)})
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': rec.id,
                'view_mode': 'form', 'target': 'current'}

    def action_create_additional(self):
        self.ensure_one()
        self._lock()
        if self.state != 'submitted':
            raise UserError(_('Choose a retained filed vehicle tax return before preparing a correction.'))
        self._check_xml()
        rec = self.copy({'filing_type': 'additional', 'original_return_id': self.id,
            'declaration_date': fields.Date.context_today(self), 'discovery_date': fields.Date.context_today(self),
            'correction_evidence': False})
        for original, copied in zip(self.line_ids.sorted('id'), rec.line_ids.sorted('id')):
            copied.previous_line_id = original
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': rec.id,
                'view_mode': 'form', 'target': 'current'}

    def action_suggest_projected_tax(self):
        self.ensure_one()
        self._check_edit_lines()
        following = self.year+1
        january = date(following, 1, 1)
        versions = self.env['l10n.sk.vehicle.tax.version'].search([
            ('date_from', '<=', january), '|', ('date_to', '=', False), ('date_to', '>=', date(following, 12, 31))])
        if len(versions) != 1:
            raise UserError(_('Select one reviewed form and rate edition covering the next January fleet.'))
        total = Decimal(0)
        for line in self.line_ids:
            if line.liability_from > january or (line.liability_to and line.liability_to < january):
                continue
            try:
                value = calculate_vehicle(year=following, category='L' if line.category.startswith('L') else line.category,
                    first_registered=line.first_registered, liability_from=january, liability_to=date(following, 1, 31),
                    propulsion=line.propulsion, engine_cm3=line.engine_cm3, power_kw=line.power_kw,
                    weight_kg=line.weight_kg, schedule=versions.schedule)
            except (ValueError, TypeError, KeyError) as error:
                raise UserError(self._calculation_error(error)) from error
            total += Decimal(value['segments'][0]['annual_final'])
        self.write({'projected_tax': float(total), 'projection_evidence': False})
        return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {
            'type': 'warning', 'sticky': True,
            'message': _('Projected tax was suggested from the known vehicles. Review the complete next January fleet, additions, disposals and rate edition before calculating the return.')}}


    def action_add_fleet_vehicles(self):
        self.ensure_one()
        self._check_edit_lines()
        vehicles = self.env['fleet.vehicle'].with_context(active_test=False).search([
            ('company_id', '=', self.company_id.id),
            '|', ('acquisition_date', '=', False), ('acquisition_date', '<=', self.date_to),
            '|', ('write_off_date', '=', False), ('write_off_date', '>=', self.date_from)])
        for vehicle in vehicles - self.line_ids.vehicle_id:
            if vehicle.l10n_sk_tax_exempt or vehicle.l10n_sk_not_taxable_reason:
                if not (vehicle.l10n_sk_not_taxable_reason or '').strip():
                    raise UserError(_('Retain the exemption or outside-scope evidence on the fleet vehicle.'))
                continue
            self.env['l10n.sk.vehicle.tax.line'].create({'return_id': self.id, 'vehicle_id': vehicle.id,
                'evidence': _('Review the imported fleet documents and liability before calculation.')})
        return True


class VehicleTaxLine(models.Model):
    _name = 'l10n.sk.vehicle.tax.line'
    _description = 'Reviewed vehicle tax technical facts'
    _check_company_auto = True
    _order = 'id'

    return_id = fields.Many2one('l10n.sk.vehicle.tax.return', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='return_id.company_id', store=True)
    vehicle_id = fields.Many2one('fleet.vehicle', check_company=True, ondelete='restrict', string='Fleet vehicle')
    vehicle_source = fields.Json(readonly=True, copy=False)
    registration_number = fields.Char(required=True)
    category = fields.Selection([(key, key) for key in ('M1', 'M2', 'M3', 'N1', 'N2', 'N3',
        'O1', 'O2', 'O3', 'O4', 'L1e', 'L2e', 'L3e', 'L4e', 'L5e', 'L6e', 'L7e')],
                                 required=True, default='M1')
    first_registered = fields.Date(required=True)
    liability_from = fields.Date(required=True)
    liability_to = fields.Date()
    propulsion = fields.Selection([('combustion', 'Combustion'), ('lpg', 'LPG'),
        ('hybrid', 'Documented hybrid'), ('cng', 'CNG'), ('lng', 'LNG'), ('hydrogen', 'Hydrogen'),
        ('electric', 'Electric only')], required=True, default='combustion')
    engine_cm3 = fields.Integer()
    power_kw = fields.Float(digits=(12, 3))
    weight_kg = fields.Integer()
    axles = fields.Integer()
    taxpayer = fields.Selection([(key, key) for key in ('a', 'b', 'c', 'd', 'e')], required=True, default='a')
    facts_reviewed = fields.Boolean(string='Taxable in Slovakia; technical document and liability reviewed')
    evidence = fields.Text(required=True)
    previous_line_id = fields.Many2one('l10n.sk.vehicle.tax.line', string='Previous filed vehicle',
                                        ondelete='restrict', check_company=True, copy=False)
    zero_liability_reviewed = fields.Boolean(string='Review complete removal of a prior erroneous tax liability')

    @api.model_create_multi
    def create(self, values_list):
        normalized = []
        for values in values_list:
            values = dict(values)
            if 'vehicle_source' in values or 'default_vehicle_source' in self.env.context:
                raise UserError(_('Refresh the reviewed vehicle snapshot through its fleet record.'))
            vehicle = self.env['fleet.vehicle'].browse(values.get('vehicle_id') or self.env.context.get('default_vehicle_id')).exists()
            if vehicle:
                source = vehicle._l10n_sk_vehicle_tax_identity()
                values = {**source['facts'], **values, 'vehicle_id': vehicle.id, 'vehicle_source': source}
            values.setdefault('return_id', self.env.context.get('default_return_id'))
            if not values['return_id']:
                raise UserError(_('Choose the vehicle tax return before adding technical facts.'))
            if 'company_id' in values or 'default_company_id' in self.env.context:
                # The company is always derived, including API default values.
                company = self.env['l10n.sk.vehicle.tax.return'].browse(values['return_id']).company_id
                if values.get('company_id', self.env.context.get('default_company_id')) != company.id:
                    raise UserError(_('Vehicle facts must belong to their return company.'))
                values.pop('company_id', None)
            self.env['l10n.sk.vehicle.tax.return'].browse(values['return_id'])._check_edit_lines()
            normalized.append(values)
        clean_context = dict(self.env.context)
        clean_context.pop('default_company_id', None)
        return super(VehicleTaxLine, self.with_context(clean_context)).create(normalized)

    def write(self, values):
        if 'vehicle_source' in values:
            raise UserError(_('Refresh the reviewed vehicle snapshot through its fleet record.'))
        if {'return_id', 'company_id'} & values.keys():
            raise UserError(_('Vehicle facts cannot be moved to another return or company.'))
        self.return_id._check_edit_lines()
        if 'vehicle_id' in values:
            raise UserError(_('Add a new vehicle line instead of reassigning its retained fleet identity.'))
        return super().write(values)

    def action_refresh_vehicle(self):
        self.return_id._check_edit_lines()
        for line in self:
            if not line.vehicle_id or line.vehicle_id.company_id != line.company_id:
                raise UserError(_('Select a fleet vehicle belonging to the return company.'))
            source = line.vehicle_id._l10n_sk_vehicle_tax_identity()
            super(VehicleTaxLine, line).write({**source['facts'], 'vehicle_source': source,
                'facts_reviewed': False})
        return True

    @api.onchange('vehicle_id')
    def _onchange_vehicle(self):
        for line in self.filtered('vehicle_id'):
            line.update(line.vehicle_id._l10n_sk_vehicle_tax_facts())
            line.facts_reviewed = False

    def unlink(self):
        self.return_id._check_edit_lines()
        return super().unlink()

    def _facts(self):
        self.ensure_one()
        names = ('registration_number', 'category', 'first_registered', 'liability_from', 'liability_to',
            'propulsion', 'engine_cm3', 'power_kw', 'weight_kg', 'axles', 'taxpayer', 'facts_reviewed', 'evidence',
            'zero_liability_reviewed')
        return dict({key: fields.Date.to_string(getattr(self, key)) if key in
                ('first_registered', 'liability_from', 'liability_to') else getattr(self, key) for key in names}
            , previous_line=self.previous_line_id.id,
            vehicle_source=self.vehicle_id._l10n_sk_vehicle_tax_identity() if self.vehicle_id else None)

    def _calculate(self):
        self.ensure_one()
        if not self.vehicle_id or self.vehicle_id.company_id != self.company_id:
            raise UserError(_('Select a fleet vehicle belonging to the return company.'))
        source = self.vehicle_id._l10n_sk_vehicle_tax_identity()
        facts = self._facts()
        if (source != self.vehicle_source or any(facts[key] != value for key, value in source['facts'].items())):
            raise UserError(_('The fleet source changed. Refresh its draft snapshot and review the vehicle facts again.'))
        if not self.facts_reviewed or not self.evidence or not self.registration_number.strip():
            raise UserError(_('Review the vehicle technical document, Slovak taxable status and liability evidence.'))
        if self.category == 'N1' and (self.axles < 1 or not 0 < self.weight_kg <= 3500):
            raise UserError(_('An N1 vehicle needs documented axles and maximum permissible mass up to 3500 kg.'))
        if self.zero_liability_reviewed and (self.return_id.filing_type != 'additional' or not self.previous_line_id):
            raise UserError(_('Complete removal of an erroneous liability requires a reviewed previous vehicle in an additional return.'))
        try:
            result = calculate_vehicle(year=self.return_id.year,
                category='L' if self.category.startswith('L') else self.category,
                first_registered=self.first_registered, liability_from=self.liability_from,
                liability_to=self.liability_to or None, propulsion=self.propulsion,
                engine_cm3=self.engine_cm3, power_kw=self.power_kw, weight_kg=self.weight_kg,
                schedule=self.return_id.version_id.schedule, allow_empty_year=self.zero_liability_reviewed)
        except (ValueError, TypeError, KeyError) as error:
            raise UserError(self.return_id._calculation_error(error)) from error
        result.update(facts=self._facts())
        return result


class VehicleTaxReturnLines(models.Model):
    _inherit = 'l10n.sk.vehicle.tax.return'

    def _check_edit_lines(self):
        self._lock()
        if any(rec.state != 'draft' for rec in self):
            raise UserError(_('Reset the unfiled return to draft before changing vehicle tax facts.'))


class VehicleTaxAttachment(models.Model):
    _inherit = 'ir.attachment'

    def _vehicle_returns(self):
        ids = self.filtered(lambda rec: rec.res_model == 'l10n.sk.vehicle.tax.return' and rec.res_id).mapped('res_id')
        return self.env['l10n.sk.vehicle.tax.return'].browse(ids).exists()

    def write(self, values):
        returns = self._vehicle_returns()
        protected = self.filtered(lambda attachment: any(
            attachment in (rec.filed_history_ids | rec.xml_attachment_id) for rec in returns))
        for attachment in protected:
            if any(key in values and values[key] != attachment[key] for key in ('store_fname', 'checksum', 'file_size')):
                raise UserError(_('Vehicle tax XML snapshots cannot be replaced or reassigned. Export a new snapshot.'))
            if any(key in values and values[key] != attachment[key] for key in
                   ('res_model', 'res_id', 'res_field', 'company_id', 'type', 'url')):
                raise UserError(_('Vehicle tax XML snapshots cannot be replaced or reassigned. Export a new snapshot.'))
            for key in ('datas', 'raw', 'db_datas'):
                if key in values:
                    value = values[key] or b''
                    raw = base64.b64decode(value) if key == 'datas' else value
                    if raw != attachment.raw:
                        raise UserError(_('Vehicle tax XML snapshots cannot be replaced or reassigned. Export a new snapshot.'))
        return super().write(values)

    def unlink(self):
        returns = self._vehicle_returns()
        if returns.filtered(lambda rec: bool((rec.filed_history_ids | rec.xml_attachment_id) & self)):
            raise UserError(_('The active or filed vehicle tax XML snapshot must be retained.'))
        return super().unlink()
