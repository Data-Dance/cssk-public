# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Carry the new row labels onto existing databases.

New in 1.2.0. Until now every DPPO line definition carried ``name`` equal to
``code`` — 941 of them, across eleven vzory — so a mapping onto a DPPO row
could be checked structurally and never semantically. The load-bearing rows
now have sourced labels; this puts them on databases that already hold the
records.

``data/dppo_version_data.xml`` is ``noupdate="1"``, so the 2025 vzor would
never see them otherwise, and a line definition already loaded is not reliably
rewritten for the others either (measured on l10n_sk_vat_return 1.11.0, where
five of five version records still lacked a newly added line after an
upgrade).

Reads the labels from the data files themselves rather than repeating them —
a table here would be the same duplication that l10n_sk_vat_return 1.11.0's
first draft carried, and it would drift the moment a label is corrected.
Only rows whose stored name is still the bare code are touched, so a label
someone edited by hand survives. Idempotent.
"""
import logging
import os
import re

_logger = logging.getLogger(__name__)

_RECORD = re.compile(
    r'<record[^>]*model="cssk\.income\.tax\.line\.def"[^>]*>(.*?)</record>',
    re.S)
_VERSION_REF = re.compile(r'name="version_id"\s+ref="([^"]+)"')
_CODE = re.compile(r'name="code">([^<]*)<')
_NAME = re.compile(r'name="name">([^<]*)<')


def _labels_from_data_files():
    """{(version xmlid, code): label} for every row the data files name."""
    module = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    data = os.path.join(module, "data")
    out = {}
    for fname in sorted(os.listdir(data)):
        if not (fname.startswith("dppo_version_") and fname.endswith(".xml")):
            continue
        with open(os.path.join(data, fname), encoding="utf-8") as fh:
            source = fh.read()
        for match in _RECORD.finditer(source):
            block = match.group(1)
            ref = _VERSION_REF.search(block)
            code = _CODE.search(block)
            name = _NAME.search(block)
            if not (ref and code and name):
                continue
            if name.group(1) == code.group(1):
                continue  # deliberately unlabelled — no source for it
            out[(ref.group(1), code.group(1))] = name.group(1)
    return out


def migrate(cr, version):
    from odoo import SUPERUSER_ID, api

    env = api.Environment(cr, SUPERUSER_ID, {})
    labels = _labels_from_data_files()
    if not labels:
        _logger.warning("l10n_sk_dppo 1.2.0: no labels found in the data files")
        return

    by_version = {}
    for (ref, code), label in labels.items():
        by_version.setdefault(ref, {})[code] = label

    renamed = 0
    for ref, per_code in by_version.items():
        xmlid = ref if "." in ref else "l10n_sk_dppo.%s" % ref
        ver = env.ref(xmlid, raise_if_not_found=False)
        if not ver:
            continue
        for ldef in ver.line_def_ids:
            label = per_code.get(ldef.code)
            # Only a name still equal to its code — never overwrite an edit.
            if label and ldef.name == ldef.code:
                ldef.name = label
                renamed += 1
    _logger.info("l10n_sk_dppo 1.2.0: labelled %s DPPO row(s)", renamed)
