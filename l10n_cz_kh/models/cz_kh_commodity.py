# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from .account_move_line import _DP_ROW_RE, _DP_ROWS_A1

#: The codes as the Pokyny k vyplnění kontrolního hlášení list them
#: ("kód předmětu plnění … vyberte hodnotu z číselníku"): 1 / 1a zlato,
#: 3 / 3a nemovitá věc, 4 / 4a stavební a montážní práce, 5 zboží přílohy
#: č. 5, 6 zboží poskytnuté původně jako záruka, 7 zboží po postoupení
#: výhrady vlastnictví, 11 povolenky na emise skleníkových plynů, 12 – 21
#: obiloviny a technické plodiny, kovy, mobilní telefony, integrované obvody,
#: přenosná zařízení, videoherní konzole, certifikáty elektřiny, elektřina,
#: plyn, služby elektronických komunikací. The help used to call 6 "emission
#: allowances" and 11 – 21 "other".
_KH_CODE_HELP = (
    "Commodity code for the VAT control statement (§92a reverse charge), "
    "reported in sections A.1 (supplier) and B.1 (customer): 1 = gold, "
    "3 = supply of immovable property, 4 = construction or assembly work, "
    "5 = goods listed in Annex 5, 6 = goods originally provided as a "
    "guarantee, 7 = goods after an assigned retention of title, "
    "11 = greenhouse-gas emission allowances, 12 = cereals and technical "
    "crops, 13 = metals, 14 = mobile phones, 15 = integrated circuits, "
    "16 = portable data-processing devices, 17 = video game consoles, "
    "18 = electricity certificates, 19 = electricity to a trader, 20 = gas "
    "to a trader, 21 = specified electronic communications services; "
    "1a, 3a and 4a as the form defines them. Set it on the reverse-charge "
    "tax or on the product."
)


class AccountTax(models.Model):
    _inherit = "account.tax"

    cssk_kh_commodity_code = fields.Char(
        string="KH commodity code (§92a)", help=_KH_CODE_HELP)
    cssk_kh_domestic_rc = fields.Boolean(
        string="§ 92a reverse charge (KH)",
        compute="_compute_cssk_kh_domestic_rc",
        help="Technical: a § 92a reverse-charge tax as the kontrolní hlášení "
        "recognises it — marked Reverse charge, or reporting on ř. 25.")

    def _compute_cssk_kh_domestic_rc(self):
        for tax in self:
            tax.cssk_kh_domestic_rc = tax._cz_kh_is_domestic_rc()

    def _cz_kh_is_domestic_rc(self):
        """Whether this is a § 92a reverse-charge tax, the way the resolver
        recognises A.1 / B.1: the flag OR a base tag of ř. 25 (supplied).
        The flag sits on the PURCHASE taxes only, so the stock "0% RC" sale
        tax was never asked for its code and a code set on it — as the
        field's help invites — was ignored on every sale."""
        self.ensure_one()
        if self.cssk_control_is_reverse_charge:
            return True
        tags = (self.invoice_repartition_line_ids
                | self.refund_repartition_line_ids).filtered(
            lambda r: r.repartition_type == "base").tag_ids
        for tag in tags.with_context(lang="en_US"):
            match = _DP_ROW_RE.match((tag.name or "").strip())
            if match and int(match.group(1)) in _DP_ROWS_A1:
                return True
        return False


class ProductTemplate(models.Model):
    _inherit = "product.template"

    cssk_kh_commodity_code = fields.Char(
        string="KH commodity code (§92a)", help=_KH_CODE_HELP)
