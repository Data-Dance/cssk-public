# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Give every existing comparison row the parent it was created without.

``comparison_id`` is declared ``required=True``, but Odoo cannot make a new
required column NOT NULL on a table that already has rows — it adds the column
nullable and moves on, silently. That is exactly the failure this repo has been
bitten by before (four required fields left with NULL rows and no not-null), so
the constraint is added HERE, by hand, and only after the backfill has been
proved complete.

Grouping is on (res_model, res_id, basis) — the row's own uniqueness key minus
the row. ``basis`` is in it because the same filing is compared against more
than one right-hand side and those are separate comparisons, not one.

Runs post rather than pre: the ``cssk_filing_comparison`` table and the
``comparison_id`` column both have to exist first, and the ORM creates them
during the schema update that sits between the two hooks.
"""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """⚠️ ``(cr, version)``, NOT ``(env, version)``.

    Odoo checks the parameter NAMES, not just the arity —
    ``odoo/modules/migration.py`` accepts only ``('cr'|'_cr', 'version'|
    '_version')`` and raises TypeError otherwise, before running anything. An
    ``(env, version)`` script therefore takes the whole upgrade down: the
    schema update has already tried to apply this version's NOT NULL, found
    the nulls the migration was supposed to fill, and the transaction rolls
    back entire. Every other migration in this repo takes ``cr``; this one did
    not, and it cost a failed upgrade to find out. ``post_init_hook`` is the
    one that takes ``env`` in 19 — different hook, different signature.
    """
    cr.execute("""
        SELECT 1 FROM information_schema.tables
         WHERE table_name = 'cssk_filing_discrepancy'
    """)
    if not cr.fetchone():
        return

    # A NULL IN A KEY COLUMN IS NOT HYPOTHETICAL HERE. All three are declared
    # ``required=True``, but this repo has already found eleven modules where
    # Odoo never created the constraint and four required fields sitting on
    # NULL rows with no not-null — so "required" is not evidence. It matters
    # because GROUP BY treats NULLs as one group while the join below compares
    # them with ``=``, which is false for NULL: such a row would get a
    # comparison created for it and then fail to link to it, surfacing as an
    # orphan count with no hint of the cause.
    cr.execute("""
        SELECT COUNT(*) FROM cssk_filing_discrepancy
         WHERE comparison_id IS NULL
           AND (res_model IS NULL OR res_id IS NULL OR basis IS NULL)
    """)
    null_keyed = cr.fetchone()[0]
    if null_keyed:
        raise ValueError(
            "cssk.filing.discrepancy: %d row(s) have a NULL res_model, res_id "
            "or basis and cannot be assigned to a comparison. They are not "
            "deleted. Inspect them, set the missing key (basis defaults to "
            "'recomputed'), and re-run the upgrade." % null_keyed)

    # NOTE: no ``form_label``. It was dropped in 19.0.1.11.3 — the label is now
    # rendered from ``res_model`` per reader instead of stored per runner — and
    # a database upgrading from 19.0.1.10.5 straight to that version gets the
    # NEW schema before this script runs, so naming the column here would fail
    # on a table that no longer has it.

    # One parent per distinct (filing, basis). The descriptive columns are
    # copied off an arbitrary member of the group because they are constant
    # within it by construction — the upsert wrote them from the same source
    # onto every row of the comparison.
    cr.execute("""
        INSERT INTO cssk_filing_comparison (
            res_model, res_id, basis, basis_label, filing_name,
            legacy_source, company_id, date_from, date_to,
            create_uid, create_date, write_uid, write_date)
        SELECT d.res_model, d.res_id, d.basis,
               MIN(d.basis_label), MIN(d.filing_name),
               MIN(d.legacy_source), MIN(d.company_id),
               MIN(d.date_from), MIN(d.date_to),
               1, NOW() AT TIME ZONE 'UTC', 1, NOW() AT TIME ZONE 'UTC'
          FROM cssk_filing_discrepancy d
         WHERE d.comparison_id IS NULL
         GROUP BY d.res_model, d.res_id, d.basis
        ON CONFLICT (res_model, res_id, basis) DO NOTHING
    """)
    created = cr.rowcount

    # MIN() above picks one value per group for the descriptive columns. They
    # are constant within a group by construction — the upsert wrote all of
    # them onto every row from the same source — so this is a formality, but a
    # formality worth logging: if it ever is not true, the comparison silently
    # shows one of several values and nothing says so.
    cr.execute("""
        SELECT COUNT(*) FROM (
            SELECT 1 FROM cssk_filing_discrepancy
             GROUP BY res_model, res_id, basis
            HAVING COUNT(DISTINCT company_id) > 1
                OR COUNT(DISTINCT COALESCE(filing_name, '')) > 1
        ) AS inconsistent
    """)
    inconsistent = cr.fetchone()[0]
    if inconsistent:
        _logger.warning(
            "l10n_cssk_core: %d comparison group(s) had rows disagreeing "
            "about the company or the filing's name; one value was kept per "
            "group. The rows themselves are untouched.", inconsistent)

    cr.execute("""
        UPDATE cssk_filing_discrepancy d
           SET comparison_id = c.id
          FROM cssk_filing_comparison c
         WHERE d.comparison_id IS NULL
           AND c.res_model = d.res_model
           AND c.res_id = d.res_id
           AND c.basis = d.basis
    """)
    linked = cr.rowcount

    cr.execute("""
        SELECT COUNT(*) FROM cssk_filing_discrepancy WHERE comparison_id IS NULL
    """)
    orphans = cr.fetchone()[0]
    if orphans:
        # Refusing rather than dropping them: a comparison row carries an
        # accountant's answer, and there is no version of "tidy up" that is
        # allowed to discard one silently.
        raise ValueError(
            "cssk.filing.discrepancy: %d row(s) could not be given a "
            "comparison. They are not deleted; fix them and re-run the "
            "upgrade." % orphans)

    cr.execute("""
        ALTER TABLE cssk_filing_discrepancy
        ALTER COLUMN comparison_id SET NOT NULL
    """)

    # The rollup is a stored compute, and nothing has triggered it for rows
    # that existed before the parent did.
    env = api.Environment(cr, SUPERUSER_ID, {})
    comparisons = env["cssk.filing.comparison"].search([])
    comparisons._compute_cssk_rollup()
    comparisons.flush_recordset()

    _logger.info(
        "l10n_cssk_core: %d comparison(s) created, %d row(s) linked, "
        "%d rolled up", created, linked, len(comparisons))
