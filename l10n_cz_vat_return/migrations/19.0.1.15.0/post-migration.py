# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Give every DPHDP3 row the caption of the form.

Until 1.15.0 the rows were named "R1 tax_base", "R40 in_full_amount" and so
on. 1.15.0 names them as vyhláška č. 387/2025 Sb., příloha č. 1, does. The
records are ``noupdate``, so an existing database gets the captions only from
here. A definition, and a line of an existing return, is renamed only while
it holds a placeholder an earlier release shipped; a name a user typed is kept.
Same rules as l10n_sk_vat_return 1.14.2 / 1.15.0. Idempotent.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    from odoo import SUPERUSER_ID, api

    from odoo.addons.l10n_cz_vat_return.row_names import (
        is_shipped_placeholder,
        shipped_row_names,
    )

    env = api.Environment(cr, SUPERUSER_ID, {})
    renamed = kept = lines = 0
    for xmlid, caption in shipped_row_names().items():
        ldef = env.ref("l10n_cz_vat_return." + xmlid, raise_if_not_found=False)
        if not ldef:
            continue
        returns_lines = env["cssk.vat.return.line"].search([
            ("return_id.version_id", "=", ldef.version_id.id),
            ("code", "=", ldef.code),
        ]).filtered(lambda ln: is_shipped_placeholder(ln.name))
        returns_lines.name = caption
        lines += len(returns_lines)
        if ldef.name == caption:
            continue
        if is_shipped_placeholder(ldef.name):
            ldef.name = caption
            renamed += 1
        else:
            kept += 1
    _logger.info(
        "l10n_cz_vat_return 1.15.0: %d DPHDP3 rows and %d return lines renamed "
        "to the form caption, %d user-named rows kept", renamed, lines, kept)
