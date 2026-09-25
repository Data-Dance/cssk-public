# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Collapse Czech submission types onto one row per code, before the load.

PRE, not post, and in this module rather than in ``l10n_cssk_kv_kh_base``.
Both placements are the fix for the same mistake: the base module's
post-migration ran before this module's data file had created anything to
collapse onto, matched nothing, and reported success.

Running here and early inverts it. The survivor is chosen from the rows that
already exist, the other rows' filings are moved onto it, and it is given the
xmlid this module is about to declare — so the data load that follows UPDATES
it instead of inserting a fourth copy.
"""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

XMLIDS = {'B': 'cz_kh_type_B', 'O': 'cz_kh_type_O', 'E': 'cz_kh_type_E'}


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    country = env.ref("base.cz", raise_if_not_found=False)
    if not country:
        return
    kept, removed, remapped = env[
        "cssk.control.statement.type"
    ]._cssk_collapse_to_one_per_code(country, "l10n_cz_kh", XMLIDS)
    _logger.info(
        "l10n_cz_kh 19.0.1.6.1: Czech submission types collapsed to %s "
        "(%s removed, %s filing(s) remapped)", kept, removed, remapped)
