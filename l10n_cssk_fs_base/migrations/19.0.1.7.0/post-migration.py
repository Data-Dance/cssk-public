# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Mark the rows of existing statements with their part of the document.

A recompute sets ``in_movement_section``; statements computed before it
existed would otherwise show an empty Income statement view. Written with SQL
because historical filings are closed to ORM writes by design, and this is a
presentation flag, not a change to anything that was filed.
"""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    movement_ids = []
    statements = env["cssk.fs.statement"].with_context(active_test=False).search([])
    for st in statements:
        defs = {d.code: d for d in st.version_id.line_def_ids}
        for line in st.line_ids:
            root, seen = line, set()
            while root.parent_id and root.id not in seen:
                seen.add(root.id)
                root = root.parent_id
            ldef = defs.get(root.code)
            if ldef and ldef._cssk_reads_movement():
                movement_ids.append(line.id)
    cr.execute("UPDATE cssk_fs_statement_line SET in_movement_section = FALSE")
    if movement_ids:
        cr.execute(
            "UPDATE cssk_fs_statement_line SET in_movement_section = TRUE "
            "WHERE id = ANY(%s)", (movement_ids,))
    _logger.info("Marked %d statement row(s) of %d statement(s) as the "
                 "movement part", len(movement_ids), len(statements))
