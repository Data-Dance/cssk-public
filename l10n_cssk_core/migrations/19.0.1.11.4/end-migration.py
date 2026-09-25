# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""⚠️ `end`, NOT `post`, and the reason is the whole point of this file.

``res_model`` is a Selection now, so a stored value the registry does not know
renders as the raw model name rather than a label. That is not an error — a
module can legitimately be uninstalled — but it is invisible, and a screen
quietly showing ``cssk.vat.return`` where a name used to be is exactly the class
of thing the change to a Selection was made to stop.

THE FIRST VERSION OF THIS CHECK LIVED IN `post` AND COULD NEVER BE TRUE. A
module's post-migration runs while only that module and its DEPENDENCIES are
loaded. ``cssk.vat.return`` lives in ``l10n_cssk_vat_return_base``, which depends
on core and therefore loads *later* — so from core's own post-migration the
registry has never heard of it, and the check reported every perfectly healthy
database as broken:

    cssk_filing_comparison has rows on model(s) the registry does not know
    (cssk.vat.return, cssk.control.statement, cssk.income.tax.return)

All three were installed. It fired on every table, on every database, on every
upgrade, and told the reader the opposite of the truth. Same family as the
migrate-arity bug earlier in this work: correct code placed where it cannot
observe the thing it is asking about.

``end`` scripts run at ``load_modules`` STEP 3.5, after every module in the
graph has been loaded — immediately after Odoo's own "check that all installed
modules have been loaded by the registry". That is the earliest point at which
this question can be asked honestly.
"""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

TABLES = ("cssk_filing_comparison", "cssk_filing_discrepancy")


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    known = [name for name, cls in env.registry.items()
             if not cls._abstract and hasattr(cls, "_cssk_form_label")]
    if not known:
        # No submission model is installed at all; there is nothing this could
        # usefully say, and saying it anyway is what the previous version did.
        return
    for table in TABLES:
        cr.execute("""
            SELECT 1 FROM information_schema.tables WHERE table_name = %s
        """, (table,))
        if not cr.fetchone():
            continue
        cr.execute(
            "SELECT DISTINCT res_model FROM %s "
            " WHERE res_model IS NOT NULL AND res_model <> ALL(%%s)" % table,
            (known,))
        unknown = sorted(r[0] for r in cr.fetchall())
        if unknown:
            _logger.warning(
                "l10n_cssk_core: %s holds rows on model(s) that are not "
                "installed (%s). Their Form column shows the raw model name "
                "until those modules are installed again; the rows themselves "
                "are untouched.", table, ", ".join(unknown))
