# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""CZ Vyúčtování daně z příjmů ze závislé činnosti (DPZVD6) — ANNUAL tax
reconciliation summary filed to the Finanční správa via EPO.

Employer-AGGREGATE annual filing. The EPO envelope is ``<Pisemnost>`` wrapping a
single ``<DPZVD6>`` (attributeless-namespace, unqualified). Structure used here:

* ``VetaD`` — header + Part II annual summary. Required: ``zdobd_od`` /
  ``zdobd_do`` (tax period), ``k_uladis`` (fixed ``DPZ``), ``dokument`` (fixed
  ``VD6``), ``c_ufo_cil`` (tax-office code), ``vdadpz_typ`` (``B`` = řádné).
  Part II row 1 (``kc_dpzii01``) ← Σ Part I column 1; row 4 (``kc_dpzii03a``)
  ← Σ Part I column 5; ``poc_zam1..12`` ← employees on the payroll on the
  last day of each calendar month.
* ``VetaP`` — payer identification: ``typ_ds`` (F/P/L), ``dic`` (DIČ), name /
  address.
* ``VetaO`` — Part I, one row per calendar month: ``mesic``; ``kc_dpzi01`` /
  ``kc_dpzi02`` ← that month's advance AFTER the monthly credits (due /
  originally withheld); ``kc_dpzi05`` ← monthly child tax bonuses paid.
* ``VetaB`` — Příloha č. 1 "Počet zaměstnanců" (§ 38j odst. 1 ZDP), filed
  with every Vyúčtování: the employees on the payroll on 1 December, counted
  per municipality (ZÚJ) of their place of work. The place is the employee's
  work address; an agreement worker (DPP / DPČ) and anyone without a work
  address is counted at the employer's seat, as the pokyny direct. The ZÚJ
  code is kept on the address (contact) itself.

Data source (over the year's payslips): the pokyny to the form (MFin 5459/1)
define column 1 as "úhrn záloh na daň po měsíčních slevách na dani (tj. slevy
na dani podle § 35ba a sleva na dani z tit. daňového zvýhodnění podle § 35c a
35d zákona)". The payslip carries the advance BEFORE credits as ``INCOMETAX``
(negative) and the credits as ``TAXCREDIT`` (§ 35ba) and ``CHILDBEN`` (§ 35c,
the part of the child benefit offset against tax) — both positive — so the
column is ``-(INCOMETAX + TAXCREDIT + CHILDBEN)``. Column 5 is the bonus paid
out, ``CHILDBONUS``. Column 2 equals column 1 because § 38i corrections are
not tracked; they differ only when an advance was corrected before filing.

Human-verify / assumptions (see README):

* Only the advance-tax figures are emitted. ``WHTAX`` (srážková daň zvláštní
  sazbou) is reconciled on a SEPARATE form (Vyúčtování daně vybírané srážkou),
  so it is intentionally NOT mixed into DPZVD6 to avoid double counting.
* Part II is populated on row 1 only (Σ advances); the reconciliation
  difference / overpayment rows are left for manual completion.
