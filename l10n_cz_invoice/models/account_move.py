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
        "invoice_line_ids.product_id.type",
        "invoice_line_ids.tax_ids",
        "invoice_line_ids.tax_ids.amount",
        "invoice_line_ids.tax_ids.tax_scope",
        "invoice_line_ids.tax_ids.l10n_cz_invoice_reverse_charge",
        "invoice_line_ids.tax_ids.l10n_cz_invoice_triangular",
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
                goods, services = move._l10n_cz_zero_rated_kinds()
                # honour our own flag and (where another CZ localization is present)
                # its native reverse-charge flag.
                is_rc = any(
                    t.l10n_cz_invoice_reverse_charge
                    or getattr(t, "l10n_cz_reverse_charge", False)
                    for t in taxes
                )
                triangular = any(t.l10n_cz_invoice_triangular for t in taxes)
                if is_rc:
                    notes.append(
                        "Daň odvede zákazník — přenesení daňové povinnosti "
                        "podle §92a zákona o DPH (Reverse charge)."
                    )
                elif pcc and pcc != home and pcc in eu_codes and partner.vat:
                    # Three different supplies, three different texts:
                    # * goods dispatched to another member state are exempt
                    #   (§64), and § 29 odst. 2 písm. a) wants the exemption
                    #   cited;
                    # * a B2B service is supplied where the customer is (§9
                    #   odst. 1) and the customer is liable, so § 29 odst. 2
                    #   písm. c) wants "daň odvede zákazník" — not an exemption;
                    # * the middle person of a triangular trade must state that
                    #   it is one (§ 29 odst. 2 písm. e)) and that the customer
                    #   pays the tax (písm. c)).
                    if triangular:
                        notes.append(
                            "Třístranný obchod — zjednodušený postup, daň "
                            "odvede zákazník (§29 odst. 2 písm. c) a e) zákona "
                            "o DPH; čl. 141 a 197 směrnice 2006/112/ES)."
                        )
                    if goods:
                        notes.append(
                            "Osvobozeno od daně podle §64 zákona o DPH "
                            "(Intra-Community supply of goods)."
                        )
                    if services:
                        notes.append(
                            "Daň odvede zákazník — místo plnění podle §9 "
                            "odst. 1 zákona o DPH (čl. 196 směrnice "
                            "2006/112/ES, Reverse charge)."
                        )
                elif goods and pcc and pcc not in eu_codes:
                    # §66 exempts the export of GOODS; a service to a
                    # customer outside the EU is supplied outside the Czech
                    # Republic and has no exemption to cite.
                    notes.append(
                        "Osvobozeno od daně podle §66 zákona o DPH "
                        "(Exempt — export of goods)."
                    )
            if move.l10n_cz_legal_note_manual:
                notes.append(move.l10n_cz_legal_note_manual)
            move.l10n_cz_legal_notes = "\n".join(notes)

    def _l10n_cz_zero_rated_kinds(self):
        """Return ``(goods, services)``: whether the zero-rated lines include
        a supply of goods and of services.

        Mirrors ``l10n_sk_invoice``. The tax's own scope decides first
        (``l10n_cz`` ships ``0% EU G`` / ``0% EX G`` for goods and
        ``0% EU S`` / ``0% EX S`` for services); a tax without one falls back
        to the product type, and a line with neither counts as goods, which is
        what this note printed before the distinction existed. Taxes marked as
        reverse charge or triangular trade have notes of their own and are not
        counted.
        """
        goods = services = False
        for line in self.invoice_line_ids:
            zero = line.tax_ids.filtered(
                lambda t: t.amount == 0
                and not t.l10n_cz_invoice_triangular
                and not t.l10n_cz_invoice_reverse_charge)
            if not zero:
                continue
            scopes = set(zero.mapped("tax_scope")) - {False}
            if not scopes:
                scopes = {
                    "service" if line.product_id.type == "service" else "consu"}
            goods = goods or "consu" in scopes
            services = services or "service" in scopes
        return goods, services
