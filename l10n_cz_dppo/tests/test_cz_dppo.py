# Copyright 2026 Data Dance s.r.o.
# Data Dance Proprietary License v1.0 — see the LICENSE file.

import base64

from lxml import etree

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCzDppo(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.vat = "CZ25663585"
        # EPO requires the destination tax office (c_ufo_cil).
        # FÚ pro hl. m. Prahu — seeded by l10n_cz_statutory's hook without an
        # xmlid (the old l10n_cssk_core.cz_ufo_* ids were removed in 1.2.0);
        # look it up by its stable submission code instead.
        cls.company.l10n_cssk_tax_authority_id = cls.env["cssk.tax.authority"].search(
            [("country_code", "=", "CZ"), ("submission_code", "=", "451")], limit=1)
        cls.version = cls.env.ref("l10n_cz_dppo.cz_dppo_version_2025")
        cls.type_b = cls.env.ref("l10n_cz_dppo.cz_dppo_type_B")
        cls.misc = cls.company_data["default_journal_misc"]

    def _acc(self, like):
        return self.env["account.account"].search(
            [("code", "=like", like), ("company_ids", "in", self.company.id)],
            limit=1)

    def _return(self):
        ret = self.env["cssk.income.tax.return"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "statement_type_id": self.type_b.id,
            "date_from": "2025-01-01", "date_to": "2025-12-31"})
        ret.action_compute_lines()
        return ret

    def _v(self, ret, code):
        return ret.line_ids.filtered(lambda l: l.code == code).value

    def test_profit_spine_and_export(self):
        income, expense, bank = self._acc("602%"), self._acc("501%"), self._acc("221%")
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.misc.id, "date": "2025-06-30",
            "line_ids": [
                Command.create({"account_id": income.id, "credit": 10000.0}),
                Command.create({"account_id": expense.id, "debit": 6000.0}),
                Command.create({"account_id": bank.id, "debit": 4000.0})]})
        move.action_post()
        ret = self._return()
        # profit 4000 -> base 4000 -> tax 21% = 840
        self.assertAlmostEqual(self._v(ret, "r10"), 4000.0, places=2)
        self.assertAlmostEqual(self._v(ret, "r270"), 4000.0, places=2)
        self.assertAlmostEqual(self._v(ret, "r290"), 840.0, places=2)

        # exporting validates against the official DPPDP9 EPO XSD
        ret.action_export_xml()
        self.assertEqual(ret.state, "exported")
        root = etree.fromstring(base64.b64decode(ret.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).localname, "Pisemnost")
        # II. oddíl values land on the official VetaO attributes
        veta_o = root.find(".//VetaO")
        self.assertIsNotNone(veta_o)
        self.assertEqual(veta_o.get("kc_ii10_10"), "4000")   # ř.10
        self.assertEqual(veta_o.get("kc_ii280_290"), "840")  # ř.290 daň
        self.assertEqual(veta_o.get("kc_ii_340"), "840")     # celková daň
