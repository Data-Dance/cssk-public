# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Where the IČO is on the partner form, and the person types behind
*Entity Type*.

The form carries up to four ``company_registry`` fields: core's in
Sales & Purchase > Misc, this module's beside the VAT number, and one each
from Odoo's l10n_sk / l10n_cz where they are installed. Each has its own
``invisible`` rule, and the rules only work together. What is pinned is
therefore the outcome, whichever of those modules the database has: a Czech
or Slovak partner shows the number exactly once, and at the top.

Found on 2026-11-24 on a Slovak database without l10n_cz: a Czech customer's
IČO was only in the Misc group of a tab, and read as missing.
"""
from lxml import etree

from odoo.tests.common import TransactionCase, tagged
from odoo.tools.safe_eval import safe_eval


@tagged("post_install", "-at_install")
class TestPartnerFormRegistry(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sk = cls.env.ref("base.sk")
        cls.cz = cls.env.ref("base.cz")
        cls.de = cls.env.ref("base.de")
        view = cls.env.ref("base.view_partner_form")
        arch = cls.env["res.partner"].get_view(view.id, "form")["arch"]
        cls.nodes = etree.fromstring(arch).xpath(
            "//field[@name='company_registry'][not(ancestor::field)]")

    def _shown(self, partner):
        """(at the top, in Misc): how many copies this partner shows."""
        values = {
            "parent_id": partner.parent_id.id,
            "is_company": partner.is_company,
            "country_code": partner.country_code,
            "l10n_cssk_registry_by_country_view":
                partner.l10n_cssk_registry_by_country_view,
        }
        top = misc = 0
        for node in self.nodes:
            if safe_eval(node.get("invisible") or "False", dict(values)):
                continue
            if node.xpath("ancestor::group[@name='misc']"):
                misc += 1
            else:
                top += 1
        return top, misc

    def _partner(self, **vals):
        return self.env["res.partner"].create({"name": "Form test", **vals})

    def test_the_form_has_a_copy_outside_misc(self):
        self.assertGreaterEqual(len(self.nodes), 2)

    def test_czech_and_slovak_partners_show_it_once_at_the_top(self):
        for country in (self.cz, self.sk):
            for is_company in (True, False):
                partner = self._partner(
                    country_id=country.id, is_company=is_company)
                self.assertEqual(
                    self._shown(partner), (1, 0),
                    "%s, is_company=%s" % (country.code, is_company))

    def test_a_contact_of_a_czech_company_shows_it_too(self):
        company = self._partner(country_id=self.cz.id, is_company=True)
        contact = self._partner(country_id=self.cz.id, parent_id=company.id)
        self.assertEqual(self._shown(contact), (1, 0))

    def test_a_contact_cannot_edit_the_companys_number(self):
        ours = [
            node for node in self.nodes
            if "l10n_cssk_registry_by_country_view" in (node.get("invisible") or "")
            and not node.xpath("ancestor::group[@name='misc']")
        ]
        self.assertEqual(len(ours), 1)
        self.assertEqual(ours[0].get("readonly"), "parent_id")

    def test_other_countries_keep_cores_behaviour(self):
        company = self._partner(country_id=self.de.id, is_company=True)
        self.assertEqual(self._shown(company), (0, 1))
        person = self._partner(country_id=self.de.id, is_company=False)
        self.assertEqual(self._shown(person), (0, 0))
        self.assertEqual(self._shown(self._partner(is_company=True)), (0, 1))


class TestPersonTypes(TransactionCase):
    def test_both_countries_are_seeded_by_the_core(self):
        """Not by the country modules: a Slovak database has Czech customers
        whether or not it has l10n_cz_statutory."""
        for xmlid, country_code, legal in (
            ("sk_person_type_fo", "SK", False),
            ("sk_person_type_po", "SK", True),
            ("cz_person_type_fo", "CZ", False),
            ("cz_person_type_po", "CZ", True),
        ):
            record = self.env.ref("l10n_cssk_core." + xmlid)
            self.assertEqual(record.country_code, country_code)
            self.assertEqual(record.is_legal_entity, legal)

    def test_the_type_of_a_subject(self):
        Type = self.env["cssk.person.type"]
        self.assertEqual(Type._cssk_for_subject("CZ", True).code, "CZ-FO")
        self.assertEqual(Type._cssk_for_subject("cz", False).code, "CZ-PO")
        self.assertEqual(Type._cssk_for_subject("SK", True).code, "SK-FO")
        self.assertEqual(Type._cssk_for_subject("SK", False).code, "SK-PO")

    def test_no_type_outside_the_two_countries(self):
        Type = self.env["cssk.person.type"]
        self.assertFalse(Type._cssk_for_subject("DE", True))
        self.assertFalse(Type._cssk_for_subject(False, False))
