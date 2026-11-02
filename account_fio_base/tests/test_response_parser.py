# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

# ``odoo.tests.BaseCase`` rather than ``unittest.TestCase``: it is the same
# plain TestCase — no database, no cursor — but its ``__init_subclass__``
# assigns the ``standard``/``at_install`` tags. Odoo's TagsSelector silently
# SKIPS any class without ``test_tags``, so a bare unittest.TestCase in a
# tests/ package never runs under ``odoo-bin --test-enable`` at all.
from odoo.tests import BaseCase as TestCase

from odoo.addons.account_fio_base.utils.response import (
    FioResponseParseError,
    parse_import_response,
)

from .fio_fixtures import import_response


class TestFioImportResponse(TestCase):
    def test_accepted(self):
        result = parse_import_response(import_response())
        self.assertTrue(result.accepted)
        self.assertEqual(result.error_code, 0)
        self.assertEqual(result.id_instruction, "1704810070")
        self.assertEqual(result.sum_debet, 1234.50)
        self.assertIn("1704810070", result.summary)
        self.assertIn("authorised", result.summary)

    def test_warning_code_still_means_accepted(self):
        """§6.1: "příkazy s odpovědí warning byly přijaty bankou".

        Treating every non-zero code as a failure is how a batch that the bank
        already holds gets uploaded a second time.
        """
        result = parse_import_response(import_response(
            error_code=2, status="warning",
            messages=[("warning", 2, "Měna platby nesouhlasí s měnou účtu")],
        ))
        self.assertTrue(result.accepted)
        self.assertEqual(len(result.messages), 1)
        self.assertEqual(result.messages[0].status, "warning")

    def test_rejected(self):
        result = parse_import_response(import_response(
            error_code=1, status="error", id_instruction="",
            messages=[("error", 100, "Neplatné číslo účtu")],
        ))
        self.assertFalse(result.accepted)
        self.assertEqual(result.messages[0].text, "Neplatné číslo účtu")
        self.assertEqual(result.messages[0].order, "1")

    def test_every_documented_code_has_a_summary(self):
        for code in (0, 1, 2, 11, 12, 13, 14):
            result = parse_import_response(import_response(error_code=code))
            self.assertTrue(result.summary)
            self.assertNotIn("error code %s" % code, result.summary)

    def test_unknown_code_is_not_silently_accepted(self):
        result = parse_import_response(import_response(error_code=99))
        self.assertFalse(result.accepted)

    def test_missing_error_code(self):
        with self.assertRaises(FioResponseParseError):
            parse_import_response(b"<responseImport></responseImport>")

    def test_html_error_page(self):
        with self.assertRaises(FioResponseParseError):
            parse_import_response(b"<html><body>500</body></html>")
