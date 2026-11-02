# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Drop ``edi_message_message_id_direction_unique``.

A Peppol ``message_id`` is the SENDER's invoice number, so two suppliers'
2026001 are two legitimate inbound rows — and the index refused the second
one, with the inbound poll failing on a document that is not a duplicate.
19.0 never created the index (``_sql_constraints`` is not read there), which
is why the dedup fix landed there without touching the schema; here it has to
go. Duplicates are decided in ``_inbound_duplicate_domain`` instead.

Removing the declaration is enough on a module update — the obsolete
``ir.model.constraint`` row is unlinked and its constraint dropped — but only
as a side effect of the data cleanup. This states it.
"""


def migrate(cr, version):
    cr.execute("""
        ALTER TABLE edi_message
        DROP CONSTRAINT IF EXISTS edi_message_message_id_direction_unique
    """)
    cr.execute("""
        DELETE FROM ir_model_constraint
        WHERE name = 'edi_message_message_id_direction_unique'
    """)
