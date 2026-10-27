# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Tax-office visibility across companies, the closing-journal setting, the
retired registration text, and export warnings a person can actually see."""

import base64
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class TestTaxAuthorityRule(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sk, cz = cls.env.ref("base.sk"), cls.env.ref("base.cz")
        cls.sk_company = cls.env["res.company"].create(
            {"name": "SK co", "country_id": sk.id})
        cls.cz_company = cls.env["res.company"].create(
            {"name": "CZ co", "country_id": cz.id})
        Authority = cls.env["cssk.tax.authority"]
        cls.sk_office = Authority.create({
            "name": "DÚ test SK", "code": "SK-TEST-1",
            "partner_id": cls.env["res.partner"].create(
                {"name": "DÚ test SK", "country_id": sk.id}).id})
        cls.cz_office = Authority.create({
            "name": "FÚ test CZ", "code": "CZ-TEST-1",
            "partner_id": cls.env["res.partner"].create(
                {"name": "FÚ test CZ", "country_id": cz.id}).id})
        cls.user = cls.env["res.users"].with_context(no_reset_password=True).create({
            "name": "CZ+SK accountant", "login": "cssk_cz_sk_accountant",
            "company_id": cls.sk_company.id,
            "company_ids": [(6, 0, (cls.sk_company | cls.cz_company).ids)],
            "group_ids": [(6, 0, [cls.env.ref("base.group_user").id,
                                  cls.env.ref("account.group_account_user").id])],
        })

    def _visible(self, companies):
        env = self.env(user=self.user, context={
            "allowed_company_ids": companies.ids})
        return env["cssk.tax.authority"].search(
            [("id", "in", (self.sk_office | self.cz_office).ids)])

    def test_both_countries_with_both_companies_active(self):
        """The rule read user.company_id — the DEFAULT company — so with a
        Slovak default the Czech offices were invisible even with the Czech
        company active, and its tax authority could not be set."""
        self.assertEqual(self._visible(self.sk_company | self.cz_company),
                         self.sk_office | self.cz_office)
        self.assertEqual(self._visible(self.cz_company), self.cz_office)

    def test_still_one_country_with_one_company_active(self):
        self.assertEqual(self._visible(self.sk_company), self.sk_office)


class TestClosingJournalSetting(TransactionCase):

    def test_closing_journals_are_in_settings(self):
        # The CZ/SK block sits inside account's group_account_user section.
        admin = self.env.ref("base.user_admin")
        admin.group_ids = [(4, self.env.ref("account.group_account_user").id)]
        arch = self.env["res.config.settings"].with_user(admin).get_views(
            [(False, "form")])["views"]["form"]["arch"]
        self.assertIn('name="l10n_cssk_closing_journal_ids"', arch)

    def test_setting_writes_the_company(self):
        company = self.env.company
        journal = self.env["account.journal"].create({
            "name": "UZAVIERKA", "code": "UZTST", "type": "general",
            "company_id": company.id})
        settings = self.env["res.config.settings"].create({
            "l10n_cssk_closing_journal_ids": [(6, 0, journal.ids)]})
        settings.execute()
        self.assertEqual(company.l10n_cssk_closing_journal_ids, journal)


@tagged("post_install", "-at_install")
class TestRegistrationInfoRetired(TransactionCase):
    """post_install: ``trade_registry`` comes from l10n_sk / l10n_cz, which
    load after core."""

    def test_not_on_the_company_form(self):
        arch = self.env["res.company"].get_views(
            [(False, "form")])["views"]["form"]["arch"]
        self.assertNotIn("l10n_cssk_registration_info", arch)

    def test_copied_into_trade_registry_where_empty(self):
        Company = self.env["res.company"]
        if "trade_registry" not in Company._fields:
            self.skipTest("trade_registry needs l10n_sk or l10n_cz")
        empty = Company.create({
            "name": "Empty", "l10n_cssk_registration_info":
                "Spoločnosť zapísaná v OR\nOkresného súdu, vložka 1/B"})
        kept = Company.create({
            "name": "Kept", "trade_registry": "already there",
            "l10n_cssk_registration_info": "other"})
        changed = (empty | kept)._cssk_retire_registration_info()
        self.assertEqual(changed, empty)
        self.assertEqual(empty.trade_registry,
                         "Spoločnosť zapísaná v OR Okresného súdu, vložka 1/B")
        self.assertEqual(kept.trade_registry, "already there")


@tagged("post_install", "-at_install")
class TestExportWarningsReachTheUser(TransactionCase):
    """A non-blocking kontrola used to be written to the server log and
    nowhere else. Run on a real statement: needs l10n_cssk_vat_return_base."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if "cssk.vat.return" not in cls.env:
            cls.skipTest(cls, "needs l10n_cssk_vat_return_base")
        cls.company = cls.env.company
        cls.company.vat = "SK2023456787"
        sk = cls.env.ref("base.sk")
        template = cls.env["ir.ui.view"].create({
            "name": "cssk warnings test", "type": "qweb",
            "arch": "<t t-name='cssk_core_warnings_test'><DPH/></t>"})
        schema = (b'<?xml version="1.0" encoding="UTF-8"?>'
                  b'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                  b'<xs:element name="DPH"/></xs:schema>')
        version = cls.env["cssk.vat.return.version"].create({
            "name": "WRN", "country_id": sk.id, "valid_from": "2025-01-01",
            "xml_template_ref_id": template.id, "xml_root_element": "DPH",
            "xml_schema_filename": "w.xsd",
            "xml_schema_data": base64.b64encode(schema),
            "statement_type_ids": [
                (0, 0, {"code": "R", "name": "Riadny", "fa_xml_value": "R"})],
        })
        cls.ret = cls.env["cssk.vat.return"].create({
            "company_id": cls.company.id, "version_id": version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": version.statement_type_ids[0].id,
        })
        cls.ret.action_compute_lines()

    def _export(self, violations):
        Model = type(self.ret)
        with patch.object(Model, "check_kontroly",
                          lambda self_, *a, **k: list(violations)):
            return self.ret.action_export_xml()

    def test_warning_is_kept_posted_and_notified(self):
        before = len(self.ret.message_ids)
        action = self._export([{"code": "KV_RATE", "desc": "Sadzba",
                                "detail": "21 % mimo zoznamu",
                                "severity": "warning"}])
        self.assertEqual(self.ret.state, "exported")
        self.assertIn("21 % mimo zoznamu", self.ret.cssk_export_warnings)
        self.assertEqual(action["tag"], "display_notification")
        self.assertTrue(action["params"]["sticky"])
        self.assertEqual(action["params"]["next"]["tag"], "soft_reload")
        self.assertIn("21 % mimo zoznamu", action["params"]["message"])
        posted = self.ret.message_ids[:len(self.ret.message_ids) - before]
        self.assertTrue(any("21 % mimo zoznamu" in (m.body or "")
                            for m in posted))

    def test_clean_export_clears_the_warning(self):
        self._export([{"code": "W", "desc": "d", "detail": "x",
                       "severity": "warning"}])
        self.ret.state = "preview"
        self.assertIs(self._export([]), True)
        self.assertFalse(self.ret.cssk_export_warnings)
