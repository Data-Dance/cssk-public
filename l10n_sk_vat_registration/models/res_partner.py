# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Which paragraph of the SK VAT Act a partner's IČ DPH was issued under.

An IČ DPH does not mean the same thing for everyone who holds one. A subject
registered under **§ 7** (acquisition of goods from another member state) or
**§ 7a** (receipt or supply of a service across the border) gets a valid IČ DPH
that VIES confirms — and is *not* a **platiteľ dane**. They do not deduct input
VAT, they do not charge VAT on domestic supplies, and § 69 ods. 12 domestic
reverse charge cannot apply to them, because that provision names a platiteľ on
both sides.

VIES cannot make that distinction: it answers valid / not valid. The paragraph
is in the Finančná správa registration record, which ORSF republishes as
``vatRegistration.druhReg``.
"""

import re

from odoo import api, fields, models

# Registrations that make the holder a platiteľ dane. § 7 and § 7a deliberately
# are not among them — that is the entire point of the field.
FULL_PAYER_CATEGORIES = ("4", "4b", "5", "6")


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_sk_vat_registration_category = fields.Selection(
        selection=[
            ("4", "§ 4 — platiteľ dane"),
            ("4b", "§ 4b — skupinová registrácia"),
            ("5", "§ 5 — zahraničná osoba"),
            ("6", "§ 6 — zásielkový predaj"),
            ("7", "§ 7 — nadobudnutie tovaru z EÚ (nie platiteľ)"),
            ("7a", "§ 7a — dodanie/prijatie služby (nie platiteľ)"),
        ],
        string="Druh registrácie DPH",
        help="The paragraph of the SK VAT Act the partner's IČ DPH was issued "
        "under. § 7 and § 7a registrants hold a VIES-valid IČ DPH but are not "
        "platitelia dane.",
    )
    l10n_sk_vat_payer_since = fields.Date(
        string="Platiteľ DPH od",
        help="Date the VAT registration took effect, per the Finančná správa "
        "record.",
    )
    l10n_sk_is_full_vat_payer = fields.Boolean(
        string="Platiteľ dane",
        compute="_compute_l10n_sk_is_full_vat_payer",
        store=True,
        help="True for a registration under § 4 / § 4b / § 5 / § 6. False for "
        "§ 7 and § 7a, and unset when the category is unknown.",
    )

    @api.depends("l10n_sk_vat_registration_category")
    def _compute_l10n_sk_is_full_vat_payer(self):
        for partner in self:
            partner.l10n_sk_is_full_vat_payer = (
                partner.l10n_sk_vat_registration_category in FULL_PAYER_CATEGORIES
            )

    @api.model
    def _l10n_sk_parse_vat_registration_category(self, value):
        """Map a register's ``druhReg`` string onto the selection.

        The Finančná správa writes it as "§4", "§ 7a", "7A" and other near
        misses depending on the route it travelled. Anything unrecognised
        returns False rather than guessing — an unknown category must read as
        unknown, never as "not a platiteľ", because the second is an assertion
        that changes how an invoice is taxed.
        """
        if not value:
            return False
        # Strip every kind of space, not just U+0020: these strings arrive via
        # HTML and PDF scrapes on the way out of the Finančná správa and carry
        # non-breaking spaces and tabs as often as plain ones.
        token = re.sub(r"[\s\u00a0]+", "", str(value).replace("§", "")).lower()
        valid = dict(
            self._fields["l10n_sk_vat_registration_category"].selection
        )
        return token if token in valid else False
