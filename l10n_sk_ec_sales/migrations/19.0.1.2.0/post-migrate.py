# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Close the 2020 Súhrnný výkaz vintage off at its start date.

The module now ships two SV vintages, because FS SR publishes two schemas and
they are not the same document: ``zaznamCast2`` (the call-off-stock register
the Quick Fixes brought in on 1. 1. 2020) exists only in the later one, and
with it the page goes from 27 records to 12 + 12.

The NEW record loads by itself — ``noupdate="1"`` blocks updates, not
creations. What it cannot do is move the existing record, which still claims
2010 onwards and would go on offering the 2020 structure for a 2014 period.
So this narrows it to 2020-01-01 and renames it to say which vzor it is.

Deliberately does not touch a statement already filed against it. Its
``version_id`` stays, its filed XML stays, and its period is what it is; the
narrowing only governs which version a NEW statement may choose.
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """
        UPDATE cssk_ec_summary_statement_version v
           SET valid_from = DATE '2020-01-01',
               name = 'Súhrnný výkaz 2020 (od 1. 1. 2020)'
          FROM ir_model_data d
         WHERE d.model = 'cssk.ec.summary.statement.version'
           AND d.module = 'l10n_sk_ec_sales'
           AND d.name = 'sdv_version_2025'
           AND d.res_id = v.id
           AND v.valid_from < DATE '2020-01-01'
        """
    )
