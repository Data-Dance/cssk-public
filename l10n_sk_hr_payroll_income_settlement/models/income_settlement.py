# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import hashlib
import json
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from .settlement import calculate_settlement, PARAM_CODES, FACT_KEYS, PENSIONS


class Settlement(models.Model):
    _name = 'l10n.sk.income.settlement'
    _description = 'Reviewed additional-income tax and health calculation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True)
    allocation_id = fields.Many2one('l10n.sk.income.allocation', required=True, ondelete='restrict')
    employee_id = fields.Many2one(related='allocation_id.employee_id', store=True)
    company_id = fields.Many2one(related='allocation_id.company_id', store=True)
    facts = fields.Json(string='Legacy API tax and health facts')
    currency_id = fields.Many2one(related='company_id.currency_id')
    paid_on = fields.Date(string='Actual/planned payment date')
    agreement = fields.Selection([(key, key) for key in ('none', 'dopc', 'dovp', 'dobps')], default='none')
    pension = fields.Selection([(key, key) for key in sorted(PENSIONS)], default='none')
    disabled = fields.Boolean(string='Health disability status')
    minimum_exception = fields.Selection([(key, key) for key in (
        'none', 'state_insured', 'multiple_payers_notice', 'disabled')], default='none')
    tax_declaration = fields.Boolean(string='Reviewed monthly tax declaration')
    pension_at_jan1 = fields.Boolean(string='Tax-relevant pensioner at 1 January under section 11(6)')
    no_child_bonus = fields.Boolean(string='Reviewed: no child bonus in this calculation')
    no_other_adjustments = fields.Boolean(string='Reviewed: no other benefits or deductions')
    only_2y_health_day = fields.Boolean(string='Reviewed: only the 2Y health day in the reporting month')
    other_tax_base = fields.Monetary(string='Previous monthly tax base before NČZD')
    other_tax_withheld = fields.Monetary(string='Previous monthly advance tax')
    other_health_base = fields.Monetary(string='Previous same-profile health base')
    other_health_employee = fields.Monetary(string='Previous employee health advance')
    other_health_employer = fields.Monetary(string='Previous employer health advance')
    other_health_topup = fields.Monetary(string='Previous health minimum top-up')
    evidence = fields.Text(required=True, string='Tax declaration, health profile and other payments evidence')
    state = fields.Selection([('draft', 'Draft'), ('calculated', 'Calculated, not posted')],
                             default='draft', required=True, readonly=True, copy=False)
    result = fields.Json(readonly=True, copy=False)
    input_digest = fields.Char(readonly=True, copy=False)
    attachment_id = fields.Many2one('ir.attachment', readonly=True, copy=False)
    _protected = frozenset(('state', 'result', 'input_digest', 'attachment_id'))

    @api.model_create_multi
    def create(self, vals_list):
        if any(self._protected & values.keys() for values in vals_list):
            raise UserError(_('Use the calculation action to generate settlement evidence.'))
        return super().create(vals_list)

    def write(self, values):
        if self._protected & values.keys() or (values and any(rec.state != 'draft' for rec in self)):
            raise UserError(_('Reset this settlement before changing its reviewed inputs.'))
        return super().write(values)

    def unlink(self):
        if any(rec.state != 'draft' for rec in self):
            raise UserError(_('Calculated settlement evidence must be retained or reset first.'))
        return super().unlink()

    def _payload(self):
        self.ensure_one()
        if self.company_id not in self.env.companies:
            raise UserError(_('Activate the settlement company before calculation.'))
        allocation = self.allocation_id
        if allocation.state != 'premiums':
            raise UserError(_('Calculate the reviewed historical social premiums first.'))
        allocation.action_calculate_standard_premiums()
        if not (self.evidence or '').strip():
            raise UserError(_('Record evidence for health status, tax declaration and all other monthly payments.'))
        get_value = self.env['hr.rule.parameter']._get_parameter_value
        if self.facts and self.paid_on:
            raise UserError(_('Use either the editable form facts or the API facts, not both.'))
        facts = self.facts
        if not facts:
            facts = {key: self[key] for key in FACT_KEYS}
            facts['paid_on'] = str(self.paid_on) if self.paid_on else ''
        return {'allocation_id': allocation.id, 'social': allocation.result,
                'facts': facts, 'evidence': self.evidence,
                'parameters': {code: get_value(code, allocation.settled_on) for code in PARAM_CODES}}

    def action_calculate(self):
        for rec in self:
            payload = rec._payload()
            digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            if rec.state != 'draft':
                if rec.input_digest != digest:
                    raise UserError(_('Source evidence or dated parameters changed; review and recalculate this settlement.'))
                continue
            try:
                result = calculate_settlement(payload['social'], payload['facts'], payload['parameters'])
            except (ValueError, TypeError, KeyError) as exc:
                raise UserError(str(exc)) from exc
            result.update(allocation_id=rec.allocation_id.id, employee_id=rec.employee_id.id,
                          company_id=rec.company_id.id, input_digest=digest)
            attachment = self.env['ir.attachment'].create({
                'name': 'SK-income-settlement-' + digest + '.json', 'res_model': rec._name,
                'res_id': rec.id, 'mimetype': 'application/json',
                'datas': base64.b64encode(json.dumps({'inputs': payload, 'result': result},
                                                     sort_keys=True, ensure_ascii=False, indent=2).encode())})
            super(Settlement, rec).write({'result': result, 'input_digest': digest,
                                          'attachment_id': attachment.id, 'state': 'calculated'})
        return True

    def action_reset(self):
        return super().write({'state': 'draft', 'result': False, 'input_digest': False, 'attachment_id': False})


class Allocation(models.Model):
    _inherit = 'l10n.sk.income.allocation'

    def action_reset(self):
        if self.env['l10n.sk.income.settlement'].search_count([
                ('allocation_id', 'in', self.ids), ('state', '=', 'calculated')]):
            raise UserError(_('Reset the dependent tax/health settlement before changing its social-premium source.'))
        return super().action_reset()
