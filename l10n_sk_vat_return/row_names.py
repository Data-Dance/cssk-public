# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The row captions this module ships, read back from its own data files.

Every row of every vzor carries the tlačivo's own text — column, rate and
section, verbatim from the Financial Administration's eForm of the vzor
(DPHv12, v18, v20, v21, v25), most specific part first: the Lines list cuts a
long name at its end, and with the section first r01 to r04 read alike there.
The row number is the Code column, so it is not repeated in the name.

The captions live in ONE place, the version records' ``line_def_ids`` in
``data/``; the upgrade migration and the tests read them from there. The data
files are ``noupdate``: a fresh install takes the captions from them, an
existing database only through a migration.
"""
import ast

from lxml import etree

from odoo.tools.misc import file_path

DATA_FILES = (
    "l10n_sk_vat_return/data/cssk_vat_return_version_data.xml",
    "l10n_sk_vat_return/data/cssk_vat_return_2024_version_data.xml",
    "l10n_sk_vat_return/data/cssk_vat_return_legacy_version_data.xml",
)


def shipped_row_names():
    """``{version xmlid (without module): {line code: caption}}``."""
    out = {}
    for rel in DATA_FILES:
        tree = etree.parse(file_path(rel))
        for record in tree.iter("record"):
            if record.get("model") != "cssk.vat.return.version":
                continue
            field = record.find("field[@name='line_def_ids']")
            if field is None:
                continue
            out[record.get("id")] = {
                cmd[2]["code"]: cmd[2]["name"]
                for cmd in ast.literal_eval(field.get("eval"))
            }
    return out
