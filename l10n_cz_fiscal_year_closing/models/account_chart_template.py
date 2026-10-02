# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models

from odoo.addons.account.models.chart_template import template

# The Czech závěrkové účty, as shipped by l10n_cz with account_type
# 'off_balance'. Odoo forbids mixing an off-balance account with any other in a
# single journal entry (account_move_line._check_off_balance, a hard
# constraint), which makes the classic Czech closing — třída 5/6 against 710,
# rozvahové účty against 702 — impossible to post as shipped.
#
# They are retyped to 'equity': they are technical accounts carrying
# balance-sheet and result totals, and a matched closing/opening pair nets them
# to zero. This does NOT disturb the statutory outputs, because the CZ
# financial statements map rows by account CODE, not by account type. It does
# make them visible to Odoo's own generic balance sheet, which is the price of
# being able to post the závěrka at all.
#
# Exactly the defect l10n_sk has, and l10n_sk_fiscal_year_closing is this module's mirror.
# Measured on a seven-year Czech import before this module existed: **82
# documents failed** outright, and because the result accounts were then never
# closed, the trial balance was out by **698 169 015** on accounts that net to
# zero in the source. Retyping took the failures to 1 and the difference to
# 2 407 136.
CZ_ZAVERKOVE_UCTY = {
    "chart_cz_701000": "equity",  # Počáteční účet rozvažný
    "chart_cz_702000": "equity",  # Konečný účet rozvažný
    "chart_cz_710000": "equity",  # Účet zisků a ztrát
}


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("cz", "account.account")
    def _get_cz_zaverka_account(self):
        return {
            xmlid: {"account_type": account_type}
            for xmlid, account_type in CZ_ZAVERKOVE_UCTY.items()
        }
