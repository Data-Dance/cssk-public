# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models

from odoo.addons.account.models.chart_template import template

# The Slovak závierkové účty, as shipped by l10n_sk with account_type
# 'off_balance'. Odoo forbids mixing an off-balance account with any other in a
# single journal entry (account_move_line._check_off_balance, a hard constrains),
# which makes the classic Czechoslovak closing — trieda 5/6 against 710, súvahové
# účty against 702 — impossible to post as shipped.
#
# They are retyped to 'equity': they are technical accounts that carry
# balance-sheet and result totals, and a matched closing/opening pair nets them
# to zero. This does NOT disturb the statutory outputs, because l10n_sk_fs maps
# rows by account CODE, not by account type. It does make them visible to Odoo's
# own generic balance sheet, which is the price of being able to post the
# závierka at all.
SK_ZAVIERKOVE_UCTY = {
    "chart_sk_701000": "equity",  # Začiatočný účet súvahový
    "chart_sk_702000": "equity",  # Konečný účet súvahový
    "chart_sk_710000": "equity",  # Účet ziskov a strát
}


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("sk", "account.account")
    def _get_sk_zavierka_account(self):
        return {
            xmlid: {"account_type": account_type}
            for xmlid, account_type in SK_ZAVIERKOVE_UCTY.items()
        }
