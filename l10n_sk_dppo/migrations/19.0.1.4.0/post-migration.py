# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Seed the § 46b daňová licencia bands on the licencia-era vintages.

New in 1.4.0. `min_tax_bands` was populated only on the 2024 vzor, so r810
computed 0,00 for 2014-2019 while a taxpayer in those years owed 480, 960 or
2 880 €. The version records are `noupdate="1"` and a data-file edit does not
reach an existing database (measured twice already in this repo), so the bands
are written here.

Reads them from the data files rather than repeating them — a table in a
migration is the duplication `l10n_sk_vat_return` 19.0.1.11.0 had to repair in
its own. Only a version whose bands are still empty is touched, so a value
someone entered by hand survives. Idempotent.
"""
import ast
import logging
import os
import re

_logger = logging.getLogger(__name__)

_RECORD = re.compile(
    r'<record id="(dppo_version_[0-9]*)"[^>]*model="cssk\.income\.tax\.version"'
    r'[^>]*>(.*?)</record>', re.S)
_BANDS = re.compile(r'<field name="min_tax_bands" eval="([^"]*)"')


def _bands_from_data_files():
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
            bands = _BANDS.search(match.group(2))
            if not bands:
                continue
            # The eval attribute is a Python literal with &quot;-free quoting.
            out[match.group(1)] = ast.literal_eval(
                bands.group(1).replace("&quot;", '"'))
    return out


def migrate(cr, version):
    from odoo import SUPERUSER_ID, api

    env = api.Environment(cr, SUPERUSER_ID, {})
    seeded = 0
    for xmlid, bands in _bands_from_data_files().items():
        ver = env.ref("l10n_sk_dppo.%s" % xmlid, raise_if_not_found=False)
        if not ver or ver.min_tax_bands:
            continue
        ver.min_tax_bands = bands
        seeded += 1
    _logger.info(
        "l10n_sk_dppo 1.4.0: seeded § 46b bands on %s version record(s)",
        seeded)
