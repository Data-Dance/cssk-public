# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The DPHDP3 row captions this module ships, read back from its data file.

The captions are the text of the form as vyhláška č. 387/2025 Sb., příloha
č. 1, states it for each row and column (25 5401), joined to the EPO
attribute through the row and column EPO's structure description gives it —
column, rate and row, most specific part first because a list cuts a long name
at its end. They live in ONE place, ``data/dphdp3_version_data.xml``; the
upgrade migration and the tests read them from there.

The data file is ``noupdate``: a fresh install takes the captions from it, an
existing database only through the migration that calls this.
"""
import re

from lxml import etree

from odoo.tools.misc import file_path

DATA_FILE = "l10n_cz_vat_return/data/dphdp3_version_data.xml"

#: What releases before 1.15.0 shipped in place of a caption: "R1 tax_base",
#: "R40 in_full_amount", "R52A coefficient".
_PLACEHOLDER = re.compile(r"R\d+[AB]? [a-z_]+")


def shipped_row_names():
    """``{line def xmlid (without module): caption}``."""
    tree = etree.parse(file_path(DATA_FILE))
    out = {}
    for record in tree.iter("record"):
        if record.get("model") != "cssk.vat.return.line.def":
            continue
        name = record.find("field[@name='name']")
        out[record.get("id")] = name.text
    return out


def is_shipped_placeholder(name):
    return bool(_PLACEHOLDER.fullmatch(name or ""))
