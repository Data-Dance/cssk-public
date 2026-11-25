# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    l10n_cz_proportional_deduction = fields.Boolean(
        string="Poměrný odpočet (§ 75)",
        help="§ 75 odst. 1 ZDPH: a supply received both for the payer's own "
             "supplies and for other purposes carries a deduction only in "
             "the proportion of the first. A bill taxed with such a tax is "
             "reported in B.2 of the kontrolní hlášení with 'Použit poměr' "
             "= A (VetaB2/pomer). Not for the deduction reduced by the "
             "coefficient of § 76, which the kontrolní hlášení does not "
             "mark.")
