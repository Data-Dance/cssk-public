# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from unittest.mock import patch

from requests.models import Response

from odoo.addons.l10n_eu_nace.wizard.res_partner_industry_eu_nace_wizard import (
    ResPartnerIndustryEUNaceWizard as OcaWizard,
)
from odoo.exceptions import UserError
from odoo.tests import Form, TransactionCase, tagged

MOCK = "odoo.addons.l10n_eu_nace.wizard.res_partner_industry_eu_nace_wizard.requests.get"

# A slice of NACE Rev. 2.1 as the EU vocabulary service returns it.
REV21 = [
    ("K", None, "Telecommunication, computer programming, consulting"),
    ("62", "K", "Computer programming, consultancy and related activities"),
    ("62.1", "62", "Computer programming activities"),
    ("62.10", "62.1", "Computer programming activities"),
]
REV2 = [
    ("J", None, "Information and communication"),
    ("62", "J", "Computer programming, consultancy and related activities"),
    ("62.0", "62", "Computer programming, consultancy and related activities"),
    ("62.01", "62.0", "Computer programming activities"),
]


def _response(rows):
    bindings = []
    for code, parent, name in rows:
        binding = {"code": {"value": code}, "EN": {"value": name}}
        if parent:
            binding["parentCode"] = {"value": parent}
        bindings.append(binding)
    response = Response()
    response.status_code = 200
    response._content = json.dumps({"results": {"bindings": bindings}}).encode()
    return response


@tagged("post_install", "-at_install")
class TestNaceCssk(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Industry = cls.env["res.partner.industry"].with_context(active_test=False)

    def _import(self, rows, **values):
        wizard = Form(self.env["res.partner.industry.eu.nace.wizard"])
        for name, value in values.items():
            setattr(wizard, name, value)
        wizard = wizard.save()
        with patch(MOCK, return_value=_response(rows)) as get:
            wizard.update_partner_industry_eu_nace()
        return get.call_args.kwargs["params"]["query"]

    def _nace(self, code, version="2.1", country=False):
        return self.Industry.search([
            ("nace_version", "=", version), ("nace_code", "=", code),
            ("nace_country_id", "=", country and self.env.ref("base.cz").id)])

    def test_rev21_is_fetched_and_tagged(self):
        query = self._import(REV21)
        self.assertIn("nace2.1", query)
        self.assertNotIn("inScheme :nace2 ;", query)
        programming = self._nace("6210")
        self.assertEqual(programming.full_name, "62.10 - Computer programming activities")
        self.assertEqual(programming.parent_id, self._nace("621"))

    def test_czech_subclasses_hang_under_their_rev21_class(self):
        self._import(REV21)
        games = self._nace("62101", country=True)
        self.assertEqual(games.parent_id, self._nace("6210"))
        self.assertTrue(games.full_name.startswith("62.10.1 - "))
        # Only subclasses whose class was imported: 62101 and 62109 here.
        self.assertEqual(
            len(self.Industry.search([("nace_country_id", "=", self.env.ref("base.cz").id)])), 2)

    def test_versions_do_not_share_records(self):
        self._import(REV2, nace_version="2", archive_other_version=False)
        self._import(REV21, archive_other_version=False)
        self.assertTrue(self._nace("62", "2"))
        self.assertTrue(self._nace("62", "2.1"))
        self.assertNotEqual(self._nace("62", "2"), self._nace("62", "2.1"))

    def test_the_other_version_is_archived(self):
        self._import(REV2, nace_version="2", archive_other_version=False)
        self._import(REV21)
        self.assertFalse(self._nace("6201", "2").active)
        self.assertTrue(self._nace("6210").active)

    def test_industries_imported_before_the_bridge_are_rev2(self):
        legacy = self.env["res.partner.industry"].create({
            "name": "Computer programming activities",
            "full_name": "62.01 - Computer programming activities"})
        plain = self.env["res.partner.industry"].create({
            "name": "Retail", "full_name": "Retail"})
        self.Industry._nace_tag_legacy_rev2()
        self.assertEqual((legacy.nace_version, legacy.nace_code), ("2", "6201"))
        self.assertFalse(plain.nace_version)

    def test_a_partner_s_code_gives_its_industry(self):
        self._import(REV21)
        partner = self.env["res.partner"].create({
            "name": "Hry s.r.o.", "is_company": True, "nace_code": "62101"})
        self.assertEqual(partner.industry_id, self._nace("62101", country=True))
        partner.nace_code = "6210"
        self.assertEqual(partner.industry_id, self._nace("6210"))

    def test_a_chosen_non_nace_industry_is_kept(self):
        self._import(REV21)
        retail = self.env["res.partner.industry"].create({"name": "Retail"})
        partner = self.env["res.partner"].create({
            "name": "Shop", "is_company": True, "industry_id": retail.id})
        partner.nace_code = "62101"
        self.assertEqual(partner.industry_id, retail)

    def test_picking_an_industry_fills_the_code(self):
        self._import(REV21)
        with Form(self.env["res.partner"]) as form:
            form.name = "Firma"
            form.company_type = "company"
            form.industry_id = self._nace("62109", country=True)
            self.assertEqual(form.nace_code, "62109")

    def test_a_reworded_oca_query_stops_the_import(self):
        wizard = self.env["res.partner.industry.eu.nace.wizard"].create({})
        with patch.object(OcaWizard, "_create_query", return_value="SELECT nothing"):
            with self.assertRaises(UserError):
                wizard._create_query([("en_US", "EN")])
