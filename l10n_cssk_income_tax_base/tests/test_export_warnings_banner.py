# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestExportWarningsBanner(TransactionCase):
    """The last export's non-blocking warnings (``cssk_export_warnings``) are
    kept on the record; the form shows them as a warning banner above the
    sheet, visible only while there are some."""

    def test_the_form_shows_the_export_warnings(self):
        arch = self.env["cssk.income.tax.return"].get_views(
            [(False, "form")])["views"]["form"]["arch"]
        tree = etree.fromstring(arch)
        banner = tree.find(".//div[@name='cssk_export_warnings_banner']")
        self.assertIsNotNone(banner, "no warnings banner on the form")
        self.assertIn("alert-warning", banner.get("class"))
        self.assertEqual(banner.get("invisible"), "not cssk_export_warnings")
        self.assertIsNotNone(
            banner.find(".//field[@name='cssk_export_warnings']"))
