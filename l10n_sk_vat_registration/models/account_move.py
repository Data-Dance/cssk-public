# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Warn when a domestic reverse charge is aimed at someone who is not a platiteľ.

§ 69 ods. 12 names a **platiteľ** on both sides of the supply. A customer
registered under § 7 or § 7a holds a VIES-valid IČ DPH and is not one, so
shifting the tax to them is wrong — the supplier owes the SK VAT.

Like ``l10n_cssk_payment_reliability``, this **never blocks**. The register is
an aggregator's copy, the categories move, and refusing to post an invoice on
that basis would be worse than the error it prevents. It warns, and it says why.
"""

from odoo import api, fields, models

NON_PAYER_CATEGORIES = ("7", "7a")


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_sk_vat_registration_warning = fields.Text(
        string="SK VAT registration warning",
        compute="_compute_l10n_sk_vat_registration_warning",
        help="Raised when the customer's VAT-registration paragraph is "
        "inconsistent with how this invoice is taxed.",
    )

    @api.depends(
        "move_type",
        "company_id",
        "partner_id",
        "partner_id.l10n_sk_vat_registration_category",
        "partner_id.country_id",
        "invoice_line_ids.tax_ids",
    )
    def _compute_l10n_sk_vat_registration_warning(self):
        # `l10n_sk_reverse_charge` belongs to l10n_sk_invoice. Detecting it
        # rather than depending on it keeps this module about registration
        # data; with no such flag in the database there is no reliable signal,
        # so the check simply stays quiet.
        has_flag = "l10n_sk_reverse_charge" in self.env["account.tax"]._fields
        for move in self:
            move.l10n_sk_vat_registration_warning = False
            if not has_flag or not move.is_sale_document():
                continue
            if move.company_id.account_fiscal_country_id.code != "SK":
                continue
            partner = move.partner_id.commercial_partner_id
            category = partner.l10n_sk_vat_registration_category
            if category not in NON_PAYER_CATEGORIES:
                continue
            # An unknown country still warns. The category itself is a Slovak
            # registration, so a partner carrying one and no country is far
            # more likely domestic than foreign, and this is a hint rather
            # than a gate.
            if partner.country_id and partner.country_id.code != "SK":
                continue
            if not any(
                tax.l10n_sk_reverse_charge for tax in move.invoice_line_ids.tax_ids
            ):
                continue
            move.l10n_sk_vat_registration_warning = (
                "%s je registrovaný podľa § %s zákona o DPH, teda nie je "
                "platiteľom dane. Prenesenie daňovej povinnosti podľa § 69 "
                "ods. 12 sa na neho nevzťahuje — daň odvádza dodávateľ.\n"
                "(%s is registered under § %s and is not a VAT payer, so the "
                "domestic reverse charge does not apply to them.)"
                % (partner.display_name, category, partner.display_name, category)
            )

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        for move in posted:
            if move.l10n_sk_vat_registration_warning:
                move.message_post(body=move.l10n_sk_vat_registration_warning)
        return posted
