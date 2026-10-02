# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Generate the archived historical Czech VAT rates for existing companies.

    Runs on install rather than waiting to be asked, because the rates are
    archived: nothing appears in a picker, nothing changes on a document, and
    the only observable effect is that a history import has something correct to
    map onto. A company that loads the Czech chart later gets them from
    :meth:`~odoo.addons.l10n_cz_vat_return.models.res_company.ResCompany`'s
    chart-load hook.
    """
    companies = env["res.company"].search([("chart_template", "=", "cz")])
    if companies:
        companies._cssk_create_historic_vat_taxes()
        # ř43/ř44: l10n_cz leaves the deduction leg of every self-assessed
        # purchase tax untagged, so the deduction reaches no line of the
        # return. See _cz_tag_selfassessed_deduction for the measurement.
        companies._cz_tag_selfassessed_deduction()
        # l10n_cz names the self-assessed leg's account on the invoice side
        # and omits it on the refund side, so a reverse-charge correction
        # leaves its VAT on the base account. See the method.
        companies._cz_fix_refund_repartition_accounts()
        # l10n_cz maps nothing onto its intra-Community acquisition taxes, so
        # an EU vendor bill keeps the domestic VAT. See the method.
        companies._cz_map_intra_community_purchase_taxes()
        _logger.info(
            "l10n_cz_vat_return: historical VAT rates prepared for %s company "
            "(companies)", len(companies),
        )
