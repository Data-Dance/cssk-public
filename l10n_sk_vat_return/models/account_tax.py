# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountTax(models.Model):
    """Which paragraph of § 69 a reverse-charge tax is, for the older vzory.

    The current tlačivo does not ask: r09/r10 read "§ 69 ods. 2, 3 a 9 až 12"
    and take the lot. So ``l10n_sk`` ships ONE reverse-charge purchase family
    (``vs_rc_5/19/23``, "PREN") and never distinguishes them — correctly, for
    the form it was written for.

    The vzory in force from 2012 to 2020 do ask. They give § 69 ods. 3 — služba
    dodaná zahraničnou osobou, where the recipient pays — its own row pair
    r11/r12, apart from § 69 ods. 2 a 9 až 12 on r09/r10. Filing a 2019 period
    therefore needs a split that no tag in the chart can make.
    """

    _inherit = "account.tax"

    l10n_sk_dph_69_par = fields.Selection(
        [
            ("auto", "From the supplier's country"),
            ("69_3", "§ 69 ods. 3 — služba od zahraničnej osoby"),
            ("69_other", "§ 69 ods. 2 a 9 až 12"),
        ],
        string="SK § 69 paragraph (pre-2021 vzory)",
        default="auto",
        help="Which row a reverse-charge amount takes on a DPH return for a "
        "period before 1. 1. 2021. Only those vzory separate the paragraphs; "
        "from 2021 the form merges them and this is ignored.\n\n"
        "Left on 'From the supplier's country' — the default, and right for "
        "the shared l10n_sk reverse-charge taxes — a line is treated as "
        "§ 69 ods. 3 when its supplier is established outside Slovakia, which "
        "is what that paragraph says. Set it explicitly on a tax a company "
        "uses for ONE paragraph only: a dedicated domestic-construction "
        "prenos tax is '§ 69 ods. 2 a 9 až 12' whoever the supplier is, and a "
        "§ 69 ods. 2 goods-with-installation tax is too, even though its "
        "supplier is foreign.",
    )
