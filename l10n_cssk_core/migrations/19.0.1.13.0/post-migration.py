# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Install ``l10n_cssk_payment_symbols`` where core used to pull it in.

19.0.1.13.0 drops core's dependency on the symbols module. The dependency
existed only because the VS/KS/SS fields (``l10n_cssk_variable_symbol`` and
siblings on ``account.move``) lived in core until 19.0.1.3.0. Any database that
went through 19.0.1.3.0 already has the symbols module installed, and dropping a
dependency never uninstalls anything, so for those this script does nothing.

THE DATABASE IT EXISTS FOR is one still on a core older than 19.0.1.3.0 that
upgrades straight to this version. There the fields are reflected under
``l10n_cssk_core`` xmlids only. Core no longer defines them, so at the end of
the upgrade ``ir.model.data._process_end`` deletes those ``ir.model.fields``
rows, and deleting a stored field DROPS ITS COLUMN. Every symbol ever entered
would be gone. It would not be hidden; it would be gone.

Marking the symbols module ``to install`` here prevents that: STEP 3 of
``load_modules`` loops until no module is left in ``to install``, so it loads
in this same run, reflects the same fields under its own xmlids, and
``_process_end`` then removes only core's xmlid and keeps the field.

``post``, NOT ``end``: end-scripts run at STEP 3.5, after that loop has
finished, so a module marked from there would not load until the next restart,
after the columns had already been dropped.

If the symbols module is not on the addons path at all, the upgrade is refused
while the columns hold data. Dropping them silently is the one outcome this
script exists to rule out.
"""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

SYMBOLS_MODULE = "l10n_cssk_payment_symbols"
SYMBOL_COLUMNS = (
    "l10n_cssk_variable_symbol",
    "l10n_cssk_constant_symbol",
    "l10n_cssk_specific_symbol",
)


def _columns_with_data(cr):
    found = []
    for column in SYMBOL_COLUMNS:
        cr.execute("""
            SELECT 1 FROM information_schema.columns
             WHERE table_name = 'account_move' AND column_name = %s
        """, (column,))
        if not cr.fetchone():
            continue
        cr.execute(
            "SELECT 1 FROM account_move WHERE %s IS NOT NULL LIMIT 1" % column)
        if cr.fetchone():
            found.append(column)
    return found


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    module = env["ir.module.module"].search([("name", "=", SYMBOLS_MODULE)])
    if module.state in ("installed", "to upgrade", "to install"):
        return
    if module.state == "uninstalled":
        module.button_install()
        _logger.info(
            "l10n_cssk_core: %s was not installed; marked for installation so "
            "the payment-symbol fields formerly in core keep their columns",
            SYMBOLS_MODULE)
        return
    columns = _columns_with_data(cr)
    if columns:
        raise RuntimeError(
            "Upgrading l10n_cssk_core from %s: core no longer depends on %s, "
            "which is not available on this server (state: %s). This upgrade "
            "would drop "
            "account_move.%s and the payment symbols stored in them. Put %s on "
            "the addons path, update the apps list, and upgrade again." % (
                version, SYMBOLS_MODULE, module.state or "not found",
                ", account_move.".join(columns), SYMBOLS_MODULE))
