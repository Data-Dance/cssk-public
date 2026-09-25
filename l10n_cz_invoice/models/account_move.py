# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_cz_legal_note_manual = fields.Text(
        string="Invoice Legal Note (manual)",
        copy=False,
        help="Free-text statutory note printed on the CZ invoice in addition "
        "to any auto-detected phrase.",
    )
    l10n_cz_legal_notes = fields.Text(
        string="CZ Statutory Phrases",
        compute="_compute_l10n_cz_legal_notes",
        help="Mandatory invoice phrases auto-detected from the taxes and the "
        "customer's country, plus the manual note.",
    )

    @api.depends(
        "move_type",
        "company_id",
        "partner_id",
        "invoice_line_ids.tax_ids",
        "invoice_line_ids.tax_ids.amount",
        "invoice_line_ids.tax_ids.l10n_cz_invoice_reverse_charge",
        "l10n_cz_legal_note_manual",
    )
    def _compute_l10n_cz_legal_notes(self):
        eu = self.env.ref("base.europe", raise_if_not_found=False)
        eu_codes = set(eu.country_ids.mapped("code")) if eu else set()
        for move in self:
            notes = []
            home = move.company_id.account_fiscal_country_id.code
            if move.is_sale_document() and home == "CZ":
                partner = move.partner_id.commercial_partner_id
                pcc = partner.country_id.code
                taxes = move.invoice_line_ids.tax_ids
                has_zero = any(t.amount == 0 for t in taxes)
                # honour our own flag and (where another CZ localization is present)
                # its native reverse-charge flag.
                is_rc = any(
                    t.l10n_cz_invoice_reverse_charge
                    or getattr(t, "l10n_cz_reverse_charge", False)
                    for t in taxes
                )
                if is_rc:
                    notes.append(
                        "Daň odvede zákazník — přenesení daňové povinnosti "
                        "podle §92a zákona o DPH (Reverse charge)."
                    )
                elif has_zero and pcc and pcc != home and pcc in eu_codes and partner.vat:
                    notes.append(
                        "Osvobozeno od daně podle §64 zákona o DPH "
                        "(Intra-Community supply, reverse charge)."
                    )
                elif has_zero and pcc and pcc not in eu_codes:
                    notes.append(
                        "Osvobozeno od daně podle §66 zákona o DPH "
                        "(Exempt — export of goods)."
                    )
            if move.l10n_cz_legal_note_manual:
                notes.append(move.l10n_cz_legal_note_manual)
            move.l10n_cz_legal_notes = "\n".join(notes)
