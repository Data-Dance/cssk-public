# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    l10n_cz_eet2_contact = fields.Boolean(
        string="EET 2.0 Contact Payments",
        help="Payments registered in this journal are in-person / on-premises "
            "(contact) payments that must be recorded by EET 2.0.")
    l10n_cz_eet2_id_pokl = fields.Char(
        string="EET 2.0 PoS ID (id_pokl)",
        help="Identifier sent as id_pokl (<=20 chars) for payments in this "
            "journal. Falls back to the journal code if empty.")
    l10n_cz_eet2_id_jednotky = fields.Integer(
        string="EET 2.0 Unit ID (id_jednotky)",
        help="Registrating-unit id for this journal. Falls back to the company "
            "default if empty.")
