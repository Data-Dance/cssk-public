# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Give every submission type its country BEFORE the column turns NOT NULL.

``cssk.control.statement.type.country_id`` is ``required=True``, so the schema
update adds a NOT NULL constraint. Odoo adds one only if no existing row
violates it — and silently declines, leaving the column nullable, if any does.
Every existing row would: the field is new. So the column is created and filled
here, in pre-migration, from the country of the version the type used to hang
off. The ORM then finds it populated and the constraint lands.

``version_id`` is deliberately NOT dropped here. The post-migration still needs
it to tell duplicates apart, and a pre-migration that drops it would take the
only evidence of which country a type belonged to with it.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        ALTER TABLE cssk_control_statement_type
          ADD COLUMN IF NOT EXISTS country_id integer
    """)
    cr.execute("""
        UPDATE cssk_control_statement_type t
           SET country_id = v.country_id
          FROM cssk_control_statement_version v
         WHERE v.id = t.version_id
           AND t.country_id IS NULL
    """)
    filled = cr.rowcount
    cr.execute("""
        SELECT count(*) FROM cssk_control_statement_type
         WHERE country_id IS NULL
    """)
    orphaned = cr.fetchone()[0]
    _logger.info(
        "l10n_cssk_kv_kh_base 19.0.2.0.0: country filled on %s submission "
        "type(s); %s still without one", filled, orphaned)
    if orphaned:
        # Raised, not warned. ``country_id`` is required, so the schema update
        # that follows will try to apply NOT NULL and fail on these rows —
        # somewhere further on, with an error that names a constraint rather
        # than a cause. Failing here says what is actually wrong while the
        # transaction can still be rolled back. Guessing a country instead
        # would put a filing on the wrong form family, which is worse than
        # stopping.
        cr.execute("""
            SELECT id, code FROM cssk_control_statement_type
             WHERE country_id IS NULL ORDER BY id
        """)
        rows = ", ".join("id=%s code=%s" % r for r in cr.fetchall())
        raise ValueError(
            "l10n_cssk_kv_kh_base 19.0.2.0.0: %s submission type(s) have no "
            "country and no version to derive one from, so country_id cannot "
            "be made required: %s. Give each a country, or delete it if it "
            "carries no filings, then re-run the upgrade." % (orphaned, rows))
