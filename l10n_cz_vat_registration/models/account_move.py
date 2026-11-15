# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Warn when a domestic reverse charge is aimed at someone who is not a plátce.

In the režim přenesení daňové povinnosti it is "plátce, pro kterého bylo
zdanitelné plnění s místem plnění v tuzemsku uskutečněno" who accounts for the
tax (§ 92a odst. 1 zákona č. 235/2004 Sb.). A customer who is an
identifikovaná osoba holds a VIES-valid DIČ and is not a plátce, and a
neplátce is not one either, so shifting the tax to them is wrong — the
supplier owes the Czech VAT.

Like ``l10n_cssk_payment_reliability``, this **never blocks**. The category is
a copy of a register, registrations change, and refusing to post an invoice on
that basis would be worse than the error it prevents. It warns, and it says
why.
"""

from odoo import api, fields, models

NON_PAYER_CATEGORIES = ("identified", "non_payer")

#: Per-tax "this is a § 92a supply" flags of modules this one does not depend
#: on: ``l10n_cz_invoice``'s, and the same-purpose field of another Czech
#: localization that ``l10n_cz_invoice`` honours too.
REVERSE_CHARGE_FLAGS = ("l10n_cz_invoice_reverse_charge", "l10n_cz_reverse_charge")

#: Row 25 of the Czech VAT return — "Režim přenesení daňové povinnosti (§ 92a)
#: – dodavatel zboží nebo poskytovatel služeb". ``l10n_cz`` tags the base of
#: its own domestic reverse-charge sale tax with it.
REVERSE_CHARGE_TAG = "VAT 25"

WARNINGS = {
    "identified": (
        "%(name)s je identifikovanou osobou (§ 6g–6l zákona o DPH), tedy není "
        "plátcem. V režimu přenesení daňové povinnosti přiznává daň jen "
        "příjemce, který je plátcem (§ 92a odst. 1) — zde daň přiznává "
        "dodavatel.\n"
        "(%(name)s is an identifikovaná osoba and not a VAT payer, so the "
        "domestic reverse charge does not apply to them.)"
    ),
    "non_payer": (
        "%(name)s není plátcem DPH. V režimu přenesení daňové povinnosti "
        "přiznává daň jen příjemce, který je plátcem (§ 92a odst. 1) — zde "
        "daň přiznává dodavatel.\n"
        "(%(name)s is not a VAT payer, so the domestic reverse charge does "
        "not apply to them.)"
    ),
}


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_cz_vat_registration_warning = fields.Text(
        string="CZ VAT registration warning",
        compute="_compute_l10n_cz_vat_registration_warning",
        help="Raised when the customer's kind of VAT registration is "
        "inconsistent with how this invoice is taxed.",
    )

    def _l10n_cz_reverse_charge_taxes(self, taxes):
        """The taxes among ``taxes`` that mark a § 92a domestic supply.

        Two signals, either of which is enough: a per-tax flag of a module
        that may or may not be installed, and the row 25 tag on the tax's base
        repartition, which is how the return itself knows the supply. A tax
        with neither says nothing, and neither does this.
        """
        flags = [f for f in REVERSE_CHARGE_FLAGS if f in taxes._fields]
        cz = self.env.ref("base.cz", raise_if_not_found=False)
        tags = (
            self.env["account.account.tag"]._get_tax_tags(REVERSE_CHARGE_TAG, cz.id)
            if cz
            else self.env["account.account.tag"]
        )

        def is_reverse_charge(tax):
            if any(tax[flag] for flag in flags):
                return True
            base_lines = (
                tax.invoice_repartition_line_ids | tax.refund_repartition_line_ids
            ).filtered(lambda line: line.repartition_type == "base")
            return bool(tags & base_lines.tag_ids)

        return taxes.filtered(is_reverse_charge)

    @api.depends(
        "move_type",
        "company_id",
        "partner_id",
        "partner_id.l10n_cz_vat_registration_category",
        "partner_id.country_id",
        "invoice_line_ids.tax_ids",
    )
    def _compute_l10n_cz_vat_registration_warning(self):
        for move in self:
            move.l10n_cz_vat_registration_warning = False
            if not move.is_sale_document():
                continue
            if move.company_id.account_fiscal_country_id.code != "CZ":
                continue
            partner = move.partner_id.commercial_partner_id
            category = partner.l10n_cz_vat_registration_category
            if category not in NON_PAYER_CATEGORIES:
                continue
            # An unknown country still warns. The category itself is a Czech
            # registration, so a partner carrying one and no country is far
            # more likely domestic than foreign, and this is a hint rather
            # than a gate.
            if partner.country_id and partner.country_id.code != "CZ":
                continue
            if not move._l10n_cz_reverse_charge_taxes(move.invoice_line_ids.tax_ids):
                continue
            move.l10n_cz_vat_registration_warning = WARNINGS[category] % {
                "name": partner.display_name
            }

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        for move in posted:
            if move.l10n_cz_vat_registration_warning:
                move.message_post(body=move.l10n_cz_vat_registration_warning)
        return posted
