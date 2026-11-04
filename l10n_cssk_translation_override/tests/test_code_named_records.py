# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from unittest import SkipTest

from odoo.tests import TransactionCase, tagged

from .. import overrides
from .test_override import EMAIL_SRC, FIXTURES, LANG

OURS = "CSSK-TEST Platný e-mail je povinný."
FIELDS = [("res.partner.category", "name")]


@tagged("post_install", "-at_install")
class TestCodeNamedRecords(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.lang"]._activate_lang(LANG)
        cls._dirs = list(overrides.OVERRIDE_DIRS)
        overrides.OVERRIDE_DIRS.append(FIXTURES)
        overrides.reset_code_translation_cache()
        cls.Module = cls.env["ir.module.module"]
        cls.Category = cls.env["res.partner.category"].with_context(lang="en_US")

    @classmethod
    def tearDownClass(cls):
        overrides.OVERRIDE_DIRS[:] = cls._dirs
        overrides.reset_code_translation_cache()
        super().tearDownClass()

    def _sk(self, record):
        record.invalidate_recordset()
        return record.with_context(lang=LANG).name

    def test_exact_and_prefixed_names(self):
        # A category stands in for an operation type: an English-only name
        # equal to a code message, and the "<warehouse>: <message>" shape.
        exact = self.Category.create({"name": EMAIL_SRC})
        prefixed = self.Category.create({"name": f"WH: {EMAIL_SRC}"})
        other = self.Category.create({"name": "Not a code message"})
        self.assertEqual(self._sk(exact), EMAIL_SRC)  # negative control
        self.Module._cssk_translate_code_named_records([LANG], FIELDS)
        self.assertEqual(self._sk(exact), OURS)
        self.assertEqual(self._sk(prefixed), f"WH: {OURS}")
        self.assertEqual(self._sk(other), "Not a code message")
        # English stays English.
        exact.invalidate_recordset()
        self.assertEqual(exact.with_context(lang="en_US").name, EMAIL_SRC)

    def test_hand_made_translation_is_kept(self):
        record = self.Category.create({"name": EMAIL_SRC})
        record.with_context(lang=LANG).write({"name": "Vlastný názov"})
        self.Module._cssk_translate_code_named_records([LANG], FIELDS)
        self.assertEqual(self._sk(record), "Vlastný názov")

    def test_warehouse_operation_types(self):
        """The real case: a warehouse created in English."""
        if "stock.warehouse" not in self.env:
            raise SkipTest("stock is not installed")
        warehouse = self.env["stock.warehouse"].with_context(lang="en_US").create(
            {"name": "CSSK Test Warehouse", "code": "CSSKT"})
        receipts = warehouse.in_type_id
        self.assertEqual(receipts.with_context(lang="en_US").name, "Receipts")
        expected = self.Module._cssk_code_terms(LANG).get("Receipts")
        self.assertTrue(expected, "no Slovak code translation for 'Receipts' to check against")
        self.Module._cssk_translate_code_named_records([LANG])
        self.assertEqual(self._sk(receipts), expected)
        route = warehouse.reception_route_id
        en_route = route.with_context(lang="en_US").name
        self.assertTrue(en_route.startswith("CSSK Test Warehouse: "))
        self.assertNotEqual(self._sk(route), en_route)
        # English stays the source, also where en_US is not an active language.
        receipts.invalidate_recordset()
        self.assertEqual(receipts.with_context(lang="en_US").name, "Receipts")

    def test_two_languages_without_english(self):
        """A Slovak + Czech tenant: both get their name from the one English
        source, which an ORM write would have replaced after the first."""
        self.env["res.lang"]._activate_lang("cs_CZ")
        record = self.Category.create({"name": EMAIL_SRC})
        cs = "CSSK-TEST Platný e-mail je povinný (cs)."
        orig = self.Module._cssk_code_terms
        def fake(lang):
            terms = orig(lang)
            return dict(terms, **({EMAIL_SRC: cs} if lang == "cs_CZ" else {}))
        from unittest.mock import patch
        with patch.object(type(self.Module), "_cssk_code_terms", lambda self, lang: fake(lang)):
            self.Module._cssk_translate_code_named_records([LANG, "cs_CZ"], FIELDS)
        record.invalidate_recordset()
        self.assertEqual(record.with_context(lang=LANG).name, OURS)
        self.assertEqual(record.with_context(lang="cs_CZ").name, cs)
        self.assertEqual(record.with_context(lang="en_US").name, EMAIL_SRC)
