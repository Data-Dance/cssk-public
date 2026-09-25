# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""A reverse-charge CORRECTION left its self-assessed VAT on the base account.

`l10n_cz` names both tax accounts on the INVOICE repartition of its four
reverse-charge purchase taxes -- `12% EU G`, `21% EU G`, `12% EU S`,
`21% EU S` -- and names only the deductible one on the REFUND repartition. The
self-assessed leg of a credit note therefore has no tax account, and Odoo puts
that amount on the BASE line's account instead.

What it looks like in the books is not a misposted tax line but an internal
clearing account that stops clearing. On a seven-year Czech import, 64
reverse-charge corrections left **289 031.99** on účet 395000, which nets to
zero in the source. Nothing else disagreed: the VAT return and the control
statement read tags, the tags were right, and the only witness was the account
balance.

Runs over every tax rather than the four xmlids, because the archived
historical rate clones inherit the repartition of whatever they were cloned
from -- and a history import is the one job that uses those.

Already-posted moves are NOT rewritten. They carry the accounts that were
configured when they were posted; correcting them is a reload, which is a
decision rather than a migration step.
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "cz")])
    if not companies:
        return
    touched = companies._cz_fix_refund_repartition_accounts()
    _logger.info(
        "l10n_cz_vat_return: %s refund repartition account(s) restored across "
        "%s Czech company(ies)", touched, len(companies),
    )
