# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The Slovak DIČ.

Slovakia issues **three** identifiers where most countries manage with two:

* **IČO** — the company registry number (``company_registry``)
* **DIČ** — the *income-tax* identifier, ten digits, this field
* **IČ DPH** — the VAT number, ``SK`` + the DIČ (Odoo's ``vat``)

A subject can hold a DIČ and no IČ DPH at all — anyone registered for income
tax who is not a VAT payer — which is exactly why the DIČ needs a field of its
own here.

**Czech Republic is not the same case and needs no such field.** In Czech usage
*DIČ* simply is the VAT number (``CZ`` + IČO), so ``vat`` already holds it;
printing a separate DIČ there would print the same number twice. That is why
this lives in an SK module rather than in the shared CZ/SK base.
"""

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_sk_dic = fields.Char(
        string="DIČ",
        help="Slovak tax identification number (DIČ) — the income-tax "
        "identifier, distinct from the VAT number (IČ DPH) and from the "
        "company registry number (IČO).",
    )

    def _commercial_fields(self):
        """The DIČ belongs to the commercial entity, not to each contact.

        A child contact of a company files nothing of its own; the number that
        reaches a document is the parent's. Odoo's PR #280178 makes the same
        call for the upstream field.
        """
        return super()._commercial_fields() + ["l10n_sk_dic"]
