# Copyright 2026 Data Dance s.r.o.
# Data Dance Proprietary License v1.0 — see the LICENSE file.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Optional Slovak localization pieces — ticking installs the module.
    module_currency_rate_update_sk = fields.Boolean(
        string="NBS/ECB exchange-rate sync"
    )
    module_l10n_sk_account_cutoff = fields.Boolean(
        string="Časové rozlíšenie (deferrals)"
    )
    module_l10n_sk_payment_reliability = fields.Boolean(
        string="Supplier reliability check (verify before paying)"
    )
    module_l10n_sk_account_asset_tax = fields.Boolean(
        string="Dual tax/accounting depreciation"
    )
    module_l10n_sk_stock_account_method_a = fields.Boolean(
        string="Method A perpetual inventory"
    )
    module_l10n_sk_sale_order_advance_invoice = fields.Boolean(
        string="Advance invoices (zálohové faktúry)"
    )

    # Added 2026-08-08. NOTE THE LICENCE RULE BEFORE MOVING ANY OF THESE INTO
    # `depends`: every hard dependency of this umbrella is "Other proprietary",
    # and every AGPL module is reached through a toggle instead. AGPL is viral
    # over network use, so hard-depending on one would relicense the whole
    # proprietary bundle. A toggle installs the module into the customer's
    # database without this module depending on it.
    module_l10n_sk_account_move_template = fields.Boolean(
        string="Predkontácie (účtovné vzory)"            # AGPL — must stay a toggle
    )
    module_l10n_sk_fiscal_year_closing = fields.Boolean(
        string="Účtovná závierka (701/702/710)"           # AGPL — must stay a toggle
    )
    module_l10n_sk_account_loan_oca = fields.Boolean(
        string="Finančný prenájom / lízing"               # AGPL — must stay a toggle
    )
    module_l10n_sk_asset_protocol_oca = fields.Boolean(
        string="Protokoly o zaradení a vyradení majetku"  # AGPL — must stay a toggle
    )
    module_l10n_sk_mis_reports = fields.Boolean(
        string="Manažérske výkazy (MIS Builder)"          # AGPL — must stay a toggle
    )
    module_l10n_sk_jcd = fields.Boolean(
        string="Dovoz tovaru (JCD)"
    )
    module_l10n_sk_vehicle_expense = fields.Boolean(
        string="Vozidlá a PHL (§ 85n, § 19 ods. 2 písm. l)"
    )
    module_account_invoice_ai_extract = fields.Boolean(
        string="Vyťažovanie došlých faktúr (AI)"
    )
