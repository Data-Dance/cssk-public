# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("sk", "account.tax")
    def _get_sk_kv_dph_account_tax(self):
        """The sale-side domestic reverse-charge tax (§69 ods. 12) for KV A.2.

        A supplier of a §69 ods. 12 domestic reverse charge (stavebné práce,
        železo, …) invoices at 0 % — the recipient self-assesses — and reports
        only the base in KV oddiel A.2. The Slovak chart ships the received side
        (``vs_rc_*`` → B.1) but no issued side, so an outbound §69/12 supply had
        no tax to carry it into A.2. This adds it: a 0 % sale tax flagged
        ``cssk_control_is_reverse_charge``, which the section resolver routes to
        A.2 for outbound lines.

        Merged into the SK chart the same way ``l10n_sk_vehicle_expense`` adds its
        vehicle taxes.
        """
        additional = self._parse_csv("sk", "account.tax", module="l10n_sk_kv_dph")
        self._deref_account_tags("sk", additional)
        return additional
