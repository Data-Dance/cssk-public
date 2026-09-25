# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Drop the axis the submission types used to hang on.

**The collapse itself is NOT here, and that is the fix.** It was, and it
collapsed nothing: the surviving records are declared by a COUNTRY module's
data file, and a country module depends on this one and therefore loads after
it. A post-migration in a base module cannot see records a dependent module has
not created yet. The query matched no pairs, logged "nothing to collapse" and
exited 0 — leaving 15 type records where there had been 12, every filing on an
orphan, and the symptom it was written to remove still on screen.

It now lives in each country module's PRE-migration, where the rows it needs
already exist: ``l10n_sk_kv_dph`` and ``l10n_cz_kh``, both calling
``cssk.control.statement.type._cssk_collapse_to_one_per_code``. Each asserts
its own outcome afterwards, because the failure mode here was a no-op that
reads exactly like a success.

What is left here is the one step that genuinely belongs to the base module and
must happen before any country module runs: dropping ``version_id``. Nothing
downstream reads it — the collapse works off ``country_id`` and ``code``.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        SELECT count(*) FROM information_schema.columns
         WHERE table_name = 'cssk_control_statement_type'
           AND column_name = 'version_id'
    """)
    if not cr.fetchone()[0]:
        return
    cr.execute("""
        ALTER TABLE cssk_control_statement_type DROP COLUMN version_id
    """)
    _logger.info(
        "l10n_cssk_kv_kh_base 19.0.2.0.1: submission types no longer hang off "
        "a form version; the country modules collapse their own duplicates")
