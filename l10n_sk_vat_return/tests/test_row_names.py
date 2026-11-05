# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import importlib.util

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools.misc import file_path

from odoo.addons.l10n_sk_vat_return.row_names import shipped_row_names


def _load_migration():
    spec = importlib.util.spec_from_file_location(
        "sk_vat_1_15_0", file_path(
            "l10n_sk_vat_return/migrations/19.0.1.15.0/post-migration.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@tagged("post_install", "-at_install")
class TestRowNames(TransactionCase):
    """The database carries the captions of the data files, and the 1.15.0
    migration moves 1.14.2's names to them without touching a user's."""

    def test_database_rows_match_the_data_files(self):
        for xmlid, names in shipped_row_names().items():
            ver = self.env.ref("l10n_sk_vat_return." + xmlid)
            self.assertEqual(
                {d.code: d.name for d in ver.line_def_ids}, names, xmlid)

    def test_frozen_previous_names_cover_every_row(self):
        previous = _load_migration().previous_names()
        current = shipped_row_names()
        self.assertEqual(set(previous), set(current))
        for xmlid in current:
            self.assertEqual(set(previous[xmlid]), set(current[xmlid]), xmlid)

    def test_migration_replaces_shipped_names_and_keeps_user_names(self):
        mig = _load_migration()
        previous = mig.previous_names()["dph_version_2025"]
        ver = self.env.ref("l10n_sk_vat_return.dph_version_2025")
        by_code = {d.code: d for d in ver.line_def_ids}
        captions = {c: d.name for c, d in by_code.items()}
        by_code["r03"].name = previous["r03"]           # 1.14.2
        by_code["r33"].name = "r33 — Nadmerný odpočet (§79/2)"  # before 1.14.2
        by_code["r05"].name = "r05"                      # before 1.14.2
        by_code["r04"].name = "r04 — Daň 23 % (moje)"    # a user's
        by_code["r06"].name = "r17 — Daň celkom"        # a user's, shaped
                                                         # like another row's
        ret = self.env["cssk.vat.return"].create({
            "version_id": ver.id,
            "statement_type_id": ver.statement_type_ids[:1].id,
            "date_from": "2026-10-01", "date_to": "2026-10-31",
            "period_type": "month",
        })
        line = self.env["cssk.vat.return.line"].create({
            "return_id": ret.id, "code": "r03", "name": previous["r03"],
            "kind": "tags"})
        typed = self.env["cssk.vat.return.line"].create({
            "return_id": ret.id, "code": "r04", "name": "moja poznámka",
            "kind": "tags"})
        self.env.flush_all()
        mig.migrate(self.env.cr, "19.0.1.14.2")
        self.env.invalidate_all()
        self.assertEqual(by_code["r03"].name, captions["r03"])
        self.assertEqual(by_code["r33"].name, captions["r33"])
        self.assertEqual(by_code["r05"].name, captions["r05"])
        self.assertEqual(by_code["r04"].name, "r04 — Daň 23 % (moje)")
        self.assertEqual(by_code["r06"].name, "r17 — Daň celkom")
        self.assertEqual(line.name, captions["r03"])
        self.assertEqual(typed.name, "moja poznámka")
