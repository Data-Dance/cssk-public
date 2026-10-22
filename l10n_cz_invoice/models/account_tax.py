# Copyright 2026 Data Dance s.r.o.
# Data Dance Proprietary License v1.0 — see the LICENSE file.

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    # NB: a distinct name from EE l10n_cz_reports' own ``l10n_cz_reverse_charge``
    # so toggling this does not trigger EE's supply-code machinery. The invoice
    # phrase also honours EE's field when that module is installed.
    l10n_cz_invoice_reverse_charge = fields.Boolean(
        string="CZ Reverse Charge phrase (§92a)",
        help="Mark this tax as a domestic reverse-charge supply (přenesení "
        "daňové povinnosti) so the mandatory §92a phrase is printed on the CZ "
        "invoice.",
    )
