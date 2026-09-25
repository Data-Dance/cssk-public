# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import SUPERUSER_ID, api
from odoo.tools.convert import convert_file

_logger = logging.getLogger(__name__)

#: The two version records whose grids and validity this release rewrites, and
#: the files that define them.
FILES = (
    "data/cssk_vat_return_version_data.xml",
    "data/cssk_vat_return_2024_version_data.xml",
)
VERSIONS = ("dph_version_2024", "dph_version_2025")


def migrate(cr, version):
    """Carry the rewritten form grids into a database that already has them.

    Both version records are ``noupdate="1"`` — deliberately, so an accountant
    may correct a line without the next upgrade reverting it — so an ordinary
    upgrade changes nothing about them, and every existing company would keep
    filing its pre-July periods on the 2025 grid. That IS the defect this
    release fixes, so the fix has to be carried over on purpose.

    **Flipping ``ir_model_data.noupdate`` does not do it, which is worth
    recording because it is the obvious move and it fails silently.** The gate
    is in ``convert.py``::

        if self.noupdate and self.mode != 'init':
            return

    ``self.noupdate`` there is the FILE's ``<data noupdate="1">`` attribute, not
    the database row. The row is a second, later check; the file-level one
    returns first and the record is never even looked up. A migration that
    clears the flag and waits for the update pass reports success, logs the rows
    it touched, and leaves the data exactly as it was — this one did, and the
    only thing that caught it was a test asserting the new ``valid_to``.

    So the file is re-applied here explicitly, in ``init`` mode, which is the
    mode the gate lets through.

    **The children have to go first.** ``line_def_ids`` and
    ``statement_type_ids`` arrive as ``(0, 0, {...})`` commands, and ``(0, 0)``
    always CREATES: re-applying over existing children appends a second full
    grid instead of replacing the first — the same trap as ``_load_data`` on a
    chart template. Every line would then be counted twice, which reads as a
    doubled rate rather than a duplicated row.

    Line definitions are safe to delete: nothing points at them, they are read
    when a return computes. **Submission types are not** — a filed
    ``cssk.vat.return`` references one through ``statement_type_id``, so they
    are deduplicated after the fact instead, keeping the lowest id, which is the
    row the existing statements already reference.

    Statements already computed keep their stored line values. Those are the
    numbers that were filed and must not move behind anyone's back; recompute a
    return deliberately to pick up the corrected placement.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    versions = env["cssk.vat.return.version"].browse([
        env["ir.model.data"]._xmlid_to_res_id(
            "l10n_sk_vat_return.%s" % name, raise_if_not_found=False)
        for name in VERSIONS
    ]).exists()
    if not versions:
        # Fresh install, or the records were removed by hand: the ordinary data
        # pass creates them from the files and there is nothing to carry over.
        return

    dropped = len(versions.line_def_ids)
    versions.line_def_ids.unlink()
    _logger.info(
        "l10n_sk_vat_return: dropped %s stale line definition(s) so the "
        "re-applied grids replace them instead of doubling them", dropped,
    )

    for filename in FILES:
        convert_file(env, "l10n_sk_vat_return", filename, None, mode="init")

    cr.execute(
        """
        DELETE FROM cssk_vat_return_type t
              USING cssk_vat_return_type keep
              WHERE t.version_id = keep.version_id
                AND t.code = keep.code
                AND t.id > keep.id
        """
    )
    if cr.rowcount:
        _logger.info(
            "l10n_sk_vat_return: removed %s duplicate submission type(s) left "
            "by the re-applied version data", cr.rowcount,
        )

    versions.invalidate_recordset()
    for record in versions:
        _logger.info(
            "l10n_sk_vat_return: %s now valid %s..%s with %s lines",
            record.name, record.valid_from, record.valid_to or "—",
            len(record.line_def_ids),
        )
