# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountTax(models.Model):
    """Marks a purchase tax as the *asset-acquisition* twin of another.

    ř. 47 of the DPHDP3 — *hodnota pořízeného majetku vymezeného v § 4 odst. 4
    písm. d) a e)* — reports how much of the deduction already claimed on
    ř. 40–46 relates to long-term assets. It is a memo row: it moves no money
    and changes no figure, which is precisely why nothing in Odoo notices when
    it is empty, and why it was empty on every return this localisation has
    ever produced.

    The row needs a per-document fact that no Odoo field carries: *is this
    purchase a long-term asset?* The twin is where that fact is recorded. A
    user picks ``21% G Majetek`` instead of ``21% G`` and the acquisition
    reports on ř. 47 as well as on ř. 40, with identical tax consequences —
    the twin's rate, repartition, accounts and deduction tags are the source's.

    This field is what makes the twin identifiable afterwards. Without it the
    only way to recognise one is its name, and a chart whose taxes are named
    in Czech, or a user who renames one, breaks that immediately.
    """

    _inherit = "account.tax"

    cz_asset_source_tax_id = fields.Many2one(
        "account.tax",
        string="Asset Twin Of",
        ondelete="set null",
        help="The ordinary purchase tax this one duplicates in order to report "
        "the acquisition on ř. 47 as well. Set only on taxes generated for "
        "that purpose.",
    )
