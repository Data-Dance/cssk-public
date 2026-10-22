# Copyright 2026 Data Dance s.r.o.
# Data Dance Proprietary License v1.0 — see the LICENSE file.

from odoo import fields, models

from odoo.addons.account_fio_base.utils.payment_reason import (
    payment_reason_selection,
)


class ResPartner(models.Model):
    _inherit = "res.partner"

    fio_payment_reason = fields.Selection(
        selection=lambda self: payment_reason_selection(),
        string="Platební titul",
        company_dependent=True,
        help="ČNB payment reason used as the default on foreign payments to "
             "this partner, where Fio requires one. Set it on the partner "
             "because it follows what you buy from them, not what any single "
             "invoice happens to be.",
    )
