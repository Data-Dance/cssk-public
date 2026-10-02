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
        "invoice_line_ids.product_id.type",
        "invoice_line_ids.tax_ids",
        "invoice_line_ids.tax_ids.amount",
        "invoice_line_ids.tax_ids.tax_scope",
        "invoice_line_ids.tax_ids.l10n_sk_reverse_charge",
        "l10n_sk_legal_note_manual",
    )
    def _compute_l10n_sk_legal_notes(self):
        eu = self.env.ref("base.europe", raise_if_not_found=False)
        eu_codes = set(eu.country_ids.mapped("code")) if eu else set()
        triangular_by_company = {}
        for move in self:
            notes = []
            home = move.company_id.account_fiscal_country_id.code
            if move.is_sale_document() and home == "SK":
                partner = move.partner_id.commercial_partner_id
                pcc = partner.country_id.code
                taxes = move.invoice_line_ids.tax_ids
                company = move.company_id
                if company.id not in triangular_by_company:
                    triangular_by_company[company.id] = self.env[
                        "account.chart.template"
                    ].with_company(company).ref("vy_eu_t", raise_if_not_found=False)
                triangular = triangular_by_company[company.id]
                goods, services = move._l10n_sk_zero_rated_kinds(triangular)
                if any(t.l10n_sk_reverse_charge for t in taxes):
                    notes.append(
                        "Prenesenie daňovej povinnosti podľa §69 ods. 12 "
                        "zákona o DPH (Reverse charge)."
                    )
                elif pcc and pcc != home and pcc in eu_codes and partner.vat:
                    # Goods and services are different supplies: goods are
                    # exempt under §43, a B2B service is taxed in the
                    # customer's state (§15 ods. 1) with the customer liable.
                    # A triangular trade is neither and keeps core's own
                    # article 141 note.
                    if goods:
                        notes.append(
                            "Dodanie oslobodené od dane podľa §43 zákona o DPH "
                            "(Intra-Community supply of goods)."
                        )
                    if services:
                        notes.append(
                            "Prenesenie daňovej povinnosti — miesto dodania "
                            "služby podľa §15 ods. 1 zákona o DPH "
                            "(Reverse charge, services)."
                        )
                elif goods and pcc and pcc not in eu_codes:
                    # §47 exempts the export of GOODS; a service to a
                    # non-EU customer is outside the scope of Slovak VAT and
                    # has no exemption to cite.
                    notes.append(
                        "Oslobodené od dane podľa §47 zákona o DPH "
                        "(Exempt — export of goods)."
                    )
            if move.l10n_sk_legal_note_manual:
                notes.append(move.l10n_sk_legal_note_manual)
            move.l10n_sk_legal_notes = "\n".join(notes)

    def _l10n_sk_zero_rated_kinds(self, triangular=None):
        """Return ``(goods, services)``: whether the zero-rated lines include
        a supply of goods and of services.

        The tax's own scope decides first (``l10n_sk`` ships ``0% EU M`` for
        goods and ``0% EU S`` for services); a tax without one falls back to
        the product type, and a line with neither counts as goods, which is
        what this note printed before the distinction existed.
        """
        goods = services = False
        for line in self.invoice_line_ids:
            zero = line.tax_ids.filtered(
                lambda t: t.amount == 0 and t != triangular)
            if not zero:
                continue
            scopes = set(zero.mapped("tax_scope")) - {False}
            if not scopes:
                scopes = {
                    "service" if line.product_id.type == "service" else "consu"}
            goods = goods or "consu" in scopes
            services = services or "service" in scopes
        return goods, services
