# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""GPC import on the OCA statement-import wizard (CE variant).

The format logic lives in ``account_gpc_base`` and is shared with the
Enterprise shim; this only feeds the OCA framework.
"""

import logging

from odoo import models

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
        # the OCA framework takes either one triplet or a list of them
        return triplets if len(triplets) > 1 else triplets[0]

    def _gpc_has_symbols(self):
        """True when a module puts the VS/KS/SS fields on statement lines."""
        return (
            "variable_symbol"
            in self.env["account.bank.statement.line"]._fields
        )
