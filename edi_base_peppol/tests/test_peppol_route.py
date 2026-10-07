"""Which customer documents go out through Peppol, per company."""

import importlib.util
from pathlib import Path

from odoo.tests.common import TransactionCase


class TestPeppolRoute(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sk = cls.env.ref("base.sk")
        cls.cz = cls.env.ref("base.cz")
        cls.company = cls.env["res.company"].create({
            "name": "alfa_sk", "country_id": cls.sk.id,
            "account_fiscal_country_id": cls.sk.id,
            "peppol_send_enabled": True, "peppol_scope": "sk_mandate"})
        cls.company.partner_id.write({
            "peppol_eas": "9950", "peppol_endpoint": "SK2020000004"})

    def _customer(self, country, company=True, vat=False, address=True):
        vals = {"name": "Customer %s" % country.code, "country_id": country.id,
                "is_company": company, "vat": vat}
        if address:
            vals.update({"peppol_eas": "9950", "peppol_endpoint": "SK2021111114"})
        return self.env["res.partner"].create(vals)

    def _route(self, partner, company=None, move_type="out_invoice"):
        move = self.env["account.move"].new({
            "move_type": move_type, "partner_id": partner.id,
            "company_id": (company or self.company).id})
        return move._peppol_route()

    # -- the Slovak mandate ---------------------------------------------
    def test_a_slovak_business_gets_an_e_invoice(self):
        self.assertEqual(self._route(self._customer(self.sk))[0], "peppol")
        self.assertEqual(
            self._route(self._customer(self.sk), move_type="out_refund")[0], "peppol")

    def test_a_consumer_gets_the_pdf(self):
        route, reason = self._route(self._customer(self.sk, company=False))
        self.assertEqual(route, "pdf")
        self.assertIn("B2C", reason)

    def test_a_consumer_with_a_vat_number_is_a_business(self):
        self.assertEqual(
            self._route(self._customer(self.sk, company=False, vat="SK2021111114"))[0],
            "peppol")

    def test_czech_and_other_foreign_customers_get_the_pdf(self):
        self.assertEqual(self._route(self._customer(self.cz))[0], "pdf")
        self.assertEqual(self._route(self._customer(self.env.ref("base.de")))[0], "pdf")

    def test_a_slovak_business_without_an_address_is_blocked(self):
        route, reason = self._route(self._customer(self.sk, address=False))
        self.assertEqual(route, "blocked")
        self.assertIn("no Peppol address", reason)

    def test_the_mandate_needs_a_slovak_company(self):
        self.company.account_fiscal_country_id = self.cz
        self.assertEqual(self._route(self._customer(self.sk))[0], "pdf")

    # -- company settings -----------------------------------------------
    def test_a_company_that_does_not_send_never_does(self):
        beta_cz = self.env["res.company"].create({
            "name": "Beta CZ s.r.o.", "country_id": self.cz.id})
        route, _reason = self._route(self._customer(self.sk), company=beta_cz)
        self.assertEqual(route, "pdf")

    def test_a_company_without_an_address_is_blocked(self):
        self.company.partner_id.peppol_endpoint = False
        self.assertEqual(self._route(self._customer(self.sk))[0], "blocked")

    def test_any_addressable_customer_outside_the_mandate(self):
        self.company.peppol_scope = "addressable"
        self.assertEqual(self._route(self._customer(self.cz))[0], "peppol")
        self.assertEqual(self._route(self._customer(self.cz, address=False))[0], "pdf")

    def test_a_vendor_bill_has_no_route(self):
        self.assertEqual(
            self._route(self._customer(self.sk), move_type="in_invoice"), (False, ""))

    def test_the_purchase_journal_is_the_company_s(self):
        journal = self.env["account.journal"].create({
            "name": "Peppol bills", "code": "PPB", "type": "purchase",
            "company_id": self.company.id})
        self.company.peppol_purchase_journal_id = journal
        self.assertEqual(
            self.env["edi.message"]._peppol_purchase_journal(self.company), journal)

    # -- migration ------------------------------------------------------
    def test_the_migration_keeps_what_was_sending(self):
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("peppol.auto_send", "True")
        silent = self.env["res.company"].create({"name": "No address"})
        self.company.write({"peppol_send_enabled": False, "peppol_auto_send": False})
        path = (Path(__file__).parents[1] / "migrations" / "19.0.1.4.0"
                / "post-migrate.py")
        spec = importlib.util.spec_from_file_location("peppol_migration", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.migrate(self.env.cr, "19.0.1.3.0")
        self.company.invalidate_recordset()
        silent.invalidate_recordset()
        self.assertTrue(self.company.peppol_send_enabled, "it had an address")
        self.assertTrue(self.company.peppol_auto_send)
        self.assertFalse(silent.peppol_send_enabled)
