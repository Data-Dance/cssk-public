# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The partner's NACE code gives it its industry.

The code (``partner_nace``) is what registers return and forms file; the
industry is the readable, hierarchical label. A code sets the industry unless
someone chose an industry that is not a NACE one; picking a NACE industry in
the form fills the code.
"""

from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _nace_sync_industry(self):
        for partner in self.filtered("nace_code"):
            if partner.industry_id and not partner.industry_id.nace_version:
                continue  # a deliberate non-NACE industry
            industry = self.env["res.partner.industry"]._nace_find(partner.nace_code)
            if industry and industry != partner.industry_id:
                partner.industry_id = industry

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        partners.filtered(lambda p: p.nace_code and not p.industry_id)._nace_sync_industry()
        return partners

    def write(self, vals):
        res = super().write(vals)
        if vals.get("nace_code") and "industry_id" not in vals:
            self._nace_sync_industry()
        return res

    @api.onchange("industry_id")
    def _onchange_industry_id_nace(self):
        industry = self.industry_id
        if industry.nace_version and industry.nace_code and industry.nace_code.isdigit():
            self.nace_code = industry.nace_code
