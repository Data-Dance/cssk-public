# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Settlements not yet posted follow the rules of this version.

A child bonus granted in 2023 and 2024 is kept (§ 33 ods. 11 zákona 595/2003
as in force to 31. 12. 2024) and a tax underpayment of 5 EUR or less is not
withheld (§ 38 ods. 7). A posted settlement is left as it was posted.
"""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    Settlement = env["l10n.sk.tax.reconciliation"]
    field = Settlement._fields["tax_underpayment_waived"]
    for settlement in Settlement.search([("state", "!=", "posted")]):
        try:
            with cr.savepoint():
                env.add_to_compute(field, settlement)
                settlement.flush_recordset()
        except Exception:  # a year without parameters must not stop the upgrade
            _logger.warning(
                "Annual tax settlement %s was not recomputed.", settlement.id,
                exc_info=True)
            env.remove_to_compute(field, settlement)
            env.invalidate_all()
