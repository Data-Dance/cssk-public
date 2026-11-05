# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    l10n_cssk_sepa_symbol_placement = fields.Selection(
        [
            ("none", "Do not export symbols"),
            ("ustrd", "Remittance info (/VS/…/KS/…/SS/…)"),
            ("end_to_end", "EndToEndId (/VS…/SS…/KS…)"),
        ],
        string="CZ/SK Symbols in SEPA Transfers",
        compute="_compute_l10n_cssk_sepa_symbol_placement",
        store=True,
        readonly=False,
        help="Where the SEPA credit transfer file of a payment order carries "
        "the payment symbols. EndToEndId in the form /VS…/SS…/KS… is what "
        "Slovak banks read; the remittance information is the placement "
        "documented by the Czech Banking Association. Send one test payment "
        "and check how it appears on the payee's statement.",
    )

    @api.depends("company_id.account_fiscal_country_id")
    def _compute_l10n_cssk_sepa_symbol_placement(self):
        for journal in self:
            if journal.l10n_cssk_sepa_symbol_placement:
                continue
            country = journal.company_id.account_fiscal_country_id.code
            journal.l10n_cssk_sepa_symbol_placement = {
                "SK": "end_to_end",
                "CZ": "ustrd",
            }.get(country, "none")
