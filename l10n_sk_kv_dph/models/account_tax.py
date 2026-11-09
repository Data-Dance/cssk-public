# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    l10n_sk_kv_supplier_excluded = fields.Boolean(
        string="Supplier omits from KV DPH",
        help="For a sale-side domestic reverse charge under § 69 ods. 12 "
             "písm. a) to e). The supplier does not report these supplies in "
             "the kontrolný výkaz; only the recipient reports them, in B.1.",
    )
