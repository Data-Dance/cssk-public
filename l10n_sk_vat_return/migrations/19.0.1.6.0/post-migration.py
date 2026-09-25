# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The pre-July grid claimed 2011; it covers DPHv21, which starts 2021.

The record is `noupdate="1"`, so editing `valid_from` in the data file reaches
a FRESH install and nothing else — verified the hard way: the change tested
green on a new database while the shared spike still read 2011-01-01, and a
peer found it there rather than me.

The rule this implements: **a version claims only the periods whose XSD we
hold.** `data/dph2021.xsd` is DPHv21 and `data/dph2025.xsd` is DPHv25; we hold
nothing earlier, so periods before 2021 now resolve to no version. That is the
intended outcome, not a regression — a computed figure nobody can validate
against a form is worth less than a visible gap.

Widening is deliberately guarded against: only a `valid_from` EARLIER than
2021-01-01 is moved, so a company that has narrowed it further keeps its own.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute(
        """
        UPDATE cssk_vat_return_version v
           SET valid_from = %s
          FROM ir_model_data d
         WHERE d.model = 'cssk.vat.return.version'
           AND d.module = 'l10n_sk_vat_return'
           AND d.name = 'dph_version_2024'
           AND d.res_id = v.id
           AND v.valid_from < %s
        """,
        ("2021-01-01", "2021-01-01"),
    )
    if cr.rowcount:
        _logger.info(
            "l10n_sk_vat_return: the pre-July grid now starts 2021-01-01, "
            "which is what dph2021.xsd covers — it claimed 2011")
