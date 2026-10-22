# Copyright 2026 Data Dance s.r.o.
# Data Dance Proprietary License v1.0 — see the LICENSE file.

import base64

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestUzpod(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write({"vat": "SK2023456787", "city": "Bratislava",
                           "company_registry": "12345678"})
        cls.journal = cls.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", cls.company.id)], limit=1)

    def _acc(self, code):
        acc = self.env["account.account"].search(
            [("code", "=like", code + "%"), ("company_ids", "in", self.company.id)],
            limit=1)
        if not acc:
            acc = self.env["account.account"].create({
                "name": code, "code": code + "000", "account_type": "asset_current",
                "company_ids": [Command.set([self.company.id])]})
        return acc

    def test_uzpod_export_validates(self):
        # Dr 012 1000, Cr 072 300 (oprávky), Cr 411 700 (equity) — balanced,
        # no open P&L -> r004 net 700, r082 net 700, sheet reconciles.
        dev, opr, eq = self._acc("012"), self._acc("072"), self._acc("411")
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.journal.id, "date": "2026-06-30",
            "line_ids": [
                Command.create({"account_id": dev.id, "debit": 1000.0}),
                Command.create({"account_id": opr.id, "credit": 300.0}),
                Command.create({"account_id": eq.id, "credit": 700.0}),
            ]})
        move.action_post()

        uz = self.env["l10n.sk.uzpod"].create({
            "company_id": self.company.id,
            "date_from": "2026-01-01", "date_to": "2026-12-31"})
        uz.action_export_xml()
        self.assertEqual(uz.state, "exported")

        root = etree.fromstring(base64.b64decode(uz.xml_attachment_id.datas))
        self.assertEqual(root.tag, "dokument")
        suvaha = root.findall(".//ucPod1Suvaha/*")
        vzs = root.findall(".//ucPod2VykazZS/*")
        self.assertEqual(len(suvaha), 145)
        self.assertEqual(len(vzs), 61)

        def srow(n):
            return root.find(".//ucPod1Suvaha/r%03d" % n)
        # r004 = Aktivované náklady na vývoj (012) - /072, 091A/
        r4 = srow(4)
        self.assertEqual(r4.findtext("s1"), "1000")   # brutto
        self.assertEqual(r4.findtext("s2"), "300")    # korekcia
        self.assertEqual(r4.findtext("s3"), "700")    # netto
        # r001 SPOLU MAJETOK netto == r079 SPOLU VI A ZÁVÄZKY netto (reconciles)
        self.assertEqual(srow(1).findtext("s3"), "700")
        self.assertEqual(srow(79).findtext("s5"), "700")

        # header typUzavierky defaults: riadna + malá účtovná jednotka (the
        # mandatory veľkostná trieda must be one-hot, never 0/0)
        tu = root.find(".//hlavicka/typUzavierky")
        self.assertEqual(tu.findtext("riadna"), "1")
        self.assertEqual(tu.findtext("mimoriadna"), "0")
        self.assertEqual(tu.findtext("priebezna"), "0")
        self.assertEqual(tu.findtext("mala"), "1")
        self.assertEqual(tu.findtext("velka"), "0")

    def test_uzpod_size_class_velka(self):
        """size_class='velka' emits velka=1 / mala=0 and stays XSD-valid."""
        dev, opr, eq = self._acc("012"), self._acc("072"), self._acc("411")
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.journal.id, "date": "2026-06-30",
            "line_ids": [
                Command.create({"account_id": dev.id, "debit": 1000.0}),
                Command.create({"account_id": opr.id, "credit": 300.0}),
                Command.create({"account_id": eq.id, "credit": 700.0}),
            ]})
        move.action_post()
        uz = self.env["l10n.sk.uzpod"].create({
            "company_id": self.company.id, "size_class": "velka",
            "date_from": "2026-01-01", "date_to": "2026-12-31"})
        uz.action_export_xml()  # XSD validation runs inside
        self.assertEqual(uz.state, "exported")
        root = etree.fromstring(base64.b64decode(uz.xml_attachment_id.datas))
        tu = root.find(".//hlavicka/typUzavierky")
        self.assertEqual(tu.findtext("velka"), "1")
        self.assertEqual(tu.findtext("mala"), "0")
        self.assertEqual(tu.findtext("riadna"), "1")

    def test_submit_lock_and_retention(self):
        """Submitting the UZPODv14 freezes the filed XML and locks re-export;
        reset keeps the filed copy."""
        dev, opr, eq = self._acc("012"), self._acc("072"), self._acc("411")
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.journal.id, "date": "2026-06-30",
            "line_ids": [
                Command.create({"account_id": dev.id, "debit": 1000.0}),
                Command.create({"account_id": opr.id, "credit": 300.0}),
                Command.create({"account_id": eq.id, "credit": 700.0}),
            ]})
        move.action_post()
        uz = self.env["l10n.sk.uzpod"].create({
            "company_id": self.company.id,
            "date_from": "2026-01-01", "date_to": "2026-12-31"})
        uz.action_export_xml()
        filed = uz.xml_attachment_id
        self.assertTrue(filed)

        uz.submission_reference = "FS-UZ-2026-001"
        uz.action_submit()
        self.assertEqual(uz.state, "submitted")
        self.assertEqual(uz.submitted_attachment_id, filed)
        self.assertTrue(uz.submitted_date)
        with self.assertRaises(UserError):
            uz.action_export_xml()
        uz.action_reset_to_draft()
        self.assertEqual(uz.state, "draft")
        self.assertEqual(uz.submitted_attachment_id, filed)

    def test_opravna_zaverka_amendment(self):
        """Opravná účtovná závierka: submit a UZPODv14, raise an amendment — it
        links back, is flagged Opravná, keeps the filed copy, and re-exports a
        still-XSD-valid body (druh stays riadna) with the corrective marker in
        the filing metadata (filename), not the schema body (which has none)."""
        dev, opr, eq = self._acc("012"), self._acc("072"), self._acc("411")
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.journal.id, "date": "2026-06-30",
            "line_ids": [
                Command.create({"account_id": dev.id, "debit": 1000.0}),
                Command.create({"account_id": opr.id, "credit": 300.0}),
                Command.create({"account_id": eq.id, "credit": 700.0}),
            ]})
        move.action_post()
        uz = self.env["l10n.sk.uzpod"].create({
            "company_id": self.company.id,
            "date_from": "2026-01-01", "date_to": "2026-12-31"})
        self.assertEqual(uz.submission_type, "radna")
        uz.action_export_xml()
        uz.submission_reference = "FS-UZ-2026-001"
        uz.action_submit()
        filed = uz.submitted_attachment_id

        action = uz.action_create_amendment()
        amend = self.env["l10n.sk.uzpod"].browse(action["res_id"])
        self.assertEqual(amend.original_return_id, uz)
        self.assertEqual(amend.submission_type, "opravna")
        self.assertEqual(amend.state, "draft")
        self.assertIn("opravná", amend.name)
        self.assertIn(amend, uz.amendment_ids)
        # original untouched: still submitted, filed copy preserved
        self.assertEqual(uz.state, "submitted")
        self.assertEqual(uz.submitted_attachment_id, filed)

        # amendment re-exports: action_export_xml validates against the XSD, so a
        # pass proves the body stays schema-valid. The corrective marker is in the
        # filename (submission-level); the body druh stays riadna with no
        # corrective element (the schema has none).
        amend.action_export_xml()
        self.assertEqual(amend.state, "exported")
        self.assertIn("-opravna", amend.xml_attachment_id.name)
        root = etree.fromstring(base64.b64decode(amend.xml_attachment_id.datas))
        tu = root.find(".//hlavicka/typUzavierky")
        self.assertEqual(tu.findtext("riadna"), "1")   # body druh stays riadna
        self.assertIsNone(tu.find("opravna"))          # no corrective body element

    def test_uzpod_kontroly(self):
        """The kontrolné pravidlá (content checks beyond the XSD) pass on valid
        data and catch a deliberately broken bilančná rovnosť."""
        dev, opr, eq = self._acc("012"), self._acc("072"), self._acc("411")
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.journal.id, "date": "2026-06-30",
            "line_ids": [
                Command.create({"account_id": dev.id, "debit": 1000.0}),
                Command.create({"account_id": opr.id, "credit": 300.0}),
                Command.create({"account_id": eq.id, "credit": 700.0}),
            ]})
        move.action_post()
        uz = self.env["l10n.sk.uzpod"].create({
            "company_id": self.company.id,
            "date_from": "2026-01-01", "date_to": "2026-12-31"})

        xml_bytes = uz._build_xml()
        # Valid, reconciling sheet -> no violations (bilancia, netto, súčty).
        self.assertEqual(
            uz.check_kontroly(xml_bytes), [],
            "kontrolné pravidlá should pass on a reconciling výkaz")

        # Break AKTÍVA = PASÍVA (mutate r079 netto) -> BS_BALANCE must fire.
        root = etree.fromstring(xml_bytes)
        root.find(".//ucPod1Suvaha/r079/s5").text = "999"
        broken = uz.check_kontroly(etree.tostring(root, encoding="UTF-8"))
        self.assertIn("BS_BALANCE", [v["code"] for v in broken],
                      "kontroly must catch AKTÍVA != PASÍVA")
