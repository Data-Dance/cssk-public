# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""DPHDP3 in a period where the status changes.

``typ_platce`` is taken on the return's last day — that is the hook's
contract — so a month in which a plátce became an identifikovaná osoba files
as I. What the month *contains* is still right, because every document was
taxed by the status on its own DUZP; but whether the change also splits the
filing is a decision for the taxpayer and the tax office, not for a template.
The return says so in its chatter when it is computed, rather than guessing.
"""

from odoo import _, models


class CsskVatReturn(models.Model):
    _inherit = "cssk.vat.return"

    def action_compute_lines(self):
        res = super().action_compute_lines()
        for ret in self:
            company = ret.company_id
            if (ret.country_id.code != "CZ"
                    or not company._l10n_cz_vat_status_has_history()):
                continue
            segments = company._l10n_cz_vat_status_segments(
                ret.date_from, ret.date_to)
            if len({s for _a, _b, s in segments}) > 1:
                ret.message_post(body=_(
                    "The company's VAT status changes within this period: "
                    "%(detail)s. Each document was taxed by the status on its "
                    "DUZP; typ_platce is filed as %(typ)s, the status on the "
                    "last day. Check with the tax office whether the change "
                    "needs a separate filing for part of the period.",
                    detail=company._l10n_cz_vat_status_describe(segments),
                    typ=company._l10n_cz_typ_platce(ret.date_to)))
        return res