* The non-resident annexes (VetaC / VetaH) are not generated.
"""
import calendar as _calendar
from collections import defaultdict
from datetime import date

from odoo import _, api, models
from odoo.exceptions import UserError


class L10nCzVyuctovani(models.Model):
    _name = "l10n.cz.vyuctovani"
    _inherit = ["cssk.payroll.declaration.mixin", "mail.thread",
                "mail.activity.mixin"]
    _description = "Czech Annual Tax Settlement Statement (DPZVD6)"
    _order = "year desc, id desc"

    _report_code = "cz_vyuctovani"
    _country_code = "CZ"
    _xml_name_fallback = "dpzvd6"

    # ------------------------------------------------------------------
    # Annual period (whole calendar year), overriding the monthly default.
    # ------------------------------------------------------------------
    def _year_bounds(self):
        self.ensure_one()
        y = int(self.year)
        return date(y, 1, 1), date(y, 12, 31)

    @api.depends("year")
    def _compute_period(self):
        """The filing covers the whole calendar year; ``month`` is ignored."""
        for rec in self:
            if rec.year:
                rec.date_from, rec.date_to = rec._year_bounds()
            else:
                rec.date_from = rec.date_to = False

    def _get_period_payslips(self):
        self.ensure_one()
        if "hr.payslip" not in self.env:
            return None
        y_start, y_end = self._year_bounds()
        return self.env["hr.payslip"].search(self._payslip_period_domain(
            self.company_id, y_start, y_end))

    # ------------------------------------------------------------------
    @staticmethod
    def _digits(value):
        return "".join(ch for ch in (value or "") if ch.isdigit())

    def _company_dic(self, company):
        return self._digits(company.vat)[:10]

    def _preflight(self):
        super()._preflight()
        for rec in self:
            company = rec.company_id
            if not self._company_dic(company):
                raise UserError(_(
                    "Company '%(company)s' needs a tax number (DIČ) for the "
                    "annual tax settlement <VetaP dic>. Set the company Tax ID.",
                    company=company.display_name))
            fu = self._digits(company.l10n_cz_fu_code)
            if not (fu and len(fu) <= 4):
                raise UserError(_(
                    "Company '%(company)s' needs a 1-4 digit tax-office code "
                    "(FÚ) for the annual tax settlement <VetaD c_ufo_cil>. "
                    "Set 'Tax office code (FÚ)' on the company.",
                    company=company.display_name))
        return True

    # ------------------------------------------------------------------
    # Příloha č. 1 — employees on 1 December per place of work (VetaB)
    # ------------------------------------------------------------------
    def _place_of_work(self, employee, day):
        """The address (res.partner) of *employee*'s place of work on *day*.

        Pokyny k příloze č. 1: the place of work in the employment contract;
        for an agreement worker (DPP / DPČ), or when the contract names more
        municipalities, the employer's seat. Without a work address on the
        contract version the seat is all we know.
        """
        version = employee.sudo()._get_version(day)
        seat = self.company_id.partner_id
        agreement = (version.l10n_cz_agreement_type
                     if "l10n_cz_agreement_type" in version._fields else False)
        if agreement in ("dpp", "dpc"):
            return seat
        return version.address_id or seat

    def _attachment_1_rows(self, payslips):
        """VetaB rows: employees with a payslip in the year who are on the
        payroll on 1 December, grouped by the ZÚJ of their place of work."""
        self.ensure_one()
        dec1 = date(int(self.year), 12, 1)
        places = defaultdict(set)
        for employee in payslips.employee_id:
            periods = self._employee_contract_intervals(employee, dec1, dec1)
            if not periods:
                continue
            places[self._place_of_work(employee, dec1)].add(employee.id)
        rows = []
        missing = []
        for partner, employees in places.items():
            zuj = self._digits(partner.l10n_cz_zuj_code)
            if len(zuj) != 6:
                missing.append(partner.display_name)
                continue
            row = {
                "c_obce_zuj": zuj,
                "poc_zam": str(len(employees)),
                "naz_vykonu": (partner.name or partner.city or "")[:40],
            }
            if partner.l10n_cz_zuj_name:
                row["naz_obce_zuj"] = partner.l10n_cz_zuj_name[:40]
            rows.append(row)
        if missing:
            raise UserError(_(
                "Příloha č. 1 to the annual tax settlement counts employees "
                "per municipality of their place of work, and these addresses "
                "have no 6-digit municipality code (ZÚJ): %(places)s. Set "
                "'Municipality code (ZÚJ)' on each of them.",
                places=", ".join(sorted(missing))))
        return sorted(rows, key=lambda r: r["c_obce_zuj"])

    # ------------------------------------------------------------------
    # Rule codes, as both CZ engines emit them (see rule_codes.py): the advance
    # before credits is negative, the two monthly credits positive.
    _TAX_AFTER_CREDIT_CODES = ("INCOMETAX", "TAXCREDIT", "CHILDBEN")
    _CHILD_BONUS_CODES = ("CHILDBONUS",)

    def _employed_on(self, employee, day):
        """Whether *employee*'s employment covers *day*, by the contract
        dates of the version in force on that day. Only called for an
        employee who has a payslip that month, so a missing start date
        counts as employed."""
        version = employee._get_version(day)
        start = version.contract_date_start
        end = version.contract_date_end
        return (not start or start <= day) and (not end or end >= day)

    def _monthly_breakdown(self, payslips):
        """{month: {'tax': float, 'bonus': float, 'emps': set()}}.

        ``tax`` is the advance after the monthly credits (signed as on the
        payslip, i.e. negative), ``bonus`` the child tax bonus paid, and
        ``emps`` the employees on the payroll on the LAST day of the month —
        the form counts "počet zaměstnanců k poslednímu dni měsíce", so
        someone who left on the 15th is not in that month's count.
        """
        year = int(self.year)
        monthly = defaultdict(
            lambda: {"tax": 0.0, "bonus": 0.0, "emps": set()})
        for slip in payslips:
            # The month the payslip ENDS in — the same date that put it into
            # this year — so a payslip straddling New Year cannot land in a
            # month of the wrong year.
            month = slip.date_to.month
            bucket = monthly[month]
            last_day = date(year, month, _calendar.monthrange(year, month)[1])
            if self._employed_on(slip.employee_id, last_day):
                bucket["emps"].add(slip.employee_id.id)
            for line in slip.line_ids:
                if line.code in self._TAX_AFTER_CREDIT_CODES:
                    bucket["tax"] += line.total
                elif line.code in self._CHILD_BONUS_CODES:
                    bucket["bonus"] += line.total
        return monthly

    def _declaration_render_context(self, data):
        self.ensure_one()
        company = self.company_id
        year = int(self.year)
        payslips = self._get_period_payslips()
        monthly = self._monthly_breakdown(payslips)

        # VetaD header + Part II summary.
        vetad = {
            "k_uladis": "DPZ",
            "dokument": "VD6",
            "zdobd_od": date(year, 1, 1).strftime("%d.%m.%Y"),
            "zdobd_do": date(year, 12, 31).strftime("%d.%m.%Y"),
            "c_ufo_cil": self._digits(company.l10n_cz_fu_code),
            "vdadpz_typ": "B",  # B = řádné (regular)
        }
        for m in range(1, 13):
            count = len(monthly.get(m, {}).get("emps", ()))
            if count:
                vetad["poc_zam%d" % m] = str(count)

        # VetaP payer identification.
        vetap = {
            "typ_ds": (company.l10n_cz_vyuctovani_typ_ds or "P"),
            "dic": self._company_dic(company),
            "zkrobchjm": (company.name or "")[:255],
        }
        if company.city:
            vetap["naz_obce"] = company.city[:255]
        if company.zip:
            vetap["psc"] = self._digits(company.zip)[:5]

        # VetaO — Part I, one row per calendar month with data.
        # Column 1 per the pokyny: the advance after the monthly credits,
        # which cannot be negative (the credits are capped at the advance).
        # Column 2 = column 1: § 38i corrections are not tracked here.
        vetao = []
        annual_tax = annual_bonus = 0
        for m in sorted(monthly):
            month_tax = max(0, int(round(-monthly[m]["tax"])))
            month_bonus = max(0, int(round(monthly[m]["bonus"])))
            annual_tax += month_tax
            annual_bonus += month_bonus
            row = {
                "mesic": str(m),
                "kc_dpzi01": str(month_tax),
                "kc_dpzi02": str(month_tax),
            }
            if month_bonus:
                row["kc_dpzi05"] = str(month_bonus)
            vetao.append(row)
        # Part II: row 1 = Σ column 1, row 4 = Σ column 5 (pokyny, Část II).
        vetad["kc_dpzii01"] = str(annual_tax)
        if annual_bonus:
            vetad["kc_dpzii03a"] = str(annual_bonus)

        return {
            "verze_pis": "1.0",
            "vetad": vetad,
            "vetap": vetap,
            "vetao": vetao,
            "vetab": self._attachment_1_rows(payslips),
            "annual_tax": annual_tax,
        }
