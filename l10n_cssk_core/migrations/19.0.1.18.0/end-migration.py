# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Move the retired *Registration Info* into Odoo's ``trade_registry``.

``end``, not ``post``: ``trade_registry`` comes from l10n_sk / l10n_cz, which
core does not depend on, so from core's post-migration it may not be loaded
yet. At ``end`` every module in the graph is.
"""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].with_context(active_test=False).search([])
    changed = companies._cssk_retire_registration_info()
    if changed:
        _logger.info(
            "Registration Info copied into Trade registry for: %s",
            ", ".join(changed.mapped("name")))
