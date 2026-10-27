# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""One discovery date, and the settlement rows on the version.

* ``cz_discovery_date`` becomes a related field of the shared
  ``discovery_date``. Its old column is still there (Odoo never drops one),
  so the date the XML used to read is copied over — it is the one that was
  filed.
* The version record is ``noupdate``: name ř. 64 / ř. 65 as its own-tax and
  excess-deduction lines here, where they are not set yet.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    cr.execute("""
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'cssk_vat_return'
           AND column_name = 'cz_discovery_date'
    """)
    if cr.fetchone():
        cr.execute("""
            UPDATE cssk_vat_return
               SET discovery_date = cz_discovery_date
             WHERE cz_discovery_date IS NOT NULL
        """)
    env = api.Environment(cr, SUPERUSER_ID, {})
    version_rec = env.ref("l10n_cz_vat_return.dphdp3_version_2025",
                          raise_if_not_found=False)
    if version_rec:
        version_rec.write({
            "own_tax_line_code": version_rec.own_tax_line_code or "dano_da",
            "excess_line_code": version_rec.excess_line_code or "dano_no",
        })
