# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from .allocation import CHANNELS


class AllocationHistory(models.Model):
    _name = 'l10n.sk.income.allocation.history'
    _description = 'Editable reviewed historical fund/month facts'
    _order = 'month, channel, id'

    allocation_id = fields.Many2one('l10n.sk.income.allocation', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='allocation_id.company_id', store=True)
    currency_id = fields.Many2one(related='allocation_id.currency_id')
    month = fields.Date(required=True, help='First day of the historical calendar month.')
    channel = fields.Selection([(code, code) for code in CHANNELS], required=True)
    insured = fields.Boolean()
    raw_before = fields.Char(required=True, default='0', help='Exact unreduced base, including fractions such as 1000/3.')
    base_before = fields.Monetary()
    oop = fields.Monetary(string='Nominal claimed agreement OOP')
    uncapped = fields.Boolean()
    cap = fields.Monetary(string='Reviewed effective ceiling')
    paid_at_cap = fields.Boolean(string='Premium paid at ceiling')
    evidence = fields.Char(help='Reference to reviewed payroll, payment and coverage evidence; required for calculation.')
    _month_fund_unique = models.Constraint('unique (allocation_id, month, channel)',
                                           'Each historical month/fund must occur exactly once.')

    @api.constrains('month')
    def _check_month(self):
        if any(row.month.day != 1 for row in self):
            raise ValidationError(_('Use the first day of the historical calendar month.'))

    @api.model_create_multi
    def create(self, vals_list):
        if any({'company_id', 'currency_id'} & values.keys() for values in vals_list):
            raise UserError(_('Company and currency are inherited from the register.'))
        parents = self.env['l10n.sk.income.allocation'].browse([values.get('allocation_id') for values in vals_list])
        if any(parent.state != 'draft' for parent in parents):
            raise UserError(_('Reset the register before changing historical facts.'))
        return super().create(vals_list)

    def write(self, values):
        if {'company_id', 'currency_id'} & values.keys():
            raise UserError(_('Company and currency are inherited from the register.'))
        parents = self.allocation_id
        if values.get('allocation_id'):
            parents |= self.env['l10n.sk.income.allocation'].browse(values['allocation_id'])
        if any(parent.state != 'draft' for parent in parents):
            raise UserError(_('Reset the register before changing historical facts.'))
        return super().write(values)

    def unlink(self):
        if any(parent.state != 'draft' for parent in self.allocation_id):
            raise UserError(_('Reset the register before deleting historical facts.'))
        return super().unlink()
