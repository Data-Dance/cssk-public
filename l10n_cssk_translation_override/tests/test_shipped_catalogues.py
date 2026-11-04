# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.modules.module import get_module_path
from odoo.tests import TransactionCase, tagged

from .. import catalogue_check, overrides


@tagged("post_install", "-at_install")
class TestShippedCatalogues(TransactionCase):
    def test_every_override_is_well_formed(self):
        """Each shipped entry is one Odoo will load: the right module header,
        the code comment a code term needs, a translation, no fuzzy flag.

        Whether each entry still matches its target's CURRENT source is not
        asked here: the catalogues are built against a pinned upstream
        revision, and on an older server a newer term looks exactly like a
        stale one. tools/check_translation_overrides.py asks that question
        against the pinned revision.
        """
        problems = []
        for path in catalogue_check.shipped_catalogues(overrides.OVERRIDE_DIRS[0]):
            found, _checked = catalogue_check.check_catalogue(path, lambda name: None)
            problems += found
        self.assertFalse(problems, "\n".join(problems[:50]))

    def test_checker_catches_a_stale_entry(self):
        """Negative control: the fixture for no_such_module cannot resolve,
        and a fixture against base with a wrong occurrence is reported."""
        import os
        import tempfile

        base = get_module_path("base")
        with tempfile.TemporaryDirectory() as tmp:
            os.mkdir(os.path.join(tmp, "base"))
            path = os.path.join(tmp, "base", "sk.po")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(
                    'msgid ""\nmsgstr ""\n"Language: sk_SK\\n"\n'
                    '"Content-Type: text/plain; charset=UTF-8\\n"\n\n'
                    "#. module: base\n"
                    "#: model:ir.model.fields,field_description:base.field_res_partner__nope\n"
                    'msgid "Notes"\nmsgstr "x"\n\n'
                    "#. module: base\n"
                    "#: code:addons/base/models/res_partner.py:0\n"
                    'msgid "This string does not exist anywhere"\nmsgstr "y"\n'
                )
            problems, checked = catalogue_check.check_catalogue(
                path, lambda name: base if name == "base" else None
            )
        self.assertTrue(checked)
        text = "\n".join(problems)
        self.assertIn("occurrence model:ir.model.fields,field_description:base.field_res_partner__nope", text)
        self.assertIn("msgid not in base's template", text)
        self.assertIn("never loaded", text)
