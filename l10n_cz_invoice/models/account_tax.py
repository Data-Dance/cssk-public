# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    # NB: DELIBERATELY a distinct name from the same-purpose field another
    # CZ localization ships, so toggling ours does not drive that module's
    # supply-code machinery. The invoice phrase honours the other field too
    # when that module is installed.
    l10n_cz_invoice_reverse_charge = fields.Boolean(
        string="CZ Reverse Charge phrase (§92a)",
        help="Mark this tax as a domestic reverse-charge supply (přenesení "
        "daňové povinnosti) so the mandatory §92a phrase is printed on the CZ "
        "invoice.",
    )
