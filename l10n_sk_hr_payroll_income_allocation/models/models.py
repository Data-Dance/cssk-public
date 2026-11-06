# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import hashlib
import json
import base64
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from .allocation import allocate
from .premiums import calculate_standard_premiums
from .parameters import dated_statutory
from .allocation import CHANNELS, months


class IncomeAllocation(models.Model):
    _name = 'l10n.sk.income.allocation'
    _description = 'Historical assessment-base calculation, not posted payroll'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(required=True)
    employee_id = fields.Many2one('hr.employee', required=True, tracking=True)
    company_id = fields.Many2one(related='employee_id.company_id', store=True)
    currency_id = fields.Many2one(related='company_id.currency_id')
    icpv = fields.Char(required=True, string='Reviewed SP relationship identifier')
    insurance_start = fields.Date(required=True)
    insurance_end = fields.Date(required=True)
    settled_on = fields.Date(required=True, string='Income settled for payment on')
    amount = fields.Monetary(required=True, string='Additional gross income')
    evidence = fields.Char(required=True, string='Settlement/insurance evidence')
    history_evidence = fields.Char(required=True, string='Historical bases, OOP and ceilings evidence')
    ledger = fields.Json(string='Legacy API historical ledger',
                         help='API compatibility only. Use editable history rows in the form.')
    history_ids = fields.One2many('l10n.sk.income.allocation.history', 'allocation_id',
                                  string='Reviewed historical fund facts', copy=True)
    result = fields.Json(readonly=True, copy=False)
    input_digest = fields.Char(readonly=True, copy=False)
    line_ids = fields.One2many('l10n.sk.income.allocation.line', 'allocation_id', readonly=True, copy=False)
    calculation_attachment_id = fields.Many2one('ir.attachment', readonly=True, copy=False)
    premium_evidence = fields.Char(string='Review of standard rates, coverage and absence of relief')
    premium_digest = fields.Char(readonly=True, copy=False)
    premium_attachment_id = fields.Many2one('ir.attachment', readonly=True, copy=False)
    state = fields.Selection([('draft', 'Draft'), ('calculated', 'Bases calculated'),
                              ('premiums', 'Standard social premiums calculated')],
                             required=True, default='draft', readonly=True, copy=False)
    _protected = frozenset(('result', 'input_digest', 'state', 'line_ids', 'calculation_attachment_id',
                            'premium_digest', 'premium_attachment_id'))

    @api.model_create_multi
    def create(self, vals_list):
        if any(self._protected & values.keys() for values in vals_list):
            raise UserError(_('Calculate the historical assessment bases using the calculation action.'))
        return super().create(vals_list)

    def write(self, values):
        reviewing_premiums = set(values) <= {'premium_evidence'} and all(rec.state in ('draft', 'calculated') for rec in self)
        if self._protected & values.keys() or (values and not reviewing_premiums and any(rec.state != 'draft' for rec in self)):
            raise UserError(_('Reset this calculation to draft before changing its source evidence.'))
        return super().write(values)

    def unlink(self):
        if any(rec.state != 'draft' for rec in self):
            raise UserError(_('Calculated evidence must be reset before deletion.'))
        return super().unlink()

    def _inputs(self):
        self.ensure_one()
        if self.history_ids and self.ledger:
            raise UserError(_('Use either editable historical rows or the API ledger, not both.'))
        ledger = self.ledger
        if self.history_ids:
            grouped = {}
            for row in self.history_ids:
                if not (row.evidence or '').strip():
                    raise UserError(_('Review every historical row and record its evidence before calculation.'))
                month = row.month.strftime('%Y-%m')
                funds = grouped.setdefault(month, {})
                if row.channel in funds:
                    raise UserError(_('Each historical month/fund must occur exactly once.'))
                funds[row.channel] = {
                    'insured': row.insured, 'raw_before': row.raw_before,
                    'base_before': str(row.base_before), 'oop': str(row.oop),
                    'cap': None if row.uncapped else str(row.cap),
                    'paid_at_cap': row.paid_at_cap,
                }
            ledger = [{'month': month, 'funds': funds} for month, funds in sorted(grouped.items())]
        return {'employee': self.employee_id.id, 'company': self.company_id.id,
                'icpv': self.icpv, 'amount': str(self.amount),
                'start': str(self.insurance_start), 'end': str(self.insurance_end),
                'settled': str(self.settled_on), 'ledger': ledger,
                'row_evidence': {str(row.id): row.evidence for row in self.history_ids},
                'statutory': dated_statutory(self.env, self.insurance_start, self.insurance_end),
                'evidence': self.evidence, 'history_evidence': self.history_evidence}

    def action_prepare_history(self):
        """Editable fallback when the original payroll is outside Odoo.

        No coverage or payment-at-ceiling is inferred. All rows start as
        unreviewed and calculation requires evidence for each of them.
        """
        for rec in self:
            if rec.state != 'draft' or rec.history_ids or rec.ledger:
                raise UserError(_('Prepare history only on an empty draft register.'))
            if not rec.insurance_start or not rec.insurance_end or rec.insurance_start > rec.insurance_end:
                raise UserError(_('Supply the insurance relationship dates first.'))
            statutory = dated_statutory(rec.env, rec.insurance_start, rec.insurance_end)
            rec.history_ids = [(0, 0, {
                'month': month + '-01', 'channel': channel, 'raw_before': '0',
                'uncapped': channel == 'up_er',
                'cap': 0 if channel == 'up_er' else float(statutory[month]['maximum']),
            }) for month in months(rec.insurance_start, rec.insurance_end) for channel in CHANNELS]
        return True

    def action_calculate(self):
        for rec in self:
            if rec.company_id not in self.env.companies:
                raise UserError(_('The calculation belongs to a company outside the active scope.'))
            if rec.currency_id.name != 'EUR':
                raise UserError(_('This Slovak social assessment register requires amounts in EUR.'))
            if (not rec.icpv or len(rec.icpv) != 12 or not rec.icpv.isascii()
                    or not rec.icpv.isdigit()):
                raise UserError(_('Supply the twelve-digit relationship identifier assigned by SP.'))
            if not (rec.evidence or '').strip() or not (rec.history_evidence or '').strip():
                raise UserError(_('Record the actual sources of the settlement and historical fund facts.'))
            inputs = json.dumps(rec._inputs(), sort_keys=True, ensure_ascii=False)
            digest = hashlib.sha256(inputs.encode()).hexdigest()
            if rec.state != 'draft':
                if rec.input_digest != digest:
                    raise UserError(_('The calculated inputs have changed. Review the historical calculation.'))
                continue
            try:
                source = rec._inputs()
                result = allocate(rec.amount, rec.insurance_start, rec.insurance_end,
                                  rec.settled_on, source['ledger'], source['statutory'])
            except ValueError as exc:
                raise UserError(str(exc)) from exc
            result.update(employee_id=rec.employee_id.id, company_id=rec.company_id.id,
                          icpv=rec.icpv, input_digest=digest,
                          premiums_calculated=False, payroll_posted=False, official_submission=False)
            details = []
            for channel, fund in result['funds'].items():
                for row in fund['rows']:
                    details.append({'allocation_id': rec.id, 'month': row['month'],
                                    'channel': channel, 'insured': row['insured'],
                                    'excluded_at_cap': row['excluded_at_cap'],
                                    'exact_share': row['exact_share'],
                                    **{key: float(row[key]) for key in ('base_before', 'base_after', 'additional_base')}})
            self.env['l10n.sk.income.allocation.line']._create_calculated(details)
            attachment = self.env['ir.attachment'].create({
                'name': 'SP-assessment-bases-' + digest + '.json',
                'res_model': rec._name, 'res_id': rec.id, 'mimetype': 'application/json',
                'datas': base64.b64encode(json.dumps({'inputs': rec._inputs(), 'result': result},
                                                     ensure_ascii=False, sort_keys=True, indent=2).encode())})
            super(IncomeAllocation, rec).write({'result': result, 'input_digest': digest,
                                               'state': 'calculated', 'calculation_attachment_id': attachment.id})
        return True

    def action_calculate_standard_premiums(self):
        for rec in self:
            if rec.state == 'draft':
                raise UserError(_('Calculate and review the historical assessment bases first.'))
            rec.action_calculate()  # validates company, currency and source digest
            if not (rec.premium_evidence or '').strip():
                raise UserError(_('Review the historical insurance coverage and confirm standard rates without special relief.'))
            payload = {'base_digest': rec.input_digest, 'policy': 'dated-standard-no-relief-v2',
                       'review': rec.premium_evidence}
            digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
            if rec.state == 'premiums':
                if rec.premium_digest != digest:
                    raise UserError(_('The premium review no longer matches its archived calculation.'))
                continue
            try:
                result = calculate_standard_premiums(rec.result, rec._inputs()['statutory'])
            except ValueError as exc:
                raise UserError(str(exc)) from exc
            result.update(premium_digest=digest, premium_review=rec.premium_evidence)
            rec.line_ids._write_calculated_premiums(result)
            attachment = self.env['ir.attachment'].create({
                'name': 'SP-standard-premiums-' + digest + '.json',
                'res_model': rec._name, 'res_id': rec.id, 'mimetype': 'application/json',
                'datas': base64.b64encode(json.dumps({'inputs': rec._inputs(), 'result': result},
                                                     ensure_ascii=False, sort_keys=True, indent=2).encode())})
            super(IncomeAllocation, rec).write({'result': result, 'premium_digest': digest,
                                               'premium_attachment_id': attachment.id, 'state': 'premiums'})
        return True

    def action_reset(self):
        self.line_ids._unlink_calculated()
        return super().write({'result': False, 'input_digest': False, 'state': 'draft',
                              'calculation_attachment_id': False, 'premium_digest': False,
                              'premium_attachment_id': False, 'premium_evidence': False})


