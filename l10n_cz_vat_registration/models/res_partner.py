# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""What kind of Czech VAT registration a partner's DIČ belongs to.

A DIČ does not mean the same thing for everyone who holds one. An
**identifikovaná osoba** (§ 6g–6l zákona č. 235/2004 Sb.) — registered because
it acquires goods from another member state, receives a service from a person
not established in the tuzemsko, or supplies a service to another member state
— holds a DIČ that VIES confirms and is *not* a **plátce**. It does not deduct
input VAT, it does not charge VAT on domestic supplies, and the režim
přenesení daňové povinnosti of § 92a cannot shift the tax to it: § 92a odst. 1
makes the *plátce* for whom the supply was made the one who accounts for it.

VIES cannot make that distinction: it answers valid / not valid. The Finanční
správa's register of VAT subjects does, as ``typSubjektu`` of its web service.

The vocabulary follows ``l10n_cz_vat_status`` (``payer`` / ``identified`` /
``non_payer``), which records the same thing for the company itself over
time. ``group`` is added because the register names a skupina separately.
"""

import re

from odoo import api, fields, models

# Registrations that make the holder a plátce. A skupina (§ 5a) comes into
# being by being registered as a plátce (§ 5a odst. 3) and acts as one.
FULL_PAYER_CATEGORIES = ("payer", "group")

VAT_REGISTRATION_CATEGORIES = [
    ("payer", "Plátce (§ 6–6f)"),
    ("group", "Skupina (§ 5a) — plátce"),
    ("identified", "Identifikovaná osoba (§ 6g–6l) — není plátce"),
    ("non_payer", "Neplátce"),
]

# What the register and people write, folded to lower case with single spaces.
# `typSubjektu` of the Finanční správa web service is PLATCE_DPH,
# IDENTIFIKOVANA_OSOBA, SKUPINA_DPH, NENALEZEN or NESPOLEHLIVA_OSOBA. The last
# two are deliberately absent:
#
# * NENALEZEN says the register did not find the DIČ it was asked about. That
#   is as often a mistyped DIČ as a neplátce, so it must not be read as one.
# * A nespolehlivá osoba (§ 106aa) is by definition not a plátce, but whether
#   it is an identifikovaná osoba or not registered at all the register does
#   not say, and the field has no value for "one of the two".
CATEGORY_WORDS = {
    "platce dph": "payer",
    "platce": "payer",
    "plátce dph": "payer",
    "plátce": "payer",
    "skupina dph": "group",
    "skupina": "group",
    "identifikovana osoba": "identified",
    "identifikovaná osoba": "identified",
    "neplatce": "non_payer",
    "neplátce": "non_payer",
}


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_cz_vat_registration_category = fields.Selection(
        selection=VAT_REGISTRATION_CATEGORIES,
        string="Registrace k DPH",
        help="What kind of Czech VAT registration the partner's DIČ belongs "
        "to. An identifikovaná osoba holds a VIES-valid DIČ but is not a "
        "plátce.",
    )
    l10n_cz_vat_payer_since = fields.Date(
        string="Registrace k DPH od",
        help="Date the VAT registration took effect. The Finanční správa "
        "register does not publish it through its web service, so it is "
        "entered by hand.",
    )
    l10n_cz_is_full_vat_payer = fields.Boolean(
        string="Plátce DPH",
        compute="_compute_l10n_cz_is_full_vat_payer",
        store=True,
        help="True for a plátce and for a skupina. False for an "
        "identifikovaná osoba and a neplátce, and unset when the category is "
        "unknown.",
    )

    @api.depends("l10n_cz_vat_registration_category")
    def _compute_l10n_cz_is_full_vat_payer(self):
        for partner in self:
            partner.l10n_cz_is_full_vat_payer = (
                partner.l10n_cz_vat_registration_category in FULL_PAYER_CATEGORIES
            )

    @api.model
    def _l10n_cz_parse_vat_registration_category(self, value):
        """Map a register's subject type onto the selection.

        Accepts the web service's codes (``PLATCE_DPH``), the Czech words
        ("identifikovaná osoba") and the selection's own keys. Anything
        unrecognised returns False rather than guessing — an unknown category
        must read as unknown, never as "not a plátce", because the second is
        an assertion that changes how an invoice is taxed.
        """
        if not value:
            return False
        # Underscores and every kind of space fold to one plain space: the
        # codes use the first, and text copied out of a web page or a PDF
        # carries non-breaking spaces and tabs as often as plain ones.
        token = re.sub(r"[\s _]+", " ", str(value)).strip().lower()
        valid = dict(self._fields["l10n_cz_vat_registration_category"].selection)
        key = token.replace(" ", "_")
        if key in valid:
            return key
        return CATEGORY_WORDS.get(token, False)
