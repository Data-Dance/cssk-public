# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Carry the DIČ over from the three places it used to live.

``res.partner.l10n_sk_dic`` is now the only storage. Three columns fed it
before, and a database can carry any combination of them:

``res_partner.l10n_cssk_dic``
    The field's first home, in the shared CZ/SK base, on the premise that both
    countries needed it. Czech usage does not — there *DIČ* is the VAT number.

``res_company.l10n_sk_dic``
    A **plain stored Char** declared independently by
    ``l10n_sk_hr_payroll_prehlad`` and ``l10n_sk_hr_payroll_hlasenie``, each to
    be self-contained. Install one of those without this module and an
    accountant fills a real column; install this module afterwards and the
    merged field definition acquires ``related=``, the ORM stops reading that
    column, and the value goes invisible with nothing having moved it. That is
    the bug this hook exists for.

``res_company.income_tax_id``
    ``l10n_sk``'s own stored Char, which this module repoints at the partner.

Why a pre_init as well as a post_init
-------------------------------------

``income_tax_id`` becomes a **stored related** field. Whether Odoo blanks such a
column when a field changes from plain to computed during install is a detail
that has moved between versions, and a migration that depends on it is a
migration that silently loses the value on the version where it goes the other
way. So the values are copied into a scratch table *before* the new definitions
are in the registry, and applied afterwards. Belt and braces, deliberately:
this runs once per database and the thing it protects is a statutory identifier.

Removing a field never drops its column, so the old values are still sitting
there when we arrive.
"""

import logging

_logger = logging.getLogger(__name__)

BACKUP_TABLE = "l10n_sk_base_dic_migration"


def _column_exists(cr, table, column):
    cr.execute(
        """
        SELECT 1 FROM information_schema.columns
         WHERE table_name = %s AND column_name = %s
        """,
        (table, column),
    )
    return bool(cr.fetchone())


def pre_init_hook(env):
    """Stash every legacy DIČ before the new field definitions load.

    Takes ``env``, not ``cr``: Odoo 19 calls this as
    ``getattr(py_module, pre_init)(env)`` (``odoo/modules/loading.py:185``).
    Older majors passed the cursor, and the same hook written for one signature
    fails on the other with an ``AttributeError`` at install time.
    """
    cr = env.cr
    # DROP first, never IF NOT EXISTS: an install that aborted between the two
    # hooks can leave this table behind, and reusing its rows would restore a
    # DIČ that has since been corrected. The stash is only ever valid for the
    # install that wrote it.
    cr.execute(f"DROP TABLE IF EXISTS {BACKUP_TABLE}")
    cr.execute(
        f"""
        CREATE TABLE {BACKUP_TABLE} (
            partner_id integer PRIMARY KEY,
            dic        varchar
        )
        """
    )
    # Company-side columns, resolved to the company's partner. Priority is
    # explicit rather than incidental: l10n_sk's own field first, the payroll
    # modules' column second. They are the same number whenever both are set,
    # and ON CONFLICT DO NOTHING keeps the first non-empty one either way.
    for column in ("income_tax_id", "l10n_sk_dic"):
        if not _column_exists(cr, "res_company", column):
            continue
        cr.execute(
            f"""
            INSERT INTO {BACKUP_TABLE} (partner_id, dic)
                 SELECT c.partner_id, c.{column}
                   FROM res_company c
                  WHERE COALESCE(c.{column}, '') != ''
                    AND c.partner_id IS NOT NULL
            ON CONFLICT (partner_id) DO NOTHING
            """
        )
        _logger.info(
            "l10n_sk_base: stashed %s DIČ value(s) from res_company.%s.",
            cr.rowcount, column,
        )


def post_init_hook(env):
    """Apply the stashed values, then the partner-side legacy column."""
    cr = env.cr

    # 1. The company-side values saved by pre_init_hook.
    cr.execute("SELECT to_regclass(%s)", (BACKUP_TABLE,))
    if cr.fetchone()[0]:
        cr.execute(
            f"""
            UPDATE res_partner p
               SET l10n_sk_dic = b.dic
              FROM {BACKUP_TABLE} b
             WHERE p.id = b.partner_id
               AND COALESCE(p.l10n_sk_dic, '') = ''
            """
        )
        _logger.info(
            "l10n_sk_base: restored %s DIČ value(s) onto company partners.",
            cr.rowcount,
        )
        cr.execute(f"DROP TABLE {BACKUP_TABLE}")

    # 2. The partner-side legacy column. Only where the new field is still
    #    empty: a value entered after the upgrade must win over a legacy one.
    if _column_exists(cr, "res_partner", "l10n_cssk_dic"):
        cr.execute(
            """
            UPDATE res_partner
               SET l10n_sk_dic = l10n_cssk_dic
             WHERE COALESCE(l10n_cssk_dic, '') != ''
               AND COALESCE(l10n_sk_dic, '') = ''
            """
        )
        _logger.info(
            "l10n_sk_base: carried %s DIČ value(s) over from l10n_cssk_dic.",
            cr.rowcount,
        )

    # 3. Reconcile the stored related with the rows we wrote behind the ORM.
    #
    #    Raw SQL bypasses both the cache and the dependency graph, so neither
    #    knows res_partner.l10n_sk_dic moved. invalidate_all() drops the stale
    #    cache; add_to_compute() then forces income_tax_id to be recomputed for
    #    every company, which is what actually refills its column.
    #
    #    Not `companies.modified(["income_tax_id"])`: modified() marks the
    #    fields that DEPEND ON the ones named, so naming income_tax_id there
    #    schedules its dependents and leaves income_tax_id itself untouched —
    #    the column would keep whatever it held and silently disagree with the
    #    partner.
    env.invalidate_all()
    companies = env["res.company"].sudo().search([])
    if companies:
        env.add_to_compute(companies._fields["income_tax_id"], companies)
    env.flush_all()
