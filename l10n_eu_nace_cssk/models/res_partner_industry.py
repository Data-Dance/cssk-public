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
    def _nace_find(self, code, country_code=None):
        """The industry for a partner's NACE code (digits): the code itself,
        else its class (first four digits).

        Which version a code is in depends on the partner's country and the
        code's length, because Rev. 2 and Rev. 2.1 reuse codes with other
        meanings:

        * **SK, five digits** — SK NACE Rev. 2 (vyhláška 306/2007), which the
          Slovak register keeps in parallel until 31. 12. 2028. Slovakia's
          Rev. 2.1 has no national fifth digit, so a five-digit Slovak code
          is never Rev. 2.1, and it is looked up in Rev. 2 **only**: falling
          back to the Rev. 2.1 class with the same digits would give it an
          industry with another meaning. Trying Rev. 2.1 first did exactly
          that.
        * anything else — Rev. 2.1 first (CZ-NACE 2025 in the Czech Republic,
          the current classification in Slovakia), then Rev. 2.

        A national subclass is matched only for the partner's own country.
        """
        code = nace_digits(code)
        if not code:
            return self.browse()
        candidates = [code] + ([code[:4]] if len(code) > 4 else [])
        if country_code == "SK" and len(code) == 5:
            versions = ("2",)
        else:
            versions = ("2.1", "2")
        country = country_code and self.env["res.country"].search(
            [("code", "=", country_code)], limit=1)
        for version in versions:
            for candidate in candidates:
                domain = [("nace_version", "=", version), ("nace_code", "=", candidate)]
                if len(candidate) > 4 and country:
                    domain.append(("nace_country_id", "in", [False, country.id]))
                # A Slovak Rev. 2 code stays Rev. 2 even after the import of
                # Rev. 2.1 archived that version: an archived industry with
                # the right meaning beats an active one with the wrong one.
                searcher = self.with_context(active_test=False) if versions == ("2",) else self
                industry = searcher.search(domain, limit=1, order="active desc, id")
                if industry:
                    return industry
        return self.browse()
