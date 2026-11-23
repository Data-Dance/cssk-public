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

A company whose wages are computed elsewhere enters GROSS, the advance and the
bonus by hand (``manual_entry``); the rows are then derived the same way.
"""
import calendar as _calendar
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_cssk_core.tools import split_street
from odoo.addons.l10n_cssk_payroll_declaration_base.rule_codes import (
    all_codes_for,
    sum_concept,
)

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

    # --- Amounts entered by hand ---------------------------------------
    # An employer whose wages are computed elsewhere (an external payroll
    # office) has no payslips here, and the form had nothing to sum: it could
    # be created but never generated.
    manual_entry = fields.Boolean(
        string="Enter the amounts by hand",
        default=lambda self: "hr.payslip" not in self.env,
        tracking=True,
        help="Fill the overview from the amounts entered below instead of "
        "summing the month's payslips. For a company whose wages are "
        "computed outside this database. Ticked by default when no payroll "
        "app is installed.",
    )
    manual_taxable_income = fields.Monetary(
        string="Taxable income paid (r. 0)",
        tracking=True,
        help="Úhrn zúčtovaných a vyplatených zdaniteľných príjmov: the "
        "taxable employment income settled and paid out to all employees "
        "for the month.",
    )
    manual_tax_advance = fields.Monetary(
        string="Tax advances withheld (r. 1)",
        tracking=True,
        help="Úhrn zrazených preddavkov na daň: the income-tax advances "
        "withheld from the employees, BEFORE the child tax bonus is taken "
        "off. Rows 4 and 8 are computed from it.",
    )
    manual_child_bonus = fields.Monetary(
        string="Child tax bonus paid (§ 33)",
        tracking=True,
        help="Daňový bonus podľa § 33 paid to the employees in total (Part "
        "II, row A). Row 5 takes it up to the withheld advances; the rest "
        "is row C of Part II.",
    )

    @api.constrains("manual_taxable_income", "manual_tax_advance",
                    "manual_child_bonus")
    def _check_manual_amounts(self):
        for rec in self:
            if min(rec.manual_taxable_income, rec.manual_tax_advance,
                   rec.manual_child_bonus) < 0:
                raise ValidationError(_(
                    "The amounts of the overview are entered as positive "
                    "numbers."))

    def write(self, vals):
        # A generated or filed overview states the figures it was rendered
        # from: changing them afterwards would leave a file that no longer
        # says what the record does.
        if any(name in vals for name in self._manual_fields()) and any(
                rec.state != "draft" for rec in self):
            raise UserError(_(
                "Reset the overview to draft before changing its amounts."))
        return super().write(vals)

    @staticmethod
    def _manual_fields():
        return ("manual_entry", "manual_taxable_income", "manual_tax_advance",
                "manual_child_bonus")

    def _manual_aggregate(self):
        """The entered amounts as a ``{rule_code: total}`` aggregate, so that
        everything downstream reads them exactly as it reads payslips."""
        self.ensure_one()
        return {
            "GROSS": self.manual_taxable_income,
            all_codes_for("INCOME_TAX")[0]: self.manual_tax_advance,
            BONUS_CODE: self.manual_child_bonus,
        }

    def _generation_data(self):
        self.ensure_one()
        if not self.manual_entry:
            return super()._generation_data()
        return {
            "aggregate": self._manual_aggregate(),
            "aggregate_bases": {},
            "per_employee": {},
        }

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

    def _month_aggregate(self, year, month):
        """The aggregate one month of this record's quarter is reported from.

        An overview filled by hand has no payslips to go back to, so each
        earlier month comes from the overview GENERATED for it: the latest
        one, which is the corrective overview where the month was corrected.
        A draft is not taken, it states nothing yet. A month generated from
        payslips, or on a database with a payroll app a month with no
        overview, is recomputed from its non-cancelled payslips, as every
        month is when this overview itself comes from payslips.
        """
        self.ensure_one()
        has_engine = "hr.payslip" in self.env
        if self.manual_entry:
            if month == int(self.month):
                return self._manual_aggregate()
            other = self.search([
                ("company_id", "=", self.company_id.id),
                ("year", "=", str(year)),
                ("month", "=", str(month)),
                ("state", "!=", "draft"),
            ], order="id desc", limit=1)
            if other.manual_entry:
                return other._manual_aggregate()
            if not has_engine:
                if other:
                    raise UserError(_(
                        "The overview for %(month)02d/%(year)s was generated "
                        "from payslips and no payroll app is installed any "
                        "more, so its child tax bonus cannot be added to the "
                        "refund. Enter that month by hand in a new overview.",
                        month=month, year=year))
                raise UserError(_(
                    "The refund of the child tax bonus difference adds up "
                    "the three months of the quarter, and no overview was "
                    "generated for %(month)02d/%(year)s. Enter and generate "
                    "that month's overview first.", month=month, year=year))
        elif not has_engine:
            raise UserError(_(
                "No payroll engine is installed (hr.payslip is unavailable), "
                "so there are no payslips to aggregate."))
        slips = self.env["hr.payslip"].search([
            ("company_id", "=", self.company_id.id),
            ("date_from", ">=", date(year, month, 1)),
            ("date_to", "<=", date(
                year, month, _calendar.monthrange(year, month)[1])),
            ("state", "!=", "cancel"),
        ])
        return self._collect_payslip_totals(slips)["aggregate"]

    def _quarter_bonus_difference(self):
        """Σ r. C over the three months of this record's quarter.

        The amount of the žiadosť in III. časť: the bonus paid from the
        employer's own money in each month of the quarter, recomputed for
        each month the same way as r. C (see ``_month_aggregate``).
        """
        self.ensure_one()
        year, last = int(self.year), int(self.month)
        total = 0.0
        for month in range(last - 2, last + 1):
            agg = self._month_aggregate(year, month)
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
