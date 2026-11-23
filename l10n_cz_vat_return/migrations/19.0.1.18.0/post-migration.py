# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""ř. 31 (třístranný obchod, dodání prostřední osobou) is computed.

It was a manual line because nothing in the l10n_cz chart carried its tag.
``l10n_cz_ec_sales`` now adds the middle party's supply tax tagged
``VAT 31``, so the line reads ``-VAT 31`` — the sign of ř. 20, a supply — as
ř. 30 already read ``VAT 30``. The line definition is ``noupdate``, so it is
rewritten here. A value an accountant typed into ř. 31 of an existing return
survives as an override.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ldef = env.ref("l10n_cz_vat_return.dphdp3_ld_tri_dozb", raise_if_not_found=False)
    # Only while it is still the shipped manual line: a definition somebody
    # changed on purpose is theirs.
    if ldef and ldef.kind == "manual":
        ldef.write({"kind": "tags", "tag_formula": "-VAT 31"})
