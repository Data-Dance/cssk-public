# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models

from odoo.addons.account.models.chart_template import get_python_translation

#: Reconciliation models of the core chart whose LINE carries a label.
RECO_LINE_LABELS = {
    "internal_transfer_reco": "Internal Transfers",
    "bank_fees_reco": "Bank Fees",
}


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    def _load_translations(self, langs=None, companies=None, template_data=None):
        res = super()._load_translations(langs=langs, companies=companies, template_data=template_data)
        self._cssk_translate_reco_line_labels(langs=langs, companies=companies)
        return res

    @api.model
    def _cssk_translate_reco_line_labels(self, langs=None, companies=None):
        """Translate the line labels of the core reconciliation models.

        Core translates chart records by xmlid, and the lines of
        ``bank_fees_reco`` / ``internal_transfer_reco`` are created inside a
        ``Command.create`` with none, so their ``label`` stayed English and
        every bank-fee posting was labelled "Bank Fees". Only a label still
        equal to the English is written, so one a user changed is kept.
        """
        langs = [
            code for code in (langs or [c for c, _n in self.env["res.lang"].get_installed()])
            if code != "en_US"
        ]
        if not langs:
            return
        companies = companies or self.env["res.company"].search([("chart_template", "!=", False)])
        for company in companies:
            loader = self.sudo().with_company(company)
            for xmlid, english in RECO_LINE_LABELS.items():
                reco = loader.ref(xmlid, raise_if_not_found=False)
                if not reco:
                    continue
                for lang in langs:
                    translated = get_python_translation("account", lang, english)
                    if not translated or translated == english:
                        continue
                    # SQL, not the ORM: with en_US not installed (a Slovak- or
                    # Czech-only database) an ORM write in sk_SK also
                    # overwrites en_US.
                    self.env.cr.execute(
                        """UPDATE account_reconcile_model_line
                              SET label = label || jsonb_build_object(%s::text, %s::text)
                            WHERE model_id = %s AND label ->> 'en_US' = %s
                              AND COALESCE(label ->> %s, label ->> 'en_US') = %s""",
                        [lang, translated, reco.id, english, lang, english],
                    )
        self.env["account.reconcile.model.line"].invalidate_model(["label"])
