# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""SK Prehľad — o zrazených a odvedených preddavkoch na daň (monthly).

Filed monthly to the Finančná správa (tax administrator) under § 39 ods. 9
zákona 595/2003 Z. z.  Unlike the MVP/social overview, the Prehľad is
**employer-aggregate only** (no per-employee annex) — every figure is a
company-level sum for the reporting month.

Line mapping (from the official PREHLADv-poucenie), amounts summed across the
company's payslips for the period:

======  ==============================================  ======================
Line    Meaning                                          Source (rule codes)
======  ==============================================  ======================
r00     úhrn zúčt. a vypl. zdaniteľných príjmov          Σ GROSS
r01     úhrn zrazených preddavkov na daň (bez bonusu)    Σ INCOMETAX19+25 / INCOMETAX
r04     úhrn r. 1 až 3                                   = r01 (r02, r03 = 0)
r05     daňový bonus § 33 vyplatený                      Σ CHILD_BONUS
r08     odvodová povinnosť (r4 − r5 − r6 − r7)           r01 − CHILD_BONUS
rA/rB   rekapitulácia daňového bonusu § 33               Σ CHILD_BONUS
======  ==============================================  ======================

The monthly income-tax advance is emitted as INCOMETAX19+INCOMETAX25 by the
``hr_payroll`` engine and as a single INCOMETAX line by the ``payroll``
engine; ``_tax_advance`` handles both.  r02/r03 (ročné zúčtovanie corrections),
r06/r07 (zamestnanecká prémia, § 33a úroky bonus) and the III. časť žiadosti
have no monthly rule source and are left empty / zero.
"""
import calendar as _calendar
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_cssk_core.tools import split_street
from odoo.addons.l10n_cssk_payroll_declaration_base.rule_codes import sum_concept

# The rule codes carrying the income-tax advance differ per engine (Enterprise
# splits it into 19 %/25 % bands, the OCA engine emits one line). That mapping
# lives once, in the declaration base, rather than being restated here.
# Daňový bonus (§ 33) paid to employees.
BONUS_CODE = "CHILD_BONUS"
# The žiadosť o poukázanie rozdielu daňového bonusu (III. časť) may only be
# filed in the Prehľad for the last month of a calendar quarter.
QUARTER_END_MONTHS = ("3", "6", "9", "12")


class L10nSkPrehlad(models.Model):
    _name = "l10n.sk.prehlad"
    _inherit = ["cssk.payroll.declaration.mixin", "mail.thread",
                "mail.activity.mixin"]
    _description = "SK monthly overview of withheld tax advances"
    _order = "date_from desc, id desc"

    _report_code = "sk_prehlad"
    # The FS Prehľad wire format carries a riadny/opravný pair and nothing
    # else — no dodatočný, no storno — so only those two are offered.
    _supported_correction_types = ("regular", "corrective")
    _country_code = "SK"
    _xml_name_fallback = "prehlad"

    request_bonus_refund = fields.Boolean(
        string="Request refund of the child tax bonus difference",
        help="Fill in Part III of the overview: ask the tax administrator to "
        "pay out the child tax bonus the company paid from its own money "
        "because it exceeded the withheld tax advances (row C of Part II), "
        "summed over the three months of the quarter. Only possible in the "
        "overview for the last month of a calendar quarter (March, June, "
        "September, December). Leave it off to deduct the difference from "
        "the tax advances of the following months instead.",
        tracking=True,
    )

    @api.constrains("request_bonus_refund", "month")
    def _check_request_bonus_refund_quarter(self):
        for rec in self:
            if rec.request_bonus_refund and rec.month not in QUARTER_END_MONTHS:
                raise ValidationError(_(
                    "The child tax bonus difference can only be claimed in "
                    "the overview for the last month of a calendar quarter "
                    "(March, June, September or December)."))

    # ------------------------------------------------------------------
    @staticmethod
    def _digits(value):
        return "".join(ch for ch in (value or "") if ch.isdigit())

    def _company_dic(self, company):
        return self._digits(company.l10n_sk_dic)

    def _preflight(self):
        super()._preflight()
        for rec in self:
            dic = rec._company_dic(rec.company_id)
            if not (dic.isdigit() and len(dic) == 10):
                raise UserError(_(
                    "Company '%(company)s' needs a 10-digit DIČ (tax "
                    "identification number) for the monthly tax overview <dic> "
                    "element. Set 'DIČ' on the company.",
                    company=rec.company_id.display_name))
            if rec.request_bonus_refund and not rec.company_id.partner_id.bank_ids:
                raise UserError(_(
                    "Company '%(company)s' needs a bank account for the "
                    "refund of the child tax bonus difference requested in "
                    "Part III of the overview.",
                    company=rec.company_id.display_name))
        return True

    # ------------------------------------------------------------------
    def _tax_advance(self, agg):
        """Withheld monthly income-tax advance before the daňový bonus."""
        return sum_concept(agg, "INCOME_TAX")

    @staticmethod
    def _company_legal_form(company):
        """The company's právna forma, or "" when nothing records it.

        The value is the ``l10n_sk_legal_form`` Char that
        ``l10n_sk_trade_registry`` adds to the PARTNER. This used to call
        ``company.l10n_sk_legal_form()`` behind a ``hasattr`` on the company,
        which no module defines, so pravnaForma was always empty.
        """
        partner = company.partner_id
        if "l10n_sk_legal_form" not in partner._fields:
            return ""
        return partner.l10n_sk_legal_form or ""

    def _bonus_split(self, agg):
        """``(r04, bonus, r05)`` of one month's aggregate.

        r. 5 carries the § 33 bonus only up to r. 4; the poučenie has the
        employer pay the rest from its own money (II. časť, r. C).
        """
        r04 = self._tax_advance(agg)
        bonus = abs(round(agg.get(BONUS_CODE, 0.0), 2))
        return r04, bonus, round(min(bonus, r04), 2)

    def _quarter_bonus_difference(self):
        """Σ r. C over the three months of this record's quarter.

        The amount of the žiadosť in III. časť: the bonus paid from the
        employer's own money in each month of the quarter, recomputed from
        that month's non-cancelled payslips the same way as r. C.
        """
        self.ensure_one()
        year, last = int(self.year), int(self.month)
        Payslip = self.env["hr.payslip"]
        total = 0.0
        for month in range(last - 2, last + 1):
            slips = Payslip.search([
                ("company_id", "=", self.company_id.id),
                ("date_from", ">=", date(year, month, 1)),
                ("date_to", "<=", date(
                    year, month, _calendar.monthrange(year, month)[1])),
                ("state", "!=", "cancel"),
            ])
            agg = self._collect_payslip_totals(slips)["aggregate"]
            _r04, bonus, r05 = self._bonus_split(agg)
            total += bonus - r05
        return round(total, 2)

    def _declaration_render_context(self, data):
        self.ensure_one()
        agg = data["aggregate"]
        company = self.company_id
        payment = self.payment_date or self.date_to

        r00 = abs(round(agg.get("GROSS", 0.0), 2))
        r01 = self._tax_advance(agg)
        r04, bonus, r05 = self._bonus_split(agg)
        r08 = round(r04 - r05, 2)

        # bank IBAN (first account of the company partner), for III. časť
        iban = ""
        banks = company.partner_id.bank_ids
        if banks:
            iban = (banks[0].acc_number or "").replace(" ", "")[:34]

        # The house number is split off the street (l10n_cssk_core), never
        # Street 2 — a building, a floor or a c/o line.
        ulica, cislo = split_street(company)
        prehlad = {
            "dic": self._company_dic(company),
            # Riadny and opravný are mutually exclusive flags in the FS wire
            # format; both used to be hardcoded, so the form could only ever
            # emit a regular Prehľad.
            "riadny": "0" if self.is_correction else "1",
            "opravny": "1" if self.is_correction else "0",
            "mesiac": str(int(self.month)),
            "rok": str(int(self.year)),
            # PO identification
            "nazov": (company.name or "")[:255],
            "pravna_forma": self._company_legal_form(company),
            # sídlo
            "ulica": ulica[:255],
            "cislo": cislo[:20],
            "psc": self._digits(company.zip)[:5],
            "obec": (company.city or "")[:255],
            "stat": (company.country_id.code or "SK"),
            "tel": (company.phone or "")[:30],
            "email": (company.email or "")[:255],
            # I. časť — preddavky na daň
            "r00": "%.2f" % r00,
            "r01_datum": payment.strftime("%d.%m.%Y") if payment else "",
            "r01_suma": "%.2f" % r01,
            "r04": "%.2f" % r04,
            "r05": "%.2f" % r05,
            "r08": "%.2f" % r08,
            # II. časť — rekapitulácia daňového bonusu § 33
            "rA": "%.2f" % bonus,
            "rB": "%.2f" % r05,
            "rC": "%.2f" % round(bonus - r05, 2),
            # III. časť — žiadosť o poukázanie rozdielu daňového bonusu,
            # only when asked for (otherwise the difference is deducted from
            # the following months' advances, which needs no filing).
            "bonus_ziadam": "1" if self.request_bonus_refund else "0",
            "bonus_suma": (
                "%.2f" % self._quarter_bonus_difference()
                if self.request_bonus_refund else ""),
            "iban": iban,
            # vyhotovil
            "zostavil": (self.env.user.name or "Odoo Payroll")[:255],
            "datum_vyhotovenia": fields.Date.context_today(self).strftime(
                "%d.%m.%Y"),
        }
        return {"p": prehlad}
