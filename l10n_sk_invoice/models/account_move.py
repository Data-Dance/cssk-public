# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_sk_legal_note_manual = fields.Text(
        string="Invoice Legal Note (manual)",
        copy=False,
        help="Free-text statutory note printed on the SK invoice in addition "
        "to any auto-detected phrase (e.g. a specific exemption reference).",
    )
    l10n_sk_legal_notes = fields.Text(
        string="SK Statutory Phrases",
        compute="_compute_l10n_sk_legal_notes",
        help="Mandatory §74 phrases printed on the invoice — auto-detected "
        "from the taxes and the customer's country, plus the manual note.",
    )

    @api.depends(
        "move_type",
        "company_id",
        "partner_id",
        "invoice_line_ids.tax_ids",
        "invoice_line_ids.tax_ids.amount",
        "invoice_line_ids.tax_ids.l10n_sk_reverse_charge",
        "l10n_sk_legal_note_manual",
    )
    def _compute_l10n_sk_legal_notes(self):
        eu = self.env.ref("base.europe", raise_if_not_found=False)
        eu_codes = set(eu.country_ids.mapped("code")) if eu else set()
        for move in self:
            notes = []
            home = move.company_id.account_fiscal_country_id.code
            if move.is_sale_document() and home == "SK":
                partner = move.partner_id.commercial_partner_id
                pcc = partner.country_id.code
                taxes = move.invoice_line_ids.tax_ids
                has_zero = any(t.amount == 0 for t in taxes)
                if any(t.l10n_sk_reverse_charge for t in taxes):
                    notes.append(
                        "Prenesenie daňovej povinnosti podľa §69 ods. 12 "
                        "zákona o DPH (Reverse charge)."
                    )
                elif has_zero and pcc and pcc != home and pcc in eu_codes and partner.vat:
                    notes.append(
                        "Dodanie oslobodené od dane podľa §43 zákona o DPH "
                        "(Intra-Community supply, reverse charge)."
                    )
                elif has_zero and pcc and pcc not in eu_codes:
                    notes.append(
                        "Oslobodené od dane podľa §47 zákona o DPH "
                        "(Exempt — export of goods)."
                    )
            if move.l10n_sk_legal_note_manual:
                notes.append(move.l10n_sk_legal_note_manual)
            move.l10n_sk_legal_notes = "\n".join(notes)
