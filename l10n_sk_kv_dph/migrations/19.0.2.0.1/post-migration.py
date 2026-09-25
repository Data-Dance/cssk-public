# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Assert that the collapse actually happened.

The reason the broken version reached a commit is that it exited 0. The
pre-migration's "country filled on 12" was true and read like the job was
done; the only signal was an INFO line saying there was nothing to collapse.
**A no-op and a success are indistinguishable unless something is counted
afterwards**, so this counts.

Two post-conditions, both cheap:

* no code is declared twice for this country — the duplication itself;
* no filing points at a type with no xmlid — an orphan left behind by a
  collapse that ran halfway.

Either one failing raises, which turns a silent no-op into a failed upgrade.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    cr.execute("SELECT id FROM res_country WHERE code = 'SK'")
    row = cr.fetchone()
    if not row:
        return
    country_id = row[0]

    cr.execute("""
        SELECT code, count(*) FROM cssk_control_statement_type
         WHERE country_id = %s GROUP BY code HAVING count(*) > 1
    """, (country_id,))
    dupes = cr.fetchall()
    if dupes:
        raise ValueError(
            "l10n_sk_kv_dph 19.0.2.0.1: the submission-type collapse did not happen — "
            "%s still declared more than once for Slovak: %s. The filings are "
            "intact; re-run the upgrade once the cause is found."
            % (len(dupes), ", ".join("%s x%s" % d for d in dupes)))

    cr.execute("""
        SELECT count(*)
          FROM cssk_control_statement s
          JOIN cssk_control_statement_type t ON t.id = s.statement_type_id
         WHERE t.country_id = %s
           AND NOT EXISTS (SELECT 1 FROM ir_model_data d
                            WHERE d.model = 'cssk.control.statement.type'
                              AND d.res_id = t.id)
    """, (country_id,))
    orphaned = cr.fetchone()[0]
    if orphaned:
        raise ValueError(
            "l10n_sk_kv_dph 19.0.2.0.1: %s Slovak filing(s) still point at a submission "
            "type with no xmlid, so the collapse left them on an orphan. "
            "Nothing has been deleted; re-run the upgrade once the cause is "
            "found." % orphaned)

    cr.execute(
        "SELECT count(*) FROM cssk_control_statement_type WHERE country_id = %s",
        (country_id,))
    _logger.info(
        "l10n_sk_kv_dph 19.0.2.0.1: %s Slovak submission type(s), one per code, every "
        "filing on one of them", cr.fetchone()[0])
