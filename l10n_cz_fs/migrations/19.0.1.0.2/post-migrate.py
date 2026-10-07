# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Declare, on existing databases, that these forms have no published XSD.

``_validate_against_schema`` was tightened to refuse an export it could not
validate — right, because a KV DPH once exported unvalidated and looked as
though it had passed. It broke every financial-statement export where no
schema exists to load, which is a published fact about the form and not a
missing file: the Czech statements are filed as attachments inside the DPPO
envelope and the Finanční správa publishes no standalone schema for any
of them.

The version record now carries ``xml_schema_optional`` to say so, but those
records live in a ``noupdate="1"`` data file, so a module upgrade will NOT
rewrite them — an existing database would take the fix and stay broken, with
the failure appearing only when somebody tries to file. Hence this.

Deliberately does not touch a version that HAS a schema, and does not create
the flag anywhere it was not already true.
"""

XMLIDS = ['rozvaha_version_2025', 'vysledovka_version_2025', 'cashflow_version_2025', 'equity_changes_version_2025']


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """
        UPDATE cssk_fs_statement_version v
           SET xml_schema_optional = TRUE
          FROM ir_model_data d
         WHERE d.model = 'cssk.fs.statement.version'
           AND d.module = %s
           AND d.name = ANY(%s)
           AND d.res_id = v.id
           AND COALESCE(v.xml_schema_optional, FALSE) = FALSE
        """,
        ('l10n_cz_fs', list(XMLIDS)),
    )
