# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_cssk_garnishment_journal_id = fields.Many2one(
        "account.journal",
        "Garnishment Remittance Journal",
        domain="[('type', '=', 'general')]",
        check_company=True,
        help="Journal the remittance entries are booked in. Usually the same "
        "general journal the payroll entries use.",
    )
    l10n_cssk_garnishment_account_id = fields.Many2one(
        "account.account",
        "Garnishment Liability Account",
        check_company=True,
        help="Account the payroll entry credits for wage garnishments — the "
        "collective liability (typically 379xxx). Remitting moves the balance "
        "from here onto the individual bailiff's payable, where the payment "
        "order can pick it up.",
    )


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_cssk_garnishment_journal_id = fields.Many2one(
        related="company_id.l10n_cssk_garnishment_journal_id", readonly=False
    )
    l10n_cssk_garnishment_account_id = fields.Many2one(
        related="company_id.l10n_cssk_garnishment_account_id", readonly=False
    )
