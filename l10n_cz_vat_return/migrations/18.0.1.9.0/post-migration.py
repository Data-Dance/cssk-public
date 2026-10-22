# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""ř. 33 / ř. 34 collect the documents flagged as bad-debt corrections.

ř. 33 kept its ``VAT 33`` tag and gains the creditor filter; ř. 34 was a
manual line and becomes ``VAT 34`` plus the debtor filter. Both line
definitions are ``noupdate``, so they are rewritten here. A value an
accountant typed into ř. 34 of an existing return survives as an override.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid, vals in (
        ("l10n_cz_vat_return.dphdp3_ld_opr_verit",
         {"line_filter": "cz_bad_debt_creditor"}),
        ("l10n_cz_vat_return.dphdp3_ld_opr_dluz",
         {"kind": "tags", "tag_formula": "VAT 34",
          "line_filter": "cz_bad_debt_debtor"}),
    ):
        ldef = env.ref(xmlid, raise_if_not_found=False)
        if ldef:
            ldef.write(vals)
