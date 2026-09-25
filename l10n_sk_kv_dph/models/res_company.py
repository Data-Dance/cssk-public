# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)

#: The sale-side domestic reverse-charge tax (§69 ods. 12) that carries an
#: issued 0 % supply into KV oddiel A.2. Chart-template xmlid suffix.
SK_RC_OUT_TEMPLATE = "vs_rc_out"

#: Self-assessment purchase taxes that belong in KV oddiel B.1:
#: - vs_rc_*     domestic reverse charge (prenos DP, § 69 ods. 12)
#: - vs_nad_eu_* intra-EU acquisitions of goods (§ 11) — confirmed in scope of
#:   B.1 by the KVDPHv17 poučenie (§ 69 ods. 2,3,6,7,9-12 incl. § 11/11a)
#: NOT flagged (accountant call pending): vs_tri_* (trojstranný obchod) and
#: vs_imp_post_* (import self-assessment) — add them here once confirmed.
SK_REVERSE_CHARGE_TEMPLATES = (
    "vs_rc_23", "vs_rc_19", "vs_rc_5",
    "vs_nad_eu_23", "vs_nad_eu_19", "vs_nad_eu_5",
    # received EU services, § 69 ods. 3 — shipped by l10n_sk_vat_return; a
    # company without that module simply has no such tax to flag
    "vs_eu_s_23", "vs_eu_s_19", "vs_eu_s_5",
)


class ResCompany(models.Model):
    _inherit = "res.company"

    def _cssk_reverse_charge_tax_templates(self):
        self.ensure_one()
        if self.chart_template == "sk":
            return SK_REVERSE_CHARGE_TEMPLATES
        return super()._cssk_reverse_charge_tax_templates()

    def _cssk_ensure_rc_out_tax(self):
        """Create the sale-side §69/12 reverse-charge tax on existing SK companies.

        The chart-template ``@template`` records only materialise when the SK
        chart is loaded (a new company), so a company that already had the chart
        when this module shipped would never get the tax. This creates it (once,
        idempotent via its chart-style external id) so an issued §69/12 supply has
        a 0 % tax to carry it into KV oddiel A.2 — the counterpart to the received
        ``vs_rc_*`` taxes that feed B.1. Same three-occasion reasoning as the
        reverse-charge flagging above.
        """
        created = 0
        for company in self:
            if company.chart_template != "sk":
                continue
            name = "account.%s_%s" % (company.id, SK_RC_OUT_TEMPLATE)
            if self.env.ref(name, raise_if_not_found=False):
                continue
            group = self.env.ref(
                "account.%s_tax_group_vat_0" % company.id, raise_if_not_found=False)
            if not group:
                _logger.warning("SK company %s has no VAT 0%% tax group — cannot "
                                "create the §69/12 sale-side reverse-charge tax",
                                company.display_name)
                continue
            rep = [
                (0, 0, {"repartition_type": "base", "document_type": "invoice",
                        "factor_percent": 100}),
                (0, 0, {"repartition_type": "tax", "document_type": "invoice",
                        "factor_percent": 100}),
                (0, 0, {"repartition_type": "base", "document_type": "refund",
                        "factor_percent": 100}),
                (0, 0, {"repartition_type": "tax", "document_type": "refund",
                        "factor_percent": 100}),
            ]
            tax = self.env["account.tax"].create({
                "name": "0% Reverse charge supplied (§69/12, A.2)",
                "amount": 0.0, "amount_type": "percent", "type_tax_use": "sale",
                "tax_group_id": group.id, "company_id": company.id,
                "cssk_control_is_reverse_charge": True,
                "cssk_control_section_default": "A.2",
                "repartition_line_ids": rep,
            })
            self.env["ir.model.data"].create({
                "module": "account", "name": "%s_%s" % (company.id, SK_RC_OUT_TEMPLATE),
                "model": "account.tax", "res_id": tax.id, "noupdate": True,
            })
            created += 1
            _logger.info("§69/12 sale-side reverse-charge tax created for %s",
                         company.display_name)
        return created
