"""The ePošťák firm a company speaks for.

Several companies in one database may exchange Peppol documents through
ePošťák, each with its own contract, or several under one integrator key. The
firm, like the credentials in the transport modules, therefore belongs to the
company. Before 19.0.1.1.0 it was the global ``epostak.firm_id`` parameter,
which the migration copied to the company the inbound cron ran as.
"""

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    epostak_firm_id = fields.Char(
        string="ePošťák Firm ID",
        groups="base.group_system",
        help="UUID of the ePošťák firm this company acts as, sent as X-Firm-Id. "
        "Needed only with an integrator key (sk_int_*).",
    )
