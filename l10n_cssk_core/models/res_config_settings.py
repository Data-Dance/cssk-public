from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_cssk_tax_authority_id = fields.Many2one(
        related="company_id.l10n_cssk_tax_authority_id",
        readonly=False,
        string="Default Tax Authority",
    )

    # True on Enterprise (account_accountant / account_reports installed). Used
    # to hide Community-only options (e.g. account_usability) that are redundant
    # or duplicate Enterprise's own menus.
    l10n_cssk_is_enterprise = fields.Boolean(
        compute="_compute_l10n_cssk_is_enterprise",
    )

    @api.depends_context("uid")
    def _compute_l10n_cssk_is_enterprise(self):
        ee = bool(
            self.env["ir.module.module"]
            .sudo()
            .search_count(
                [
                    ("name", "in", ("account_accountant", "account_reports")),
                    ("state", "=", "installed"),
                ]
            )
        )
        for rec in self:
            rec.l10n_cssk_is_enterprise = ee

    # ``module_`` convention: ticking this installs the OCA account_usability
    # module, unticking uninstalls it (handled by res.config.settings.set_values).
    # Lets Community databases opt into the extra accounting menus Enterprise
    # ships, without a hard dependency that would clash on Enterprise.
    module_account_usability = fields.Boolean(
        string="Extra accounting menus (Community)",
        help="Install OCA account_usability — adds the accounting menus and "
        "report shortcuts Odoo Enterprise provides (general ledger, journals, "
        "aged balances, closing entries…). Recommended on Community editions.",
    )

    # OCA account_financial_report — the Community counterpart of Enterprise's
    # dynamic account_reports (General Ledger, Trial Balance, Partner Ledger,
    # Aged Balance, Journal Ledger). Hidden on EE (which ships its own).
    module_account_financial_report = fields.Boolean(
        string="Financial reports (Community)",
        help="Install OCA account_financial_report — General Ledger, Trial "
        "Balance, Partner Ledger, Aged Partner Balance and Journal Ledger, the "
        "reports Enterprise provides natively. Recommended on Community.",
    )
