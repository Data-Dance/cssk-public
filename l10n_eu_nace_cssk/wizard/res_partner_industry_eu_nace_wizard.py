# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Import NACE Rev. 2.1 and the Czech national subclasses.

OCA's wizard imports NACE Rev. 2 from the EU vocabulary service. The Czech
Republic moved to CZ-NACE 2025 (NACE Rev. 2.1 plus a fifth, national digit)
and Slovakia's register to NACE Rev. 2.1 (no national digit) for 2026, and the
same service publishes Rev. 2.1. So the version is a choice here, records are
kept apart by version, and the 716 CZ-NACE 2025 subclasses are added under
their Rev. 2.1 classes from the Czech Statistical Office's codelist
(``data/cz_nace_2025_subclasses.csv``).
"""

import csv
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import file_path

from ..models.res_partner_industry import nace_digits, nace_dotted

#: The parts of OCA's Rev. 2 query that name the version. A Rev. 2.1 query is
#: the same text with these replaced; if OCA reworded the query, the import
#: stops rather than silently fetching Rev. 2 under a Rev. 2.1 label.
_REV2_MARKERS = (
    ("PREFIX : <http://data.europa.eu/ux2/nace2/>",
     "PREFIX : <http://data.europa.eu/ux2/nace2.1/>"),
    ("skos:inScheme :nace2 ;", "skos:inScheme :nace2.1 ;"),
    ('STRAFTER(?NACELEVEL, "/nace2/")', 'STRAFTER(?NACELEVEL, "/nace2.1/")'),
)

CZ_SUBCLASSES = "l10n_eu_nace_cssk/data/cz_nace_2025_subclasses.csv"


class ResPartnerIndustryEUNaceWizard(models.TransientModel):
    _inherit = "res.partner.industry.eu.nace.wizard"

    nace_version = fields.Selection(
        [("2.1", "NACE Rev. 2.1 (current: CZ-NACE 2025, SK from 2026)"),
         ("2", "NACE Rev. 2 (former)")],
        string="Version", default="2.1", required=True)
    include_cz_subclasses = fields.Boolean(
        string="Czech subclasses (CZ-NACE 2025)", default=True,
        help="Add the 716 national subclasses, the fifth digit of CZ-NACE "
        "2025, under their NACE Rev. 2.1 classes.")
    archive_other_version = fields.Boolean(
        string="Archive the other version", default=True,
        help="Archive the industries of the other NACE version, so the "
        "industry list offers one classification. Partners keep theirs.")

    def _create_query(self, language_list):
        query = super()._create_query(language_list)
        if self.nace_version != "2.1":
            return query
        for rev2, rev21 in _REV2_MARKERS:
            if rev2 not in query:
                raise UserError(_(
                    "The NACE import query of l10n_eu_nace has changed; the "
                    "Rev. 2.1 import needs updating (missing: %s).", rev2))
            query = query.replace(rev2, rev21)
        return query

    def _create_nace_industry(self, nace_data, languages):
        """OCA's import, with the records keyed by version and code rather
        than by the prefix of their name, which two versions share."""
        version = self.nace_version or "2"
        Industry = self.env["res.partner.industry"].with_context(active_test=False)
        bindings = nace_data.json().get("results", {}).get("bindings", [])
        existing = {
            industry.nace_code: industry
            for industry in Industry.search([("nace_version", "=", version),
                                             ("nace_country_id", "=", False)])
        }
        created = Industry.browse()
        for binding in bindings:
            code = binding.get("code", {}).get("value", "")
            digits = nace_digits(code)
            parent = existing.get(nace_digits(binding.get("parentCode", {}).get("value", "")))
            industry = existing.get(digits)
            name = binding.get("EN", {}).get("value") or code
            if not industry:
                industry = Industry.create({
                    "name": name, "full_name": f"{code} - {name}",
                    "parent_id": parent.id if parent else False,
                    "nace_version": version, "nace_code": digits,
                })
                existing[digits] = industry
                created |= industry
            elif not industry.active:
                industry.active = True
            for lang, lang_code in languages:
                translated = binding.get(lang_code, {}).get("value")
                if translated:
                    industry.with_context(lang=lang).write({
                        "name": translated, "full_name": f"{code} - {translated}"})
        if version == "2.1" and self.include_cz_subclasses:
            created |= self._import_cz_subclasses(existing, languages)
        if self.archive_other_version:
            Industry.search([("nace_version", "not in", (False, version)),
                             ("active", "=", True)]).active = False
        return created

    @api.model
    def _cz_subclass_rows(self):
        with open(file_path(CZ_SUBCLASSES), encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def _import_cz_subclasses(self, classes, languages):
        """The fifth digit of CZ-NACE 2025, each under its Rev. 2.1 class. A
        subclass whose class was not imported is left out."""
        Industry = self.env["res.partner.industry"].with_context(active_test=False)
        czech = self.env.ref("base.cz")
        existing = {
            industry.nace_code: industry for industry in Industry.search(
                [("nace_version", "=", "2.1"), ("nace_country_id", "=", czech.id)])
        }
        installed = {lang for lang, _code in languages}
        created = Industry.browse()
        for row in self._cz_subclass_rows():
            parent = classes.get(row["class_code"])
            if not parent or not re.fullmatch(r"\d{5}", row["code"]):
                continue
            label = nace_dotted(row["code"])
            industry = existing.get(row["code"])
            if not industry:
                industry = Industry.create({
                    "name": row["name_en"],
                    "full_name": f"{label} - {row['name_en']}",
                    "parent_id": parent.id, "nace_version": "2.1",
                    "nace_code": row["code"], "nace_country_id": czech.id,
                })
                created |= industry
            elif not industry.active:
                industry.active = True
            for lang, name in (("en_US", row["name_en"]), ("cs_CZ", row["name_cs"])):
                if lang in installed:
                    industry.with_context(lang=lang).write(
                        {"name": name, "full_name": f"{label} - {name}"})
        return created
