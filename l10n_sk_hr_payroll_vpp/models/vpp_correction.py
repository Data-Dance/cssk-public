# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Full corrective VPP, not a negative/delta payroll or a bank operation."""
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class Vpp(models.Model):
    _inherit = 'l10n.sk.vpp'
    _supported_correction_types = ('regular', 'corrective')

    replaced_vpp_id = fields.Many2one('l10n.sk.vpp', string='Replaces filed VPP',
                                         ondelete='restrict', copy=False, check_company=True)

    def _retained_prior_vpp(self):
        """Use the declaration base's company/period lookup, retaining its scope."""
        self.ensure_one()
        return self._prior_submitted().filtered(
            lambda prior: prior.submitted_attachment_id
            and prior.submitted_attachment_id in prior.filed_history_ids)

    def _prefill_replaced_vpp(self):
        for report in self.filtered(lambda rec: rec.correction_type == 'corrective' and not rec.replaced_vpp_id):
            candidates = report._retained_prior_vpp()
            if len(candidates) == 1:
                report.replaced_vpp_id = candidates

    @api.onchange('correction_type', 'company_id', 'year', 'month')
    def _onchange_replaced_vpp(self):
        for report in self:
            if report.correction_type != 'corrective':
                report.replaced_vpp_id = False
            elif not report.replaced_vpp_id or report.replaced_vpp_id not in report._retained_prior_vpp():
                report.replaced_vpp_id = False
                report._prefill_replaced_vpp()

    @api.model_create_multi
    def create(self, values_list):
        reports = super().create(values_list)
        for report, values in zip(reports, values_list):
            if 'replaced_vpp_id' not in values:
                report._prefill_replaced_vpp()
        return reports

    def write(self, values):
        identity = {'company_id', 'year', 'month', 'version_id', 'correction_type',
                    'correction_reference', 'replaced_vpp_id'}
        if identity & values.keys() and any(report.state != 'draft' for report in self):
            raise UserError(_('Reset the VPP to draft before changing its period or correction identity. The filed copy is retained.'))
        result = super().write(values)
        if {'correction_type', 'company_id', 'year', 'month'} & values.keys() and 'replaced_vpp_id' not in values:
            self._prefill_replaced_vpp()
        return result

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
