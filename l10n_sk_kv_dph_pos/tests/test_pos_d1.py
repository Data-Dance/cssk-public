# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from lxml import etree

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestPosD1(AccountTestInvoicingCommon):
    """A POS session's closing entry is eKasa turnover: KV DPH D.1."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write({
            "vat": "SK2023456787", "city": "Bratislava",
            "country_id": cls.env.ref("base.sk").id,
        })
        cls.version = cls.env.ref("l10n_sk_kv_dph.kvdph_version_2025v1")
        Tax = cls.env["account.tax"]
        cls.tax_basic = cls.tax_sale_a
        cls.tax_reduced = Tax.search([
            ("company_id", "=", cls.company.id), ("type_tax_use", "=", "sale"),
            ("amount_type", "=", "percent"), ("amount", ">", 0.0),
            ("amount", "<", 20.0)], limit=1)
        cls.income = cls.company_data["default_account_revenue"]
        cls.cash = cls.company_data["default_journal_cash"].default_account_id
        cls.config = cls.env["pos.config"].sudo().create({"name": "Predajňa"})

    def _session_entry(self, lines, session=True):
        """A closing entry shaped like the one a POS session posts:
        a sales-journal entry, no partner, income lines carrying the tax."""
        total = 0.0
        vals = []
        for amount, tax in lines:
            vals.append(Command.create({
                "name": "Predaj", "account_id": self.income.id,
                "credit": amount, "tax_ids": [Command.set(tax.ids)]}))
            total += amount * (1 + tax.amount / 100.0)
        vals.append(Command.create({
            "name": "Hotovosť", "account_id": self.cash.id,
            "debit": round(total, 2)}))
        move = self.env["account.move"].create({
            "move_type": "entry", "date": "2026-06-15",
            "journal_id": self.config.sudo().journal_id.id, "line_ids": vals})
        if session:
            pos_session = self.env["pos.session"].sudo().create({
                "config_id": self.config.id, "user_id": self.env.uid})
            pos_session.move_id = move
        move.action_post()
        return move

    def _code(self, move):
        return move.line_ids.filtered("tax_ids")[:1].cssk_control_section_code

    def test_a_session_sale_is_d1(self):
        self.assertEqual(self._code(self._session_entry(
            [(100.0, self.tax_basic)])), "D.1")

    def test_the_same_entry_without_a_session_stays_d2(self):
        self.assertEqual(self._code(self._session_entry(
            [(100.0, self.tax_basic)], session=False)), "D.2")

    def test_a_journal_override_still_wins(self):
        self.config.journal_id.sudo().cssk_control_section_override = "D.2"
        self.assertEqual(self._code(self._session_entry(
            [(100.0, self.tax_basic)])), "D.2")

    def test_the_statement_files_the_turnover_and_the_rates(self):
        self.assertTrue(self.tax_reduced, "the SK chart ships a reduced rate")
        self._session_entry([(100.0, self.tax_basic),
                             (50.0, self.tax_reduced)])
        st = self.env["cssk.control.statement"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": self.env["cssk.control.statement.type"].search([
                ("country_id", "=", self.env.ref("base.sk").id),
                ("fa_xml_value", "=", "R")]).id,
        })
        st.action_compute_lines()
        self.assertFalse(st.sk_section_d2_ids, "nothing left in D.2")
        st.action_export_xml()
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        d1 = root.find(".//{*}D1")
        basic_tax = round(100.0 * self.tax_basic.amount / 100.0, 2)
        lower_tax = round(50.0 * self.tax_reduced.amount / 100.0, 2)
        self.assertEqual(d1.get("Z"), "100.00")
        self.assertEqual(d1.get("D"), "%.2f" % basic_tax)
        self.assertEqual(d1.get("ZZn"), "50.00")
        self.assertEqual(d1.get("DZn"), "%.2f" % lower_tax)
        self.assertEqual(d1.get("SumaObratov"),
                         "%.2f" % (150.0 + basic_tax + lower_tax))
