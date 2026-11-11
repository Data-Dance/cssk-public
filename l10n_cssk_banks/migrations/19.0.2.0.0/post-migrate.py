# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Remove what the 2023 data set (l10n_banks_cz_sk 19.0.1.0.0) shipped and the
registries do not support.

That data carried hand-collected addresses, phones and e-mails, and a few BICs
that belonged to a parent bank (ČSOB Stavební spořitelna had ČSOB's
``CEKOCZPP``) or were malformed. Neither registry publishes contact details, and
several of the banks have since changed name — Poštová banka's address is not
that of ČSOB's run-off code 6500.

A field is cleared only while it still holds EXACTLY the value shipped in
2023 (``legacy_2023.csv``); anything a user typed in is kept. Banks that left
the registry are not touched here: they are archived as they were.

Runs once, on the upgrade that crosses 19.0.2.0.0 — that is, on a database
renamed from ``l10n_banks_cz_sk`` by ``tools/rename_banks_cz_sk.sh``.
"""

import csv
import logging
import os

from odoo import SUPERUSER_ID, api

from odoo.addons.l10n_cssk_banks.hooks import MODULE, shipped_banks

_logger = logging.getLogger(__name__)

FIELDS = ("street", "city", "phone", "email", "bic")


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    shipped = shipped_banks()
    path = os.path.join(os.path.dirname(__file__), "legacy_2023.csv")
    with open(path, encoding="utf8", newline="") as fh:
        legacy = {row["xmlid"]: row for row in csv.DictReader(fh)}
    cleared = 0
    for imd in env["ir.model.data"].search(
            [("module", "=", MODULE), ("model", "=", "res.bank")]):
        old = legacy.get(imd.name)
        if not old or imd.name not in shipped:
            continue
        bank = env["res.bank"].with_context(active_test=False).browse(imd.res_id).exists()
        if not bank:
            continue
        vals = {}
        for fname in FIELDS:
            if fname == "bic" and shipped[imd.name]["bic"]:
                continue  # the registry sync sets it
            if old[fname] and (bank[fname] or "").strip() == old[fname]:
                vals[fname] = False
        if vals:
            bank.write(vals)
            cleared += 1
    _logger.info("%s: cleared 2023 contact data/BICs on %d bank(s)", MODULE, cleared)
