"""Which customer documents go out through Peppol, per company."""

import importlib.util
from pathlib import Path
from unittest.mock import patch

from odoo.tests import tagged
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
            "vat": "SK2020000004",
            "peppol_eas": "9950", "peppol_endpoint": "SK2020000004"})
        # With several transports installed one must be chosen, or nothing
        # is routed to Peppol at all (tested below).
        transports = cls.env["account.move"]._peppol_transports()
        if transports:
            cls.env["ir.config_parameter"].sudo().set_param(
                "peppol.transport", transports[0])

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

    def test_a_sole_trader_without_vat_is_a_business(self):
        """§ 85o ods. 3: a taxable person, VAT-registered or not. A natural
        person with an IČO is a sole trader, not a consumer."""
        trader = self._customer(self.sk, company=False)
        trader.company_registry = "12345678"
        self.assertEqual(self._route(trader)[0], "peppol")
        self.assertFalse(
            self._customer(self.sk, company=False)._peppol_is_sk_business())

    def test_the_mandate_binds_a_vat_payer(self):
        self.company.partner_id.vat = False
        route, reason = self._route(self._customer(self.sk))
        self.assertEqual(route, "pdf")
        self.assertIn("§ 85o", reason)

    def test_several_transports_need_a_choice(self):
        Move = type(self.env["account.move"])
        customer = self._customer(self.sk)
        with patch.object(Move, "_peppol_transports",
                          lambda self: ["editel", "grit"]):
            ICP = self.env["ir.config_parameter"].sudo()
            ICP.set_param("peppol.transport", False)
            route, reason = self._route(customer)
            self.assertEqual(route, "blocked")
            self.assertIn("Peppol Transport", reason)
            ICP.set_param("peppol.transport", "grit")
            self.assertEqual(self._route(customer)[0], "peppol")
            self.assertEqual(
                self.env["account.move"]._peppol_chosen_transport(), "grit")
            ICP.set_param("peppol.transport", "nonexistent")
            self.assertFalse(self.env["account.move"]._peppol_chosen_transport())
        with patch.object(Move, "_peppol_transports", lambda self: ["grit"]):
            self.assertEqual(
                self.env["account.move"]._peppol_chosen_transport(), "grit",
                "a single transport is used whatever the setting says")

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
        # The migration writes in SQL, so this state has to be in the database
        # first: left in the cache, the migration's closing invalidate_all()
        # flushed it OVER the migrated values and the test failed on every run.
        self.env.flush_all()
        path =(Path(__file__).parents[1] / "migrations" / "19.0.1.4.0"
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


@tagged("post_install", "-at_install")
class TestPeppolTransports(TransactionCase):
    """After every module is loaded, so the installed transports are there."""

    def test_every_transport_honours_the_setting(self):
        """No transport claims Peppol unless it is the chosen one — Editel
        used to claim it always, so with Editel loaded last the setting was
        ignored. Each module's own override is called, so the test does not
        depend on the order the modules load in."""
        Move = self.env["account.move"]
        ICP = self.env["ir.config_parameter"].sudo()
        overrides = [
            cls for cls in type(Move).mro()
            if "_peppol_provider" in vars(cls)
            and cls.__module__.startswith("odoo.addons.edi_")
            and not cls.__module__.startswith("odoo.addons.edi_base_peppol")
        ]
        for key in Move._peppol_transports():
            ICP.set_param("peppol.transport", key)
            self.assertEqual(Move._peppol_provider(), key)
            for cls in overrides:
                self.assertIn(
                    cls._peppol_provider(Move), (key, False),
                    "%s claims Peppol while %s is chosen" % (cls.__module__, key))
