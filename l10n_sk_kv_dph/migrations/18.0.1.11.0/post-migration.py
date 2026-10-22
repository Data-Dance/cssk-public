# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)

# (table, deducted column, tax column) — the rows whose XML carries an
# odpočítaná daň. B.1/B.2/C.2 are the received detail sections (attribute O,
# OR on C.2); B.3/B.3.1/B.3.2 are the simplified-invoice aggregates. The
# issued sections A.1/A.2/C.1 have no such attribute and no such column.
_TABLES = [
    ("l10n_sk_kv_dph_section_b1", "deducted_amount", "tax_amount"),
    ("l10n_sk_kv_dph_section_b2", "deducted_amount", "tax_amount"),
    ("l10n_sk_kv_dph_section_c2", "deducted_amount", "tax_amount"),
    ("l10n_sk_kv_dph_section_b3", "total_deducted_amount", "total_tax_amount"),
    ("l10n_sk_kv_dph_section_b31", "total_deducted_amount", "total_tax_amount"),
    ("l10n_sk_kv_dph_section_b32", "total_deducted_amount", "total_tax_amount"),
]


def migrate(cr, version):
    """Backfill the deduction on statements computed before 1.11.0.

    Until 1.11.0 the XML rendered attribute ``O`` (``OR``) straight from the
    tax charged, and ``deducted_amount`` was declared but never written — so
    every stored row holds 0.00. 1.11.0 renders from the field, which would
    make an already-computed statement export zeros the next time it is
    exported: a silent change to a filed figure, and the worst kind, because
    the statement was correct when it was computed.

    So carry the old rendering forward into the data: where the deduction is
    still zero and tax was charged, the row deducted the whole of it, which is
    exactly what it filed. Rows whose tax is itself zero are left alone —
    there is nothing to carry and 0.00 is the right answer.

    Idempotent, and it cannot overwrite a hand-set deduction: a row edited to
    a partial § 50 figure is non-zero and therefore not matched.
    """
    touched = 0
    for table, deducted, tax in _TABLES:
        cr.execute(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = %s AND column_name = %s",
            (table, deducted),
        )
        if not cr.fetchone():
            continue
        cr.execute(
            "UPDATE %s SET %s = %s "
            "WHERE COALESCE(%s, 0) = 0 AND COALESCE(%s, 0) <> 0"
            % (table, deducted, tax, deducted, tax)
        )
        touched += cr.rowcount
    _logger.info(
        "l10n_sk_kv_dph 1.11.0: carried the filed deduction into "
        "%s pre-existing control-statement row(s)", touched,
    )
