from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    cssk_control_section_override = fields.Char(
        string="Control-statement section override",
        help="If set, every VAT line of this journal is reported in this "
        "section of the control statement, whatever the section resolver "
        "would decide. Use the code as the form prints it, e.g. D.1 on the "
        "journal of a Slovak eKasa cash register, so its sales are reported "
        "as eKasa turnover rather than in D.2.",
    )
