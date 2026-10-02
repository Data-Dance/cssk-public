# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""KB BEST electronic statement (``*.OKM``) on the OCA statement-import wizard.

The record layout lives in ``account_kb_best_base``; this feeds the OCA
framework and finds the journal.
"""

import logging

from odoo import models

from odoo.addons.account_cz_bankfile_base.utils.common import (
    national_account_key,
)
from odoo.addons.account_kb_best_base.utils.best import parse_best_statement

_logger = logging.getLogger(__name__)


class AccountStatementImport(models.TransientModel):
    _inherit = "account.statement.import"

    def _parse_file(self, data_file):
        try:
            triplets = parse_best_statement(
                data_file, with_symbols=self._kb_best_has_symbols())
        except (ValueError, IndexError, KeyError):
            # fixed-width slicing and the int()/date() conversions are what a
            # wrong-format file trips on; anything else must surface
            _logger.debug("Statement file is not KB BEST", exc_info=True)
            return super()._parse_file(data_file)
        if not triplets:
            return super()._parse_file(data_file)
        triplets = [
            (currency, self._kb_best_journal_account(account), stmts)
            for currency, account, stmts in triplets
        ]
        return triplets if len(triplets) > 1 else triplets[0]

    def _kb_best_journal_account(self, account):
        """The journal's own spelling of the statement's account.

        The statement names the account by IBAN; a journal may hold it as
        ``90093-669910217/0100``, which the framework's sanitized ``ilike``
        does not pair with the IBAN. Compare (bank, prefix, number) instead.
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

    def _kb_best_has_symbols(self):
        """True when a module puts the VS/KS/SS fields on statement lines."""
        return (
            "variable_symbol"
            in self.env["account.bank.statement.line"]._fields
        )
