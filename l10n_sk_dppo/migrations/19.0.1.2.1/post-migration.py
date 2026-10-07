# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Correct the 800/900-block labels that 1.2.0 shipped wrong.

1.2.0 labelled r820 "Daňová licencia na úhradu" and r900 "Suma na účely
určenia výšky preddavkov" on the licencia-era vzory. Both were extrapolated
from the DPPOv24/v25 computation spine onto vzory it does not describe, and
Finančná správa's own usmernenie (20. 12. 2018) prints those captions:

    r. 800 – Daň po úľavách a po zápočte dane
    r. 810 – Daňová licencia
    r. 820 – Kladný rozdiel medzi daňovou licenciou a daňou určený na zápočet
    r. 900 – Daňová licencia na úhradu

The form REUSED those numbers between the two eras, which is why an
extrapolation that is safe everywhere else on this form is not safe here.

1.2.0's own migration cannot repair it: that one only fills a name still
equal to its code, deliberately, so it never overwrites an edit — and a wrong
label is not a bare one. Several vintage data files are ``noupdate="1"`` as
well, so a reload does not reach them either.

So this one FORCES the 800/900 block to whatever the data files now say,
including back to bare where the label was withdrawn for want of a source.
Scoped to that block: a label anywhere else is left exactly as it is.
"""
import logging
import os
import re

_logger = logging.getLogger(__name__)

# The rows whose number the form reused between the daňová licencia and the
# minimálna daň eras. Only these are forced.
_VOLATILE = ("r800", "r810", "r820", "r830", "r900")

_RECORD = re.compile(
    r'<record[^>]*model="cssk\.income\.tax\.line\.def"[^>]*>(.*?)</record>',
    re.S)
_VERSION_REF = re.compile(r'name="version_id"\s+ref="([^"]+)"')
_CODE = re.compile(r'name="code">([^<]*)<')
_NAME = re.compile(r'name="name">([^<]*)<')


def _volatile_names_from_data_files():
    """{(version xmlid, code): name} for the 800/900 block, bare included."""
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
            if code.group(1) in _VOLATILE:
                out[(ref.group(1), code.group(1))] = name.group(1)
    return out


def migrate(cr, version):
    from odoo import SUPERUSER_ID, api

    env = api.Environment(cr, SUPERUSER_ID, {})
    wanted = _volatile_names_from_data_files()
    if not wanted:
        _logger.warning("l10n_sk_dppo 1.2.1: no 800/900 rows found in the data")
        return

    by_version = {}
    for (ref, code), name in wanted.items():
        by_version.setdefault(ref, {})[code] = name

    fixed = 0
    for ref, per_code in by_version.items():
        xmlid = ref if "." in ref else "l10n_sk_dppo.%s" % ref
        ver = env.ref(xmlid, raise_if_not_found=False)
        if not ver:
            continue
        for ldef in ver.line_def_ids:
            name = per_code.get(ldef.code)
            if name is not None and ldef.name != name:
                ldef.name = name
                fixed += 1
    _logger.info(
        "l10n_sk_dppo 1.2.1: corrected %s row name(s) in the 800/900 block",
        fixed)
