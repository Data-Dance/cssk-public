# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAccount(models.Model):
    """Where a denník row's category comes from, by default.

    The account is the right carrier because it is what the CZ/SK accounting
    habit already uses: a *predkontácia* names an account, and the account says
    what kind of expense it is. So the accountant maps the chart once —
    501 → zásoby, 518 → služby, 526 → poistné podnikateľa (non-taxable in CZ,
    taxable in SK) — and every payment of every document is filed correctly
    without touching a single invoice.

    ``account.posting.preset`` (see ``docs/predkontacia-document-level-design.md``)
    selects the account; this field turns that account into a denník column. The
    two compose and neither needs to know about the other.

    **Two fields, because an account can move both ways.** A loan account
    receives the loan and pays the instalments; ``343`` pays the VAT over and
    receives the nadmerný odpočet back. Those are two different columns of the
    book — príjmy neovplyvňujúce ZD against výdavky neovplyvňujúce ZD — and a
    single category nets them into one, which is what a cooperating accountant's
    question about a pôžička exposed. So an account may carry a category per
    direction; one category still covers an account that only moves one way.

    **This is not company-scoped.** ``account.account.company_ids`` is a
    many2many in 19.0, so a chart shared by two companies shares its categories
    too. That is harmless for the audience — a sole trader is one company — and
    a per-company mapping model would be a second object to keep in step with
    the chart. If a shared chart ever needs two mappings, the per-line override
    is the escape hatch.
    """

    _inherit = "account.account"

    cssk_cash_category_id = fields.Many2one(
        "cssk.cash.category",
        string="Cash Journal Category",
        help="Denník category for payments that touch this account, and for "
             "money going out where the inbound category below is set. A line "
             "of a paid document may override it.",
    )
    cssk_cash_category_in_id = fields.Many2one(
        "cssk.cash.category",
        string="Cash Journal Category (Money In)",
        help="Category to use when money comes IN through this account, where "
             "that is a different column from money going out. Leave it empty "
             "when one category covers both directions.",
    )
