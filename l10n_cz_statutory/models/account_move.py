# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Bad-debt VAT corrections: § 46 (creditor), § 74b (debtor), old § 44.

A correction of tax on an unrecoverable receivable is not an ordinary credit
note. The DPHDP3 reports it on its own rows — ř. 33 for the creditor, ř. 34
for the debtor — instead of reducing ř. 1 / ř. 40, and the kontrolní hlášení
reports it in A.4 / B.2 **whatever its amount**, flagged by ``zdph_44``. None
of that can be read off the taxes, which are the ordinary ones, so the
document says it.
"""

from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

#: The old § 44 applies to receivables from supplies made while it was in
#: force: the wording valid to 31. 3. 2019.
OLD_SECTION_44_END = date(2019, 3, 31)


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_cz_bad_debt = fields.Selection(
        [("P", "Oprava u nedobytné pohledávky (§ 46 / § 74b)"),
         ("A", "Oprava podle § 44 ve znění do 31. 3. 2019")],
        string="Oprava u nedobytné pohledávky",
        copy=False,
        tracking=True,
        help="Marks a correction of tax on an unrecoverable receivable. The "
        "creditor's correction is § 46 and following, the debtor's § 74b "
        "(§ 74a before 1. 1. 2025); 'A' is the old § 44 and only for "
        "supplies made up to 31. 3. 2019.\n\n"
        "Its tax goes to DPHDP3 ř. 33 (creditor) or ř. 34 (debtor) instead of "
        "the ordinary rows, and the kontrolní hlášení reports it in A.4 / B.2 "
        "with zdph_44 set, whatever the amount.",
    )

    def _l10n_cz_bad_debt_origin_date(self):
        """Date of the supply being corrected: the corrected document's DUZP."""
        self.ensure_one()
        origin = self.reversed_entry_id
        if not origin:
            return None
        return origin.taxable_supply_date or origin.invoice_date or origin.date

    @api.constrains("l10n_cz_bad_debt", "reversed_entry_id")
    def _check_l10n_cz_bad_debt(self):
        for move in self.filtered("l10n_cz_bad_debt"):
            if move.company_id.account_fiscal_country_id.code != "CZ":
                raise ValidationError(_(
                    "%s: the bad-debt correction flag is Czech; the company "
                    "does not file Czech VAT.", move.display_name))
            if move.l10n_cz_bad_debt != "A":
                continue
            origin_date = move._l10n_cz_bad_debt_origin_date()
            if origin_date and origin_date > OLD_SECTION_44_END:
                raise ValidationError(_(
                    "%(move)s: a correction under the old § 44 (zdph_44 = A) is "
                    "only for supplies made up to 31. 3. 2019; the corrected "
                    "document is dated %(date)s. Use § 46 / § 74b (P).",
                    move=move.display_name, date=origin_date))
