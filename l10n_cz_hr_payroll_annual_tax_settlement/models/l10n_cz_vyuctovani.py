# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""CZ Vyúčtování daně z příjmů ze závislé činnosti (DPZVD6) — ANNUAL tax
reconciliation summary filed to the Finanční správa via EPO.

Employer-AGGREGATE annual filing. The EPO envelope is ``<Pisemnost>`` wrapping a
single ``<DPZVD6>`` (attributeless-namespace, unqualified). Structure used here:

* ``VetaD`` — header + Part II annual summary. Required: ``zdobd_od`` /
  ``zdobd_do`` (tax period), ``k_uladis`` (fixed ``DPZ``), ``dokument`` (fixed
  ``VD6``), ``c_ufo_cil`` (tax-office code), ``vdadpz_typ`` (``B`` = řádné).
  Part II row 1 (``kc_dpzii01``) ← Σ annual advance income tax; ``poc_zam1..12``
  ← employee count per calendar month.
* ``VetaP`` — payer identification: ``typ_ds`` (F/P/L), ``dic`` (DIČ), name /
  address.
* ``VetaO`` — Part I, one row per calendar month: ``mesic`` + ``kc_dpzi01`` /
  ``kc_dpzi02`` ← that month's advance income tax (due / withheld).

Data source (via the engine-neutral base adapter, over the year's payslips):
the advance income tax ``INCOMETAX`` (záloha na daň, § 6), summed annually for
Part II and per month for Part I.

Human-verify / assumptions (see README):

* Only the advance-tax figures are emitted. ``WHTAX`` (srážková daň zvláštní
  sazbou) is reconciled on a SEPARATE form (Vyúčtování daně vybírané srážkou),
  so it is intentionally NOT mixed into DPZVD6 to avoid double counting.
* Part II is populated on row 1 only (Σ advances); the reconciliation
  difference / overpayment rows are left for manual completion.
* The per-employee annexes (VetaC / VetaH — non-residents) are not generated.
"""
import calendar as _calendar
from collections import defaultdict
from datetime import date

from odoo import _, fields, models
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

    def _get_period_payslips(self):
        self.ensure_one()
        if "hr.payslip" not in self.env:
            return None
        y_start, y_end = self._year_bounds()
        return self.env["hr.payslip"].search([
            ("company_id", "=", self.company_id.id),
            ("date_from", ">=", y_start),
            ("date_to", "<=", y_end),
            ("state", "!=", "cancel"),
        ])

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
    def _monthly_breakdown(self, payslips):
        """{month: {'tax': float, 'emps': set()}} from the year's payslips."""
        monthly = defaultdict(lambda: {"tax": 0.0, "emps": set()})
        for slip in payslips:
            month = (slip.date_from or slip.date_to).month
            monthly[month]["emps"].add(slip.employee_id.id)
            for line in slip.line_ids:
                if line.code == "INCOMETAX":
                    monthly[month]["tax"] += line.total
        return monthly

    def _declaration_render_context(self, data):
        self.ensure_one()
        company = self.company_id
        year = int(self.year)
        payslips = self._get_period_payslips()
        monthly = self._monthly_breakdown(payslips)

        annual_tax = int(round(abs(data["aggregate"].get("INCOMETAX", 0.0))))

        # VetaD header + Part II summary.
        vetad = {
            "k_uladis": "DPZ",
            "dokument": "VD6",
            "zdobd_od": date(year, 1, 1).strftime("%d.%m.%Y"),
            "zdobd_do": date(year, 12, 31).strftime("%d.%m.%Y"),
            "c_ufo_cil": self._digits(company.l10n_cz_fu_code),
            "vdadpz_typ": "B",  # B = řádné (regular)
            "kc_dpzii01": str(annual_tax),
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
        vetao = []
        for m in sorted(monthly):
            month_tax = int(round(abs(monthly[m]["tax"])))
            vetao.append({
                "mesic": str(m),
                "kc_dpzi01": str(month_tax),
                "kc_dpzi02": str(month_tax),
            })

        return {
            "verze_pis": "1.0",
            "vetad": vetad,
            "vetap": vetap,
            "vetao": vetao,
            "annual_tax": annual_tax,
        }
