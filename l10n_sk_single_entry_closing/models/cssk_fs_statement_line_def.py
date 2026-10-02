# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CsskFsStatementLine(models.Model):
    """The computed row carries the kind too, so the value has to exist here."""

    _inherit = "cssk.fs.statement.line"

    kind = fields.Selection(
        selection_add=[("cash_categories", "Cash journal categories")],
        ondelete={"cash_categories": "cascade"},
    )


class CsskFsStatementLineDef(models.Model):
    """A statement row that reads the peňažný denník instead of the ledger.

    The účtovná závierka in jednoduché účtovníctvo has two components on two
    different footings: the **výkaz o majetku a záväzkoch** reports balances,
    which the existing ``accounts`` kinds already do, while the **výkaz o
    príjmoch a výdavkoch** reports what was received and paid — the denník's own
    columns. Deriving the second one from account balances would mean rebuilding
    the cash basis a second time, in a second place, with a second set of bugs;
    the denník rows already carry it, category by category.
    """

    _inherit = "cssk.fs.statement.line.def"

    kind = fields.Selection(
        selection_add=[("cash_categories", "Cash journal categories")],
        ondelete={"cash_categories": "cascade"},
    )
    cash_category_formula = fields.Char(
        help="Cash journal category codes for kind=cash_categories, e.g. "
             "'P1,P2,P3' (leading '-' negates the token). The value is the sum "
             "of the denník rows in those categories, as their own columns "
             "carry them — a storno reduces its category.",
    )
