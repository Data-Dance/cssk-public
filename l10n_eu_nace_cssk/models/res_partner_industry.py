# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Which NACE an industry comes from, and its code as data.

OCA's ``l10n_eu_nace`` keeps the code only as the prefix of ``full_name``
(``"62.10 - …"``) and imports NACE Rev. 2, the version the Czech and Slovak
registers left in 2025/2026. Rev. 2 and Rev. 2.1 reuse codes with different
meanings (Rev. 2 ``62.01`` is programming, Rev. 2.1 ``62.10``), so an industry
here carries its version and its code, and a national subclass its country.
"""

import re

from odoo import api, fields, models

#: OCA's full_name: "<code> - <name>", the code a section letter or dotted digits.
_LEGACY_NAME = re.compile(r"^([A-U]|\d{2}(?:\.\d{1,2})?) - ")


def nace_digits(code):
    """``"62.10"`` -> ``"6210"``; a section letter stays a letter."""
    return (code or "").replace(".", "").strip()


def nace_dotted(digits):
    """``"62101"`` -> ``"62.10.1"``, ``"6210"`` -> ``"62.10"``, ``"621"`` -> ``"62.1"``."""
    if len(digits) <= 2 or not digits.isdigit():
        return digits
    return ".".join(filter(None, (digits[:2], digits[2:4], digits[4:])))


class ResPartnerIndustry(models.Model):
    _inherit = "res.partner.industry"

    nace_version = fields.Selection(
        [("2", "NACE Rev. 2"), ("2.1", "NACE Rev. 2.1")],
        string="NACE version", index=True, readonly=True)
    nace_code = fields.Char(
        string="NACE code", index=True, readonly=True,
        help="The code as digits (6210), or the section letter.")
    nace_country_id = fields.Many2one(
        "res.country", string="National subclass of", readonly=True,
        help="Set on a national subclass (the fifth digit), e.g. CZ-NACE.")

    @api.model
    def _nace_tag_legacy_rev2(self):
        """Industries imported by OCA's wizard alone: tag them Rev. 2."""
        untagged = self.with_context(active_test=False).search(
            [("nace_version", "=", False), ("full_name", "!=", False)])
        for industry in untagged:
            match = _LEGACY_NAME.match(industry.full_name or "")
            if match:
                industry.write({"nace_version": "2",
                                "nace_code": nace_digits(match.group(1))})

    @api.model
    def _nace_find(self, code):
        """The industry for a partner's NACE code (digits): the code itself,
        else its class (first four digits); Rev. 2.1 first, the current
        classification in both countries, then Rev. 2."""
        code = nace_digits(code)
        if not code:
            return self.browse()
        candidates = [code] + ([code[:4]] if len(code) > 4 else [])
        for version in ("2.1", "2"):
            for candidate in candidates:
                industry = self.search([
                    ("nace_version", "=", version), ("nace_code", "=", candidate)],
                    limit=1)
                if industry:
                    return industry
        return self.browse()
