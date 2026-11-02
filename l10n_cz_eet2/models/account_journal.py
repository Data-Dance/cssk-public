# -*- coding: utf-8 -*-
from odoo import _, api, fields, models

from .res_company import check_id_jednotky


class AccountJournal(models.Model):
    _inherit = "account.journal"

    l10n_cz_eet2_contact = fields.Boolean(
        string="EET 2.0 Contact Payments",
        help="Payments registered in this journal are, by default, in-person / "
            "on-premises (contact) payments that must be recorded by EET 2.0. "
            "Each payment carries its own flag that starts from this value.")
    l10n_cz_eet2_id_pokl = fields.Char(
        string="EET 2.0 PoS ID (id_pokl)",
        help="Identifier sent as id_pokl (<=20 chars) for payments in this "
            "journal. Falls back to the journal code if empty.")
    l10n_cz_eet2_id_jednotky = fields.Integer(
        string="EET 2.0 Unit ID (id_jednotky)",
        help="Registrating-unit id for this journal. Falls back to the company "
            "default if empty.")

    @api.constrains("l10n_cz_eet2_id_jednotky")
    def _check_l10n_cz_eet2_id_jednotky(self):
        for journal in self:
            check_id_jednotky(journal.l10n_cz_eet2_id_jednotky,
                            _("EET 2.0 Unit ID of journal %s", journal.name))
