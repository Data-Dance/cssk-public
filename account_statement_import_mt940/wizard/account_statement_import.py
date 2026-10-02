# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""MT940 / MultiCash ``*.STA`` import on the OCA statement-import wizard.

The format logic lives in ``account_mt940_base``; this feeds the OCA framework
and bridges one gap it cannot close on its own: finding the journal.
"""

import logging

from odoo import models

from odoo.addons.account_cz_bankfile_base.utils.common import (
    national_account_key,
)
from odoo.addons.account_mt940_base.utils.mt940 import parse_mt940

_logger = logging.getLogger(__name__)


class AccountStatementImport(models.TransientModel):
    _inherit = "account.statement.import"

    def _parse_file(self, data_file):
        try:
            triplets = parse_mt940(data_file, with_symbols=self._mt940_has_symbols())
        except (ValueError, IndexError, KeyError):
            # What a wrong-format file trips on: the field regexes and the
            # date/amount conversions. Anything else is a real defect and must
            # surface rather than be reported as an unsupported format.
            _logger.debug("Statement file is not MT940", exc_info=True)
            return super()._parse_file(data_file)
        if not triplets:
            return super()._parse_file(data_file)
        triplets = [
            (currency, self._mt940_journal_account(account), stmts)
            for currency, account, stmts in triplets
        ]
        return triplets if len(triplets) > 1 else triplets[0]

    def _mt940_journal_account(self, account):
        """Return the ``acc_number`` of the bank journal this statement is for.

        The framework finds the journal by an ``ilike`` on the sanitized
        number, so ``19-2000145399/0800`` (how ČS writes :25:) never meets a
        journal whose account is stored as the IBAN ``CZ65 0800 0000 1920 0014
        5399``, nor the other way round — and both spellings are common for the
        same Czech account. Compare them as (bank, prefix, number) instead, and
        hand back the journal's own spelling so the framework's lookup is exact.
        Unmatched, the statement's value is passed through and the framework
        reports it.
        """
        key = national_account_key(account)
        if key is None:
            return account
        journals = self.env["account.journal"].search([
            ("type", "=", "bank"),
            ("bank_account_id", "!=", False),
            ("company_id", "in", self.env.companies.ids),
        ])
        for journal in journals:
            acc_number = journal.bank_account_id.acc_number
            if national_account_key(acc_number) == key:
                return acc_number
        return account

    def _mt940_has_symbols(self):
        """True when a module puts the VS/KS/SS fields on statement lines."""
        return (
            "variable_symbol"
            in self.env["account.bank.statement.line"]._fields
        )
