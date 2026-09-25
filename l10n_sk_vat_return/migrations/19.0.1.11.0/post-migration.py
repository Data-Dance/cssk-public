# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Add ``r_deduction_total`` to the version records of existing databases.

New in 1.11.0. Adding a line to a version's ``line_def_ids`` in the data files
does NOT reach an existing database: measured on a 1.10.0 copy of the
validation DB, all five version records still lacked the line after the
upgrade, and this migration is what put it on them. (The 2024 file is
``noupdate="1"``; the other two are not, and a one2many member added to an
already-loaded record is not re-created either way.) Same shape as the lesson
19.0.1.7.0 documents — an edit that tests green on a clean database and leaves
the shared one untouched.

The line is a rate-agnostic deduction total (both rates, excluding r29/r30).
It exists so a legacy filing that carries "odpočítaná daň celkom" as ONE
number has something correct to be compared against: mapped onto a single
per-rate half instead, it agrees on an agenda whose purchases are all
standard-rated and silently drops every reduced-rate deduction.

Purely additive — ``r_net`` still reads the two halves, no computed figure
moves, and no filing changes. Idempotent.
"""
import logging

_logger = logging.getLogger(__name__)

# The halves are named by a convention, not a hardcoded table per vzor. An
# earlier draft of this migration carried one, and it was the same defect it
# exists to repair: the formula written in two places, the data file and here,
# free to drift. Deriving it means there is one rule — "sum every per-rate
# half this version defines" — stated identically by the data file, this
# migration and the test.
#
# The convention is that a deduction half is a line code ending in ``_total``.
# True of every SK vzor: r20_total/r21_total on the legacy forms,
# r18_total/r19_total on DPHv21, plus r18a_total from 2025. A future vintage
# introducing a ``_total`` code that is NOT a deduction half has to revisit
# this, the data files and the test together.
_CODE = "r_deduction_total"
_NAME = "(internal) odpočet celkom — obe sadzby"


def _halves(version):
    return sorted(
        c for c in version.line_def_ids.mapped("code")
        if c.endswith("_total") and c != _CODE
    )


def migrate(cr, version):
    from odoo import SUPERUSER_ID, api

    env = api.Environment(cr, SUPERUSER_ID, {})
    Def = env["cssk.vat.return.line.def"]
    added = 0
    for ver in env["cssk.vat.return.version"].search(
            [("country_id.code", "=", "SK")]):
        if ver.line_def_ids.filtered(lambda d: d.code == _CODE):
            continue
        halves = _halves(ver)
        if not halves:
            # No per-rate halves to sum. Not ours to invent one — leave the
            # version exactly as it was and say so.
            _logger.warning(
                "l10n_sk_vat_return 1.11.0: %s defines no deduction halves, "
                "skipping %s", ver.name, _CODE,
            )
            continue
        # After the halves and before r_net, matching the data files.
        sequence = max(ver.line_def_ids.filtered(
            lambda d: d.code in halves).mapped("sequence")) + 1
        Def.create({
            "version_id": ver.id,
            "code": _CODE,
            "name": _NAME,
            "kind": "aggregate",
            "aggregate_formula": " + ".join(halves),
            "sequence": sequence,
        })
        added += 1
    _logger.info(
        "l10n_sk_vat_return 1.11.0: added %s to %s version record(s)",
        _CODE, added,
    )
