# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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

    # NOTE THE RULE BEFORE MOVING ANY OF THESE INTO `depends`. It changed on
    # 2026-08-27 and now runs the other way round.
    #
    # This umbrella is AGPL-3 and PUBLISHED, so an AGPL dependency is no longer
    # a problem — the earlier note here said the opposite, because the bundle
    # used to be proprietary and a hard AGPL dependency would have relicensed
    # it. What must stay a toggle now is anything NOT published: a hard
    # dependency on a module the public repository does not ship makes this
    # module uninstallable for everyone outside a subscription.
    #
    # A toggle is safe either way. `res.config.settings` resolves a
    # `module_<name>` field through `ir.module.module._get()`, which returns an
    # empty recordset when the module is absent from the addons path, so the
    # switch is simply inert rather than an error. Odoo core relies on exactly
    # this to advertise Enterprise modules from Community — see
    # `module_account_batch_payment` in `addons/account`.
    module_l10n_sk_account_move_template = fields.Boolean(
        # Deliberately NOT called "Predkontácie": in POHODA / ABRA that word means
        # a preset chosen ON a document, which this is not. See the module README.
        string="Účtovné vzory pre interné doklady"     # AGPL — must stay a toggle
    )
    module_l10n_sk_fiscal_year_closing = fields.Boolean(
        string="Účtovná závierka (701/702/710)"         # AGPL — must stay a toggle
    )
    module_l10n_sk_account_loan_oca = fields.Boolean(
        string="Finančný prenájom / lízing"             # AGPL — must stay a toggle
    )
    module_l10n_sk_asset_protocol_oca = fields.Boolean(
        string="Protokoly o zaradení a vyradení majetku"  # AGPL — must stay a toggle
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
    module_l10n_sk_mis_reports = fields.Boolean(
        string="Manažérske výkazy (MIS Builder)"
    )

    # The annual filings. Moved out of `depends` on 2026-08-27: both are
    # delivered to subscribers rather than published, so a hard dependency
    # would have made this whole bundle uninstallable from the public
    # repository. Subscribers have them in the addons path and the toggle
    # installs them as before.
    module_l10n_sk_fs = fields.Boolean(
        string="Účtovná závierka — Súvaha a Výkaz ziskov a strát"
    )
    module_l10n_sk_dppo = fields.Boolean(
        string="Daňové priznanie k dani z príjmov právnických osôb (DPPO)"
    )
