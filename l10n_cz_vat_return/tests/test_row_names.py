# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import importlib.util

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools.misc import file_path

from odoo.addons.l10n_cz_vat_return.row_names import (
    is_shipped_placeholder,
    shipped_row_names,
)


@tagged("post_install", "-at_install")
class TestRowNames(TransactionCase):
    """Every DPHDP3 row carries the form's caption, not a placeholder."""

    def test_every_row_has_a_caption(self):
        names = shipped_row_names()
        self.assertEqual(len(names), 74)
        for xmlid, name in names.items():
            self.assertFalse(is_shipped_placeholder(name), xmlid)

    def test_database_rows_match_the_data_file(self):
        for xmlid, name in shipped_row_names().items():
            self.assertEqual(
                self.env.ref("l10n_cz_vat_return." + xmlid).name, name, xmlid)

    def test_captions(self):
        names = shipped_row_names()
        self.assertEqual(
            names["dphdp3_ld_obrat23"],
            "Základ daně — základní sazba — Dodání zboží nebo poskytnutí "
            "služby s místem plnění v tuzemsku")
        self.assertEqual(names["dphdp3_ld_dano_da"], "Vlastní daň (62 – 63)")
        self.assertTrue(names["dphdp3_ld_odkr_zdp5"].startswith(
            "Krácený odpočet — snížená sazba — "))

    def test_placeholder_rule(self):
        for old in ("R1 tax_base", "R40 in_full_amount", "R52A coefficient",
                    "R66 value"):
            self.assertTrue(is_shipped_placeholder(old), old)
        self.assertFalse(is_shipped_placeholder("Tržby 21 %"))
        self.assertFalse(is_shipped_placeholder("Vlastní daň (62 – 63)"))

    def test_migration_replaces_placeholders_and_keeps_user_names(self):
        obrat = self.env.ref("l10n_cz_vat_return.dphdp3_ld_obrat23")
        dan = self.env.ref("l10n_cz_vat_return.dphdp3_ld_dan23")
        caption = obrat.name
        obrat.name = "R1 tax_base"
        dan.name = "Daň 21 % (moje)"
        ver = obrat.version_id
        ret = self.env["cssk.vat.return"].create({
            "version_id": ver.id,
            "statement_type_id": ver.statement_type_ids[:1].id,
            "date_from": "2026-10-01", "date_to": "2026-10-31",
            "period_type": "month",
        })
        line = self.env["cssk.vat.return.line"].create({
            "return_id": ret.id, "code": "obrat23", "name": "R1 tax_base",
            "kind": "tags"})
        typed = self.env["cssk.vat.return.line"].create({
            "return_id": ret.id, "code": "dan23", "name": "moje", "kind": "tags"})
        self.env.flush_all()
        spec = importlib.util.spec_from_file_location(
            "cz_vat_1_15_0", file_path(
                "l10n_cz_vat_return/migrations/19.0.1.15.0/post-migration.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.migrate(self.env.cr, "19.0.1.14.1")
        self.env.invalidate_all()
        self.assertEqual(obrat.name, caption)
        self.assertEqual(dan.name, "Daň 21 % (moje)")
        self.assertEqual(line.name, caption)
        self.assertEqual(typed.name, "moje")
