# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CsskCashCategory(models.Model):
    """The *členenie* a denník row is filed under.

    Neither country prescribes the form of the tax records, so the catalogue is
    data rather than code:

    * **SK daňová evidencia** (§ 6 ods. 11 ZDP) wants príjmy and *daňové*
      výdavky "v členení potrebnom na zistenie základu dane" — § 21 expenses
      are not recorded at all.
    * **SK jednoduché účtovníctvo** does prescribe the columns (opatrenie
      MF/27076/2007-74, § 4): predaj tovaru / predaj výrobkov a služieb /
      ostatné, and on the expense side zásoby / služby / mzdy / poistné /
      tvorba sociálneho fondu / ostatné, each split into "zahŕňané do ZD" and
      "neovplyvňujúce ZD", plus priebežné položky.
    * **CZ daňová evidence** (§ 7b ZDP) only says "v členění potřebném pro
      zjištění základu daně"; vendors record non-deductible expenses too
      (POHODA's VN rows), because the reader wants the till to reconcile.

    So a category is a country catalogue entry, shipped by the country module,
    and the accountant may add their own. It carries three decisions:

    ``kind``
        which column of the denník the amount lands in.
    ``taxable``
        whether it reaches the tax base — the split SK calls "zahŕňané do
        základu dane" and POHODA calls P/V versus PN/VN.
    ``non_cash``
        a row that never touched the money: depreciation, the § 23 / § 17
        adjustments. POHODA keeps these in a separate *nepeněžní deník*.

    **No ``company_id``.** A catalogue belongs to a country's statute, not to a
    company, and the per-company decision — which account means which category
    — lives on the account instead. A company that needs a private category
    creates one; nothing stops it being used elsewhere in the same database.
    """

    _name = "cssk.cash.category"
    _description = "Cash Journal Category (členenie peňažného denníka)"
    _order = "country_id, sequence, code"

    code = fields.Char(
        required=True, index=True,
        help="Short key the country module and the denník grid refer to.",
    )
    name = fields.Char(required=True, translate=True)
    country_id = fields.Many2one(
        "res.country", required=True, index=True,
        help="The country whose statute this category comes from.",
    )
    kind = fields.Selection(
        [
            ("income", "Income"),
            ("expense", "Expense"),
            ("transit", "Transit (priebežná položka)"),
        ],
        required=True, default="expense",
    )
    taxable = fields.Boolean(
        string="Affects the tax base", default=True,
        help="Income or expense that enters the personal income-tax base. "
             "Clear it for what SK calls 'neovplyvňujúce základ dane' and "
             "POHODA files as PN/VN: an owner's withdrawal, a loan repayment, "
             "the VAT remittance, income tax paid.",
    )
    non_cash = fields.Boolean(
        help="A row that moved no money: depreciation, the tax-base "
             "adjustments of SK § 17 ods. 8 / CZ § 23 odst. 8. Generated from "
             "ordinary journal entries rather than from a payment.",
    )
    tax_return_code = fields.Char(
        help="Which row of the personal income-tax return this category feeds "
             "— SK DPFO typ B tabuľka 1, CZ Příloha č. 1. The country module "
             "sets it; the figures report groups by it.",
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    note = fields.Text(
        help="Why this category exists — the statutory reference, or the "
             "internal directive that defines it.",
    )

    _code_country_uniq = models.Constraint(
        "UNIQUE (code, country_id)",
        "A cash journal category code must be unique per country.",
    )

    @api.constrains("kind", "taxable", "non_cash")
    def _check_transit_is_not_taxable(self):
        """A transit leg is money moving between one's own pockets.

        It is neither income nor expense, so it cannot reach the tax base, and
        it is by definition a movement of money, so it cannot be non-cash. Both
        mistakes are easy to make in a hand-written catalogue and neither
        raises anywhere else — a taxable transit category would simply inflate
        income by every transfer from the bank to the till.
        """
        for category in self:
            if category.kind != "transit":
                continue
            if category.taxable:
                raise ValidationError(_(
                    "Category %s is a transit (priebežná položka), so it "
                    "cannot affect the tax base.", category.display_name,
                ))
            if category.non_cash:
                raise ValidationError(_(
                    "Category %s is a transit (priebežná položka), so it "
                    "cannot be a non-cash category.", category.display_name,
                ))

    @api.depends("code", "name")
    def _compute_display_name(self):
        for category in self:
            category.display_name = "%s — %s" % (category.code, category.name)
