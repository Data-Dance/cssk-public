# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Make room for the unique keys that Odoo 19 never created.

The unique (employee_id, year, company_id) key on the annual tax
reconciliation was declared as ``_sql_constraints``, which Odoo 19 ignores,
so a database may already hold two reconciliations of one employee and year.
The new ``models.Constraint`` cannot be added over them, and Odoo only logs
that.

Duplicates are resolved conservatively, before the module loads:

* per key, the record to keep is the furthest along (posted, then computed,
  then draft) and, among equals, the most recently written one;
* the others are deleted only if NOT posted — a draft or computed
  reconciliation is recomputed from the payslips at the press of a button;
* posted duplicates are never deleted: they are logged, the constraint stays
  missing for that table, and the payroll officer decides.
"""
import logging

_logger = logging.getLogger(__name__)

STATE_RANK = "CASE state WHEN 'posted' THEN 2 WHEN 'computed' THEN 1 ELSE 0 END"


def _table_exists(cr, table):
    cr.execute("SELECT 1 FROM pg_class WHERE relname = %s AND relkind = 'r'",
               (table,))
    return bool(cr.fetchone())


def migrate(cr, version):
    if not version:
        return
    _check_rule_parameter_codes(cr)
    if not _table_exists(cr, "l10n_sk_tax_reconciliation"):
        return
    cr.execute(
        """
        WITH ranked AS (
            SELECT id, state,
                   ROW_NUMBER() OVER (
                       PARTITION BY employee_id, year, company_id
                       ORDER BY """ + STATE_RANK + """ DESC,
                                write_date DESC NULLS LAST, id DESC) AS rn
              FROM l10n_sk_tax_reconciliation
        )
        DELETE FROM l10n_sk_tax_reconciliation r
         USING ranked
         WHERE r.id = ranked.id
           AND ranked.rn > 1
           AND COALESCE(ranked.state, 'draft') <> 'posted'
        RETURNING r.id
        """
    )
    removed = [row[0] for row in cr.fetchall()]
    if removed:
        _logger.warning(
            "l10n.sk.tax.reconciliation: removed %d unposted duplicate(s) of "
            "an employee/year so the unique key can be created: ids %s",
            len(removed), removed)
    cr.execute(
        """
        SELECT employee_id, year, company_id, array_agg(id ORDER BY id)
          FROM l10n_sk_tax_reconciliation
         GROUP BY employee_id, year, company_id
        HAVING COUNT(*) > 1
        """
    )
    for employee_id, year, company_id, ids in cr.fetchall():
        _logger.error(
            "l10n.sk.tax.reconciliation: employee %s, year %s, company %s has "
            "several POSTED reconciliations %s; they were left alone and the "
            "unique key will not be created until one is removed.",
            employee_id, year, company_id, ids)


def _check_rule_parameter_codes(cr):
    """hr.rule.parameter.code got the same treatment. The parameters come
    from this module's data files, which cannot produce two rows per code,
    and the model had no screen until this version, so a duplicate would be a
    hand-made row: it is reported, not merged, because the values hanging off
    each row are the payroll's statutory history."""
    if not _table_exists(cr, "hr_rule_parameter"):
        return
    cr.execute(
        """
        SELECT code, array_agg(id ORDER BY id)
          FROM hr_rule_parameter
         GROUP BY code
        HAVING COUNT(*) > 1
        """
    )
    for code, ids in cr.fetchall():
        _logger.error(
            "hr.rule.parameter: code %r is used by several rows %s; the unique "
            "key will not be created until they are merged by hand.", code, ids)
