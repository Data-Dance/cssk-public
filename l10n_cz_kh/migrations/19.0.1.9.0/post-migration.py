# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Re-resolve every line's KH section, and correct the A.2 label.

The resolver changed for four kinds of line, and the section code is a stored
value no data change refreshes:

* a supply that CHARGES Czech VAT to a customer with an EU VAT number used to
  be dropped as an intra-EU supply; it is a domestic supply (A.4 / A.5);
* a recipient-liable supply from a non-established person (ř. 12/13, e.g. a
  service from a third country) went to B.2; it belongs in A.2;
* an import of goods (§ 23, ř. 7/8) went to B.2; it is not reported at all;
* the stock "0% RC" sale tax (ř. 25) never reached A.1.

Rows of statements already computed are NOT touched: what was filed stays as
filed, and a recompute of such a statement is the user's decision.

The A.2 section label cited § 108 odst. 1, which is the supplier's own
liability. The section is "§ 108 odst. 2 a 3" in the Metodická informace
k vyplnění KH; the record is ``noupdate``, so the label is corrected here.
"""
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.l10n_cz_kh.hooks import _recompute_section_codes

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        UPDATE cssk_control_statement_section_code s
           SET name = 'A.2 — Přijatá plnění s povinností přiznat daň (§ 108 odst. 2 a 3)'
          FROM ir_model_data d
         WHERE d.module = 'l10n_cz_kh'
           AND d.name = 'cz_kh_version_2025'
           AND d.model = 'cssk.control.statement.version'
           AND s.version_id = d.res_id
           AND s.code = 'A2'
           AND s.name LIKE '%%§ 108 odst. 1)%%'
    """)
    if cr.rowcount:
        _logger.info("l10n_cz_kh 19.0.1.9.0: A.2 label corrected (%s row)", cr.rowcount)
    env = api.Environment(cr, SUPERUSER_ID, {})
    _recompute_section_codes(env, "CZ", "l10n_cz_kh 19.0.1.9.0")
