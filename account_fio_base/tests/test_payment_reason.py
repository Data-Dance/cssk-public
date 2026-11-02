# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""The platební titul code list (§6.3.4).

It is transcribed from a PDF, and Fio rejects a foreign payment carrying a code
it does not know — so the list's shape is worth asserting rather than trusting.
"""

import re
# ``odoo.tests.BaseCase`` rather than ``unittest.TestCase``: it is the same
# plain TestCase — no database, no cursor — but its ``__init_subclass__``
# assigns the ``standard``/``at_install`` tags. Odoo's TagsSelector silently
# SKIPS any class without ``test_tags``, so a bare unittest.TestCase in a
# tests/ package never runs under ``odoo-bin --test-enable`` at all.
from odoo.tests import BaseCase as TestCase

from odoo.addons.account_fio_base.utils.payment_reason import (
    PAYMENT_REASONS,
    is_valid_payment_reason,
    payment_reason_selection,
)


class TestPaymentReasons(TestCase):
    def test_the_whole_list_was_transcribed(self):
        self.assertEqual(len(PAYMENT_REASONS), 129)

    def test_every_code_is_three_digits(self):
        """``paymentReason`` is a ``3!n`` field — a fixed three-digit number."""
        bad = [code for code in PAYMENT_REASONS if not re.fullmatch(r"\d{3}", code)]
        self.assertEqual(bad, [])

    def test_every_description_is_real_text(self):
        """Catches a row where the PDF's page furniture leaked into the value."""
        for code, description in PAYMENT_REASONS.items():
            self.assertGreaterEqual(len(description), 4, code)
            self.assertNotIn("www.fio.cz", description)
            self.assertNotIn("Verze", description)

    def test_the_codes_the_documentation_uses_as_examples(self):
        # §6.3.1 uses 110, §6.3.3 uses 348.
        self.assertEqual(PAYMENT_REASONS["110"], "Vývoz zboží")
        self.assertEqual(PAYMENT_REASONS["348"], "Nájemné")
        self.assertEqual(PAYMENT_REASONS["120"], "Dovoz zboží")

    def test_the_wrapped_row_survived_transcription(self):
        """347's description runs across three lines in the PDF."""
        self.assertIn("public relations", PAYMENT_REASONS["347"])
        self.assertTrue(PAYMENT_REASONS["347"].startswith("Poradenství"))

    def test_validation(self):
        self.assertTrue(is_valid_payment_reason("110"))
        self.assertTrue(is_valid_payment_reason(" 110 "))
        self.assertFalse(is_valid_payment_reason("999"))
        self.assertFalse(is_valid_payment_reason("11"))
        self.assertFalse(is_valid_payment_reason(""))
        self.assertFalse(is_valid_payment_reason(None))

    def test_selection_is_sorted_and_labelled(self):
        selection = payment_reason_selection()
        self.assertEqual(len(selection), len(PAYMENT_REASONS))
        self.assertEqual(selection, sorted(selection))
        code, label = selection[0]
        self.assertTrue(label.startswith(code))
        self.assertIn(PAYMENT_REASONS[code], label)
