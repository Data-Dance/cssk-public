from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    cssk_control_section_override = fields.Char(
        string="Control-statement section override",
        help="If set, forces this section code on lines of this journal, "
        "overriding the tax-level default in the section resolver.",
    )
