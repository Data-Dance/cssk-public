# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""List the taxpayer's declarations that are signed twice.

From this version one person (one birth number) may have the declaration
ticked on one employee record of a company at a time (§ 36 ods. 6 zákona
595/2003 Z. z.). The rule is checked when a record is written; data that
breaks it already is not touched and does not stop the update. Each such pair
is written to the log here, so that it can be put right.
"""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    pairs = env["hr.version"]._l10n_sk_tax_declaration_offenders()
    for first, second in pairs:
        _logger.warning(
            "Slovak payroll: the taxpayer's declaration is signed twice for one "
            "birth number in company %s: employee %s (id %s, version from %s) "
            "and employee %s (id %s, version from %s). Untick Tax Declaration "
            "Signed on one of them.",
            first.company_id.display_name,
            first.employee_id.display_name, first.employee_id.id, first.date_start,
            second.employee_id.display_name, second.employee_id.id, second.date_start,
        )
    if not pairs:
        _logger.info(
            "Slovak payroll: no birth number has the taxpayer's declaration "
            "signed on two employee records at once.")