class AllocationLine(models.Model):
    _name = 'l10n.sk.income.allocation.line'
    _description = 'Calculated historical fund/month assessment base'
    _order = 'month, channel, id'

    allocation_id = fields.Many2one('l10n.sk.income.allocation', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='allocation_id.company_id', store=True)
    currency_id = fields.Many2one(related='allocation_id.currency_id')
    month = fields.Char(required=True)
    channel = fields.Selection([(value, value) for value in (
        'np_ee', 'np_er', 'sp_ee', 'sp_er', 'ip_ee', 'ip_er', 'pvn_ee', 'pvn_er',
        'up_er', 'gp_er', 'rfs_er', 'pfp_er')], required=True)
    insured = fields.Boolean()
    excluded_at_cap = fields.Boolean()
    exact_share = fields.Char()
    base_before = fields.Monetary()
    base_after = fields.Monetary()
    additional_base = fields.Monetary()
    rate = fields.Float(string='Rate (%)')
    premium = fields.Monetary(string='Additional social premium')

    @api.model_create_multi
    def create(self, vals_list):
        raise UserError(_('Historical result rows are generated by the calculation, not entered separately.'))

    def write(self, vals):
        raise UserError(_('Reset and recalculate the source register to change historical result rows.'))

    def unlink(self):
        raise UserError(_('Reset and recalculate the source register to remove historical result rows.'))

    @api.model
    def _create_calculated(self, vals_list):
        return super().create(vals_list)

    def _unlink_calculated(self):
        return super().unlink()

    def _write_calculated_premiums(self, result):
        rows = {(channel, row['month']): row for channel, fund in result['funds'].items() for row in fund['rows']}
        if len(rows) != len(self):
            raise UserError(_('Premium results do not match the calculated fund/month rows.'))
        for line in self:
            row = rows.get((line.channel, line.month))
            if not row or float(row['additional_base']) != line.additional_base:
                raise UserError(_('A fund/month assessment row changed before premium calculation.'))
            super(AllocationLine, line).write({'rate': float(row['rate']), 'premium': float(row['premium'])})
