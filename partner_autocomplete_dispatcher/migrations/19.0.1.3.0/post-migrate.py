# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Companies left on the old "None" move to the real None provider.

Until 19.0.1.2.0 the choice labelled "None" was Odoo's own IAP lookup, and it
was also the default, so a company that chose "None" and one that never
touched the setting look the same. Neither expected paid lookups to leave for
Odoo, so both move to the provider that sends nothing. Czech and Slovak
partners are still looked up in ARES / ORSF: those go by the partner's country.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute(
        """
        UPDATE res_company
           SET partner_autocomplete_provider = 'partner.autocomplete.provider.none'
         WHERE partner_autocomplete_provider = 'partner.autocomplete.provider'
        """
    )
    _logger.info(
        "partner_autocomplete_dispatcher: %s company(ies) moved from Odoo IAP "
        "(formerly labelled None) to None", cr.rowcount)
