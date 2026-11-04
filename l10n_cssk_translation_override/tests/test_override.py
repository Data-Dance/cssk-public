# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import os

from odoo.tests import TransactionCase, tagged
from odoo.tools.translate import TranslationImporter, code_translations, get_po_paths

from .. import overrides

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "i18n_override")
LANG = "sk_SK"
EMAIL_SRC = "A valid email is required for find_or_create to work properly."


@tagged("post_install", "-at_install")
class TestTranslationOverride(TransactionCase):
    """The mechanism, on fixture catalogues for ``base`` and ``web``.

    Every fixture value starts with ``CSSK-TEST`` so no assertion can pass on
    Odoo's own Slovak text by coincidence.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.lang"]._activate_lang(LANG)
        cls._dirs = list(overrides.OVERRIDE_DIRS)
        overrides.OVERRIDE_DIRS.append(FIXTURES)
        overrides.reset_code_translation_cache()

    @classmethod
    def tearDownClass(cls):
        overrides.OVERRIDE_DIRS[:] = cls._dirs
        overrides.reset_code_translation_cache()
        super().tearDownClass()

    def _apply(self):
        self.env["ir.module.module"]._cssk_apply_translation_overrides([LANG])
        self.env.invalidate_all()

    def _sk(self, xmlid, field):
        return self.env.ref(xmlid).with_context(lang=LANG)[field]

    def _reload_odoo_catalogue(self):
        """Load base's own Slovak catalogue with overwrite, bypassing our hook,
        as `--i18n-overwrite` or a language reload would."""
        importer = TranslationImporter(self.env.cr, verbose=False)
        for path in get_po_paths("base", LANG):
            importer.load_file(path, LANG)
        importer.save(overwrite=True)
        self.env.invalidate_all()

    def test_field_selection_and_view_terms(self):
        self._apply()
        self.assertEqual(
            self._sk("base.field_res_partner__comment", "field_description"),
            "CSSK-TEST Poznámky",
        )
        # What the user actually sees: the label the web client is given.
        self.env.registry.clear_cache()
        fields = self.env["res.partner"].with_context(lang=LANG).fields_get(["comment", "type"])
        self.assertEqual(fields["comment"]["string"], "CSSK-TEST Poznámky")
        self.assertIn(("invoice", "CSSK-TEST Fakturačná adresa"), fields["type"]["selection"])
        arch = self._sk("base.view_partner_form", "arch_db")
        self.assertIn("CSSK-TEST Možné duplicity:", arch)

    def test_odoo_overwrite_then_hook_restores(self):
        self._apply()
        self._reload_odoo_catalogue()
        # Negative control: an overwriting reload of Odoo's own catalogue
        # really does replace the override, so the next assertion is not
        # vacuous.
        self.assertNotEqual(
            self._sk("base.field_res_partner__comment", "field_description"),
            "CSSK-TEST Poznámky",
        )
        self.env["ir.module.module"]._load_module_terms(["base"], [LANG], overwrite=True)
        self.env.invalidate_all()
        self.assertEqual(
            self._sk("base.field_res_partner__comment", "field_description"),
            "CSSK-TEST Poznámky",
        )

    def test_module_upgrade_path(self):
        """``loading.py`` reloads a module's terms through _update_translations."""
        self._reload_odoo_catalogue()
        self.env.ref("base.module_base")._update_translations(LANG)
        self.env.invalidate_all()
        self.assertEqual(
            self._sk("base.selection__res_partner__type__invoice", "name"),
            "CSSK-TEST Fakturačná adresa",
        )

    def test_language_reload_with_overwrite(self):
        """Settings > Languages > Add with "Overwrite Existing Terms"."""
        self._apply()
        lang = self.env["res.lang"]._lang_get(LANG)
        wizard = self.env["base.language.install"].create(
            {"lang_ids": [(6, 0, [lang.id])], "overwrite": True}
        )
        wizard.lang_install()
        self.env.invalidate_all()
        self.assertEqual(
            self._sk("base.field_res_partner__comment", "field_description"),
            "CSSK-TEST Poznámky",
        )

    def test_absent_target_is_skipped(self):
        # The fixture for no_such_module names an unknown model and an unknown
        # xmlid on a known model; neither may raise or create anything.
        self._apply()
        self.assertNotIn("nothing", self.env["res.partner"]._fields)
        self.assertFalse(self.env.ref("no_such_module.field_res_partner__nothing", False))

    def test_python_code_term(self):
        overrides.reset_code_translation_cache()
        self.assertEqual(
            code_translations.get_python_translations("base", LANG).get(EMAIL_SRC),
            "CSSK-TEST Platný e-mail je povinný.",
        )

    def test_web_code_term(self):
        overrides.reset_code_translation_cache()
        translations, _params = self.env["ir.http"]._get_translations_for_webclient(["web"], LANG)
        messages = {m["id"]: m["string"] for m in translations["web"]["messages"]}
        self.assertEqual(messages.get("# Code editor"), "CSSK-TEST # Editor kódu")
        # Odoo's own terms for web still arrive alongside ours.
        self.assertGreater(len(messages), 100)

    def test_patch_is_idempotent(self):
        func = type(code_translations)._get_code_translations
        # Assert before calling install, or this test would itself install
        # the patch and mask its absence from the code-term tests after it.
        self.assertTrue(getattr(func, "_cssk_override", False), "patch not installed at import")
        overrides.install_code_translation_patch()
        self.assertIs(type(code_translations)._get_code_translations, func)
        self.assertTrue(func._cssk_override)
