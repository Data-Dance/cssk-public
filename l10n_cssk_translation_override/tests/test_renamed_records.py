# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import os
import tempfile

from psycopg2.extras import Json

from odoo.tests import TransactionCase, tagged

from .. import catalogue_check
from ..models.ir_module import SourceCheckedImporter

LANG = "sk_SK"
RENAMED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "i18n_renamed")
XMLID = "base.menu_administration"
HEADER = 'msgid ""\nmsgstr ""\n"Language: sk_SK\\n"\n"Content-Type: text/plain; charset=UTF-8\\n"\n\n'


def _po(msgid, msgstr, module="base"):
    return (HEADER + f"#. module: {module}\n#: model:ir.ui.menu,name:{XMLID}\n"
            f'msgid "{msgid}"\nmsgstr "{msgstr}"\n').encode()


@tagged("post_install", "-at_install")
class TestRenamedRecords(TransactionCase):
    """A record another module renames in English (OCA account_usability:
    account.menu_finance "Invoicing" -> "Accounting") must get the translation
    of its CURRENT English, whichever catalogue loads last."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.lang"]._activate_lang(LANG)
        cls.menu = cls.env.ref(XMLID)

    def _set_english(self, value):
        self.env.cr.execute(
            "UPDATE ir_ui_menu SET name = name || %s WHERE id = %s", [Json({"en_US": value}), self.menu.id]
        )
        self.env.invalidate_all()

    def _import(self, *files):
        importer = SourceCheckedImporter(self.env.cr, verbose=False)
        with tempfile.TemporaryDirectory() as tmp:
            for i, content in enumerate(files):
                path = os.path.join(tmp, f"{i}.po")
                with open(path, "wb") as fh:
                    fh.write(content)
                with open(path, "rb") as fh:
                    importer.load(fh, "po", LANG)
        importer.save(overwrite=True)
        self.env.invalidate_all()
        return self.menu.with_context(lang=LANG).name

    def test_current_english_wins_in_either_order(self):
        self._set_english("CSSK Renamed")
        old = _po("CSSK Original", "CSSK-TEST stary nazov")
        new = _po("CSSK Renamed", "CSSK-TEST novy nazov", module="account_usability")
        self.assertEqual(self._import(old, new), "CSSK-TEST novy nazov")
        self.assertEqual(self._import(new, old), "CSSK-TEST novy nazov")

    def test_stale_source_is_not_written(self):
        # English is still the original: an entry for the renamed text must not land.
        self.assertNotEqual(self._import(_po("CSSK Renamed", "CSSK-TEST before")), "CSSK-TEST before")
        self._set_english("CSSK Renamed")
        self.assertEqual(self._import(_po("CSSK Renamed", "CSSK-TEST novy")), "CSSK-TEST novy")
        # The renaming module is gone (English back to the original): the old
        # entry applies again, the renamed one no longer does.
        self._set_english("CSSK Original")
        self.assertEqual(self._import(_po("CSSK Renamed", "CSSK-TEST zle")), "CSSK-TEST novy")
        self.assertEqual(self._import(_po("CSSK Original", "CSSK-TEST stary")), "CSSK-TEST stary")

    def _import_as_override(self, *targets):
        """As the hook does: <dir>/<target>/sk.po through load_file. The
        fixtures live in the module, because file_open only reads files
        under an addons path (a temp file would be skipped in silence)."""
        importer = SourceCheckedImporter(self.env.cr, verbose=False)
        for target in targets:
            importer.load_file(os.path.join(RENAMED, target, "sk.po"), LANG)
        importer.save(overwrite=True)
        self.env.invalidate_all()
        return self.menu.with_context(lang=LANG).name

    def test_renamed_record_overrides_noupdate(self):
        self.env.cr.execute(
            "UPDATE ir_model_data SET noupdate = true WHERE module = 'base' AND name = 'menu_administration'"
        )
        self._set_english("CSSK Renamed")
        # Control: the record's own module's catalogue respects noupdate.
        before = self.menu.with_context(lang=LANG).name
        self.assertEqual(self._import_as_override("base"), before)
        # A catalogue of the module that renamed it writes through noupdate.
        self.assertEqual(
            self._import_as_override("fake_renamer"),
            "CSSK-TEST premenovany",
        )

    def test_own_entry_keeps_noupdate_when_rename_is_gone(self):
        """The renaming catalogue is loaded but its English is not the
        record's any more: the record's own entry wins, and as a normal entry
        it must not write through noupdate."""
        self.env.cr.execute(
            "UPDATE ir_model_data SET noupdate = true WHERE module = 'base' AND name = 'menu_administration'"
        )
        self._set_english("CSSK Original")
        before = self.menu.with_context(lang=LANG).name
        self.assertEqual(self._import_as_override("base", "fake_renamer"), before)
        self.assertEqual(self._import_as_override("fake_renamer", "base"), before)


@tagged("post_install", "-at_install")
class TestRenamedRecordCheck(TransactionCase):
    def test_checker_verifies_against_the_renaming_xml(self):
        with tempfile.TemporaryDirectory() as tmp:
            mod = os.path.join(tmp, "fake_renamer")
            os.makedirs(os.path.join(mod, "views"))
            os.makedirs(os.path.join(mod, "i18n"))
            with open(os.path.join(mod, "views", "menu.xml"), "w") as fh:
                fh.write('<odoo><record id="base.menu_administration" model="ir.ui.menu">'
                         '<field name="name">CSSK Renamed</field></record></odoo>')
            with open(os.path.join(mod, "i18n", "fake_renamer.pot"), "w") as fh:
                fh.write('msgid ""\nmsgstr ""\n')
            over = os.path.join(tmp, "over", "fake_renamer")
            os.makedirs(over)
            path = os.path.join(over, "sk.po")
            with open(path, "wb") as fh:
                fh.write(_po("CSSK Renamed", "ok", module="fake_renamer")[:-1] + b"\n\n"
                         + _po("CSSK Wrong English", "bad", module="fake_renamer")[len(HEADER):])
            problems, checked = catalogue_check.check_catalogue(
                path, lambda name: mod if name == "fake_renamer" else None
            )
        self.assertTrue(checked)
        text = "\n".join(problems)
        self.assertNotIn("CSSK Renamed", text)
        self.assertIn("CSSK Wrong English", text)
