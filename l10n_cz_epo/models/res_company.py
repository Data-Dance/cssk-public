# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_cz_epo_certificate_id = fields.Many2one(
        "l10n.cz.epo.certificate", string="EPO signing certificate",
        domain="[('company_id', '=', id)]",
        help="The qualified certificate EPO filings of this company are "
        "signed with.")
    l10n_cz_epo_allow_filing = fields.Boolean(
        string="Allow filing through EPO",
        help="Off: EPO is used only to CHECK filings (test mode, nothing is "
        "filed). On: a queued EPO submission is filed for real. Checking and "
        "filing differ by one parameter of the same call, so the difference is "
        "enforced here rather than left to habit.")
