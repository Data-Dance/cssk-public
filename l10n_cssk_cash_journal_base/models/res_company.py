# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    """Which set of books this company keeps.

    The regime is recorded on the company because it decides what the year has
    to produce, not how a document is posted: the books are double-entry in
    every regime. ``pu`` is the default, so installing this module changes
    nothing until someone says otherwise.

    ``ju`` (jednoduché účtovníctvo) is **Slovak only**. The Czech Republic
    closed it to sole traders — § 1f zákona 563/1991 Sb. leaves it to small
    non-profits — so offering it to a Czech company would invite a filing that
    does not exist.
    """

    _inherit = "res.company"

    cssk_bookkeeping_regime = fields.Selection(
        [
            ("pu", "Double-entry (podvojné účtovníctvo / účetnictví)"),
            ("de", "Tax records (daňová evidencia / daňová evidence)"),
            ("ju", "Single-entry accounting (jednoduché účtovníctvo, SK only)"),
            ("pausal", "Flat-rate expenses (paušálne výdavky / paušální výdaje)"),
        ],
        string="Bookkeeping Regime",
        default="pu", required=True,
    )
    cssk_cash_partial_allocation = fields.Selection(
        [
            ("prorata", "Pro rata over base and VAT"),
            ("vat_first", "VAT first, then the base"),
            ("base_first", "Base first, then the VAT"),
        ],
        string="Partial Payment Allocation",
        default="prorata", required=True,
        help="How a part payment of an invoice is split between the tax base "
             "and the VAT. All three are permissible: the entity chooses one in "
             "its internal directive, keeps it for the whole year and applies "
             "it to income and expenses alike. Pro rata is Odoo's own "
             "convention; POHODA settles the VAT first.",
    )
    cssk_cash_journal_start = fields.Date(
        string="Cash Journal Starts",
        help="First date the denník covers. Earlier payments are left alone, "
             "which is what a mid-year migration needs.",
    )

    def _cssk_chart_category_map(self):
        """``[(code prefixes, outbound category, inbound category)]``.

        The country module answers with its chart's mapping; an empty list means
        the accountant maps the chart by hand. Each entry names an xmlid of a
        ``cssk.cash.category``, and the inbound one is ``None`` for an account
        that only ever moves one way.
        """
        return []

    def _cssk_map_chart_categories(self, overwrite=False):
        """Fill the denník categories on this company's chart by code prefix.

        **Never overwrites what somebody chose**, unless asked to: a default
        mapping is a starting point, and the accountant's own decision on an
        account outranks ours. Re-runnable, so it can be applied again after a
        chart is extended.

        Returns the number of accounts it touched.
        """
        touched = 0
        for company in self:
            table = company._cssk_chart_category_map()
            if not table:
                continue
            accounts = self.env["account.account"].with_company(company).search([
                ("company_ids", "in", company.id),
            ])
            for prefixes, out_ref, in_ref in table:
                out_category = self.env.ref(out_ref, raise_if_not_found=False) \
                    if out_ref else None
                in_category = self.env.ref(in_ref, raise_if_not_found=False) \
                    if in_ref else None
                for account in accounts:
                    if not account.code or not account.code.startswith(prefixes):
                        continue
                    values = {}
                    if out_category and (overwrite
                                         or not account.cssk_cash_category_id):
                        values["cssk_cash_category_id"] = out_category.id
                    if in_category and (overwrite
                                        or not account.cssk_cash_category_in_id):
                        values["cssk_cash_category_in_id"] = in_category.id
                    if values:
                        account.write(values)
                        touched += 1
        return touched

    @api.constrains("cssk_bookkeeping_regime", "country_id")
    def _check_cssk_bookkeeping_regime(self):
        for company in self:
            if company.cssk_bookkeeping_regime != "ju":
                continue
            if company.country_id.code == "CZ":
                raise ValidationError(_(
                    "Jednoduché účetnictví is not open to a Czech sole trader "
                    "(§ 1f zákona 563/1991 Sb. leaves it to small "
                    "non-profits). Use tax records (daňová evidence) instead.",
                ))
