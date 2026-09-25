# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Assign the control section on lines that predate the resolver.

A database that installed this module at 19.0.2.0.4 or earlier over existing
accounting holds ``cssk_control_section_code = False`` on every line: the
column was computed when ``l10n_cssk_kv_kh_base`` installed, before this
module's resolver was loaded. The install hook now recomputes; this carries
the same repair to the databases that already went through the install.
Idempotent — a line already classified correctly is left as it is.
"""

from odoo import SUPERUSER_ID, api

from odoo.addons.l10n_sk_kv_dph.hooks import _recompute_section_codes


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    _recompute_section_codes(env, "SK", "l10n_sk_kv_dph 19.0.2.0.5")
