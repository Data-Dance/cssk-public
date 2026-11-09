# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from pathlib import Path

from odoo.tests import TransactionCase, tagged
from odoo.tools.translate import PoFileReader


@tagged("post_install", "-at_install")
class TestTranslationCatalogs(TransactionCase):
    def test_slovak_and_czech_catalogs_can_be_read_by_odoo(self):
        root = Path(__file__).resolve().parents[1] / "i18n"
        for language in ("sk", "cs"):
            with self.subTest(language=language):
                with (root / (language + ".po")).open("rb") as source:
                    rows = list(PoFileReader(source))
                self.assertTrue(rows)
