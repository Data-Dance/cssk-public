# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

# 548 Ostatné náklady na hospodársku činnosť — where the non-deductible half of
# the VAT and the non-tax share of the fuel land. Configurable, because a company
# tracking daňovo neuznané náklady on its own analytic account will want its own.
SK_VEHICLE_NONDEDUCTIBLE_ACCOUNT = "chart_sk_548000"

# The § 85n VAT share (50 %, 1. 1. 2026 - 30. 6. 2028) is not a setting: the
# law allows exactly 50 % or, with the ods. 6 records, the ordinary 100 %, and
# it lives in the repartition of the vs_auto_* taxes, the only place the DPH
# return reads it from.
# § 19 ods. 2 písm. l) bod 3 zákona 595/2003 — unaffected by the VAT change.
SK_FUEL_INCOME_RATIO = 80.0


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_sk_fuel_income_ratio = fields.Float(
        string="Fuel tax-expense share (%)",
        default=SK_FUEL_INCOME_RATIO,
        help="§ 19 ods. 2 písm. l) bod 3: paušálne výdavky na spotrebované PHL do "
             "výšky 80 %. Nezmenené zmenou DPH — obidva režimy sú nezávislé.",
    )
    l10n_sk_vehicle_nondeductible_account_id = fields.Many2one(
        "account.account",
        string="Non-deductible vehicle costs",
        domain="[('company_ids', 'in', id)]",
        help="Account for the non-deducted VAT and the non-tax share of the fuel.",
    )
    l10n_sk_vehicle_is_sk_company = fields.Boolean(
        string="Slovak chart in use (technical)",
        compute="_compute_l10n_sk_vehicle_is_sk_company",
    )

    def _compute_l10n_sk_vehicle_is_sk_company(self):
        for company in self:
            company.l10n_sk_vehicle_is_sk_company = company.chart_template == "sk"
