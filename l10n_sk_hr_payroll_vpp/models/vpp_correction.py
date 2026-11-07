# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Full corrective VPP, not a negative/delta payroll or a bank operation."""
from odoo import _, fields, models
from odoo.exceptions import UserError


class Vpp(models.Model):
    _inherit = 'l10n.sk.vpp'
    _supported_correction_types = ('regular', 'corrective')

    replaced_vpp_id = fields.Many2one('l10n.sk.vpp', string='Replaces filed VPP',
                                         ondelete='restrict', copy=False, check_company=True)

    def write(self, values):
        identity = {'company_id', 'year', 'month', 'version_id', 'correction_type',
                    'correction_reference', 'replaced_vpp_id'}
        if identity & values.keys() and any(report.state != 'draft' for report in self):
            raise UserError(_('Reset the VPP to draft before changing its period or correction identity. The filed copy is retained.'))
        return super().write(values)

    def _preflight(self):
        result = super()._preflight()
        for report in self:
            prior = report.replaced_vpp_id
            if report.correction_type == 'regular':
                if prior:
                    raise UserError(_('A regular VPP cannot replace a filed VPP. Select Corrective.'))
                continue
            if (not prior or prior == report or prior.company_id != report.company_id
                    or prior.date_from != report.date_from or prior.date_to != report.date_to
                    or prior.state != 'submitted' or not prior.submitted_attachment_id
                    or prior.submitted_attachment_id not in prior.filed_history_ids):
                raise UserError(_('Choose the retained filed VPP for this exact company and settlement period.'))
        return result

    def _declaration_render_context(self, data):
        context = super()._declaration_render_context(data)
        context['typ_vykazu'] = 'O' if self.correction_type == 'corrective' else 'R'
        # Native generation collects ALL current period sources. A corrective
        # VPP replaces the previous filing; it is never an amount difference.
        return context
