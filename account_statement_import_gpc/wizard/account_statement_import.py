# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""GPC import on the OCA statement-import wizard (CE variant).

The format logic lives in ``account_gpc_base`` and is shared with the
Enterprise shim; this only feeds the OCA framework.
"""

import logging

from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.account_cz_bankfile_base.utils.common import (
    account_number_key,
    bare_account_key,
    is_same_bare_account,
)
from odoo.addons.account_gpc_base.utils.gpc import parse_gpc

_logger = logging.getLogger(__name__)


class AccountStatementImport(models.TransientModel):
    _inherit = "account.statement.import"

    def _parse_file(self, data_file):
        try:
            triplets = parse_gpc(data_file, with_symbols=self._gpc_has_symbols())
        except (ValueError, IndexError, KeyError):
            # What a wrong-format file trips on: fixed-width slicing and the
            # int()/date() conversions. Anything else is a real defect and must
            # surface rather than be reported as an unsupported file format.
            _logger.debug("Statement file is not GPC", exc_info=True)
            return super()._parse_file(data_file)
        if not triplets:
            return super()._parse_file(data_file)
        self._gpc_check_accounts(triplets)
        # the OCA framework takes either one triplet or a list of them
        return triplets if len(triplets) > 1 else triplets[0]

    def _match_journal(self, account_number, currency):
        """Find the journal of a bank-code-less account by number.

        GPC names the own account as bare digits — prefix and number run
        together, no bank code — and the framework looks for that string
        *inside* the journal's account, which misses ``19-123456789/0100``
        (GPC ``190123456789``). Compare (prefix, number) instead and hand the
        framework the journal's own spelling, so its checks (the selected
        journal, the currency) still run. The account string the statement
        lines are keyed with is left alone, so files imported before keep
        deduplicating.
        """
        journals = self._gpc_journals_of(account_number)
        if len(journals) > 1:
            journals = journals.filtered(
                lambda journal: (journal.currency_id
                                 or journal.company_id.currency_id) == currency
            ) or journals
        ctx_journal_id = self.env.context.get("journal_id")
        if ctx_journal_id in journals.ids:
            journals = journals.browse(ctx_journal_id)
        if len(journals) == 1:
            account_number = journals.bank_account_id.acc_number
        return super()._match_journal(account_number, currency)

    def _gpc_journals_of(self, account_number):
        return self.env["account.journal"].search([
            ("type", "=", "bank"),
            ("bank_account_id", "!=", False),
            ("company_id", "in", self.env.companies.ids),
        ]).filtered(lambda journal: is_same_bare_account(
            journal.bank_account_id.acc_number, account_number,
        ))

    def _gpc_check_accounts(self, triplets):
        """Refuse a GPC account that only a substring search would place.

        ``2000145399`` (no prefix) is found inside the account of a
        ``19-2000145399`` journal by the framework's ``ilike``, and the
        statement would be booked to an account it does not belong to.
        """
        for _currency, account_number, _stmts in triplets:
            if bare_account_key(account_number) is None:
                continue
            if self._gpc_journals_of(account_number):
                continue
            lookalikes = self.env["account.journal"].search([
                ("type", "=", "bank"),
                ("company_id", "in", self.env.companies.ids),
                ("bank_account_id.sanitized_acc_number", "ilike",
                 account_number),
            ]).filtered(lambda journal: account_number_key(
                journal.bank_account_id.acc_number) is not None)
            if lookalikes:
                raise UserError(_(
                    "No bank journal has the account %(account)s of this GPC "
                    "statement. %(journals)s only contains the same digits "
                    "within a different account number.",
                    account=account_number,
                    journals=", ".join(lookalikes.mapped("display_name")),
                ))

    def _gpc_has_symbols(self):
        """True when a module puts the VS/KS/SS fields on statement lines."""
        return (
            "variable_symbol"
            in self.env["account.bank.statement.line"]._fields
        )
