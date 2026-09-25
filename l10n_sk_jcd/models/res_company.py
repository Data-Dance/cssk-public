# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

# The clearing account the notional import base is posted to (+base and -base, so
# it nets to zero and only the VAT and the duty remain). 379 Iné záväzky is the
# conventional home; the account is a company setting because this is exactly the
# kind of mapping an accountant will want to move.
SK_JCD_CLEARING_ACCOUNT = "chart_sk_379000"


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_sk_jcd_clearing_account_id = fields.Many2one(
        "account.account",
        string="Import clearing account",
        domain="[('company_ids', 'in', id)]",
        help="Zúčtovací účet pre pomyselný základ dane pri dovoze. Základ sa naň "
             "zaúčtuje kladne aj záporne, takže sa vynuluje a reálne zostane len "
             "daň a clo.",
    )
    l10n_sk_jcd_duty_product_id = fields.Many2one(
        "product.product",
        string="Customs duty product",
        domain="[('landed_cost_ok', '=', True)]",
        help="Služobný produkt, cez ktorý sa clo pripočíta k obstarávacej cene "
             "zásob (stock.landed.cost).",
    )
    l10n_sk_jcd_default_regime = fields.Selection(
        [
            ("paid", "Daň zaplatená colnému orgánu (§ 49 ods. 2 písm. d)"),
            ("postponed", "Samozdanenie pri dovoze (§ 84a ods. 3)"),
        ],
        string="Default import VAT regime",
        default="paid",
        help="Or ktorý režim sa má predvyplniť. Nejde o voľbu pre jednotlivú "
             "zásielku — § 84a ods. 3 je podmienený statusom platiteľa.",
    )
    l10n_sk_jcd_is_sk_company = fields.Boolean(
        string="Slovak chart in use (technical)",
        compute="_compute_l10n_sk_jcd_is_sk_company",
        help="Technical — hides the Slovak import settings on other charts.",
    )

    def _compute_l10n_sk_jcd_is_sk_company(self):
        for company in self:
            company.l10n_sk_jcd_is_sk_company = company.chart_template == "sk"
