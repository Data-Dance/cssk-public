# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The partner's main economic activity, as the code a register or a form uses.

One field for every country: the national classifications (CZ-NACE, SK NACE)
are EU NACE plus national digits, and a partner has one country, which says
which variant its code is in. Only the code is kept, digits without dots
(``35110``, not ``35.11.0``), because that is what registers return and forms
ask for. A readable, hierarchical industry is another question; see the
``partner_nace_industry`` bridge to OCA's ``l10n_eu_nace``.
"""

import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


def normalize_nace(value):
    """``"62.01"`` / ``"62 01 0"`` -> ``"62010"``-style digits; falsy stays falsy."""
    return re.sub(r"\D", "", value) if value else value


class ResPartner(models.Model):
    _inherit = "res.partner"

    nace_code = fields.Char(
        string="NACE (main activity)",
        index="btree_not_null",
        help="Code of the partner's prevailing economic activity in its "
        "country's NACE classification, digits only: CZ-NACE 2025 in the "
        "Czech Republic (up to five digits), NACE Rev. 2.1 / SK NACE in "
        "Slovakia. Filled from the business register where the partner "
        "autocomplete supports it.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("nace_code"):
                vals["nace_code"] = normalize_nace(vals["nace_code"])
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("nace_code"):
            vals = dict(vals, nace_code=normalize_nace(vals["nace_code"]))
        return super().write(vals)

    @api.constrains("nace_code")
    def _check_nace_code(self):
        for partner in self.filtered("nace_code"):
            if not re.fullmatch(r"\d{2,6}", partner.nace_code):
                raise ValidationError(_(
                    "%s: a NACE code is two to six digits (e.g. 62010 or 4719).",
                    partner.display_name))

    @api.model
    def _commercial_fields(self):
        # The activity belongs to the legal entity, like its VAT number.
        return super()._commercial_fields() + ["nace_code"]
