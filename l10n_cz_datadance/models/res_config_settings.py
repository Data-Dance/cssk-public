# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_currency_rate_update_cz = fields.Boolean(
        string="ČNB exchange-rate sync"
    )
    module_l10n_cz_account_cutoff = fields.Boolean(
        string="Časové rozlišení (deferrals)"
    )
    module_l10n_cz_payment_reliability = fields.Boolean(
        string="Supplier reliability check (ADIS — verify before paying)"
    )
    module_l10n_cz_account_asset_tax = fields.Boolean(
        string="Dual tax/accounting depreciation"
    )
    module_l10n_cz_stock_account_method_a = fields.Boolean(
        string="Method A perpetual inventory"
    )
    module_l10n_cz_sale_order_advance_invoice = fields.Boolean(
        string="Advance invoices (zálohové faktury)"
    )

    # The annual filings. Moved out of `depends` on 2026-08-27: both are
    # delivered to subscribers rather than published, so a hard dependency
    # would have made this whole bundle uninstallable from the public
    # repository. A toggle is safe when the module is absent —
    # `res.config.settings` resolves `module_<name>` through
    # `ir.module.module._get()`, which returns an empty recordset rather than
    # raising, so the switch is inert. Odoo core uses the same mechanism to
    # advertise Enterprise modules from Community.
    module_l10n_cz_fs = fields.Boolean(
        string="Účetní závěrka — Rozvaha a Výkaz zisku a ztráty"
    )
    module_l10n_cz_dppo = fields.Boolean(
        string="Přiznání k dani z příjmů právnických osob (DPPDP9)"
    )
