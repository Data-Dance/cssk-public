# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""CZ ELDP — Evidenční list důchodového pojištění (ANNUAL pension record).

Per-employee ANNUAL pension-insurance record filed to the ČSSZ
(ns ``http://schemas.cssz.cz/ELDP09``, root ``<RELDP>`` carrying one
``<eldp09>`` per employee). Unlike the monthly PVPOJ, ELDP aggregates the WHOLE
calendar year: for each employee it sums the year's pension assessment base and
counts the days of pension insurance.

Data source (via the engine-neutral base adapter, over the year's payslips)
-------------------------------------------------------------------------
* ``items/t1/@inc`` (vyměřovací základ / assessment base) ← Σ ``GROSS`` across
  the employee's payslips for the calendar year (rounded to whole Kč). In the CZ
  system the pension-insurance assessment base equals the social-insurance base,
  which for standard employment is the insurable gross wage.
* ``items/t1/@din`` (dny / days) ← calendar days of pension insurance in the
  year = the employee's employment period (``contract_date_start`` ..
  ``contract_date_end``) intersected with the reporting year.
* ``items/@coun`` = number of ``t1`` periods (1 here); ``items/@sinc`` = Σ inc.

Header / identification (employee + hr.version lifecycle, NOT payslips):
``client`` ← employee name / birthday / birth number / private address;
``comp`` ← employer name / IČ / ČSSZ variable symbol; ``eldp09/@yer`` ← year;
``eldp09/@typ`` ← 1 (ongoing) / 2 (employment ended in the year);
``eldp09/@tco`` + ``@dep`` ← company OSSZ code.

Human-verify / assumptions (see README): single continuous period per employee;
assessment base uncapped (no max-base ceiling, no excluded income); excluded /
deducted day columns (``dex`` / ``dar``) emitted as ``0``.
"""
import calendar as _calendar
from datetime import date

from odoo import _, fields, models
from odoo.exceptions import UserError

# ELDP "Typ ELDP" (field 03) codes.
TYP_ONGOING = "1"   # zaměstnání trvá (continues past year-end)
TYP_ENDED = "2"     # zaměstnání skončilo v daném roce


class L10nCzEldp(models.Model):
    _name = "l10n.cz.eldp"
    _inherit = ["cssk.payroll.declaration.mixin", "mail.thread",
                "mail.activity.mixin"]
    _description = "Czech ELDP — Pension Insurance Record"
    _order = "year desc, id desc"

    _report_code = "cz_eldp"
    _country_code = "CZ"
    _xml_name_fallback = "eldp"

    # ------------------------------------------------------------------
    # Annual period: ELDP aggregates the WHOLE calendar year, so override the
    # payslip window (the mixin defaults to a single month).
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
    def _preflight(self):
        super()._preflight()
        for rec in self:
            company = rec.company_id
            vs = "".join(ch for ch in (company.l10n_cz_ossz_vs or "")
                         if ch.isdigit())
            if not (8 <= len(vs) <= 10):
                raise UserError(_(
                    "Company '%(company)s' needs an 8-10 digit ČSSZ variable "
                    "symbol for the ELDP <comp vs>. Set 'ČSSZ variable symbol "
                    "(VS)' on the company.", company=company.display_name))
            code = (company.l10n_cz_ossz_code or "").strip()
            if not (code.isdigit() and 100 <= int(code) <= 999):
                raise UserError(_(
                    "Company '%(company)s' needs a valid OSSZ code (100-999) "
                    "for the ELDP <eldp09 tco/dep>.",
                    company=company.display_name))
        return True

    # ------------------------------------------------------------------
    @staticmethod
    def _digits(value):
        return "".join(ch for ch in (value or "") if ch.isdigit())

    def _employee_insured_days(self, employee, y_start, y_end):
        """Calendar days of pension insurance in the year = employment period
        intersected with [y_start, y_end]. Approximates a single continuous
        engagement from the employee's current version contract dates."""
        version = employee.version_id
        start = version.contract_date_start or y_start
        end = version.contract_date_end or y_end
        lo = max(start, y_start)
        hi = min(end, y_end)
        return ((hi - lo).days + 1) if hi >= lo else 0

    def _employee_typ(self, employee, y_start, y_end):
        end = employee.version_id.contract_date_end
        if end and y_start <= end <= y_end:
            return TYP_ENDED
        return TYP_ONGOING

    def _client_address(self, employee):
        """Employee private address for <client><adr>. All parts required by
        the XSD; a missing house number is approximated from the street."""
        street = (employee.private_street or "").strip()
        num = ""
        # split a trailing house number off the street if present
        parts = street.rsplit(" ", 1)
        if len(parts) == 2 and any(c.isdigit() for c in parts[1]):
            street, num = parts[0], parts[1]
        city = (employee.private_city or "").strip()
        zip_ = self._digits(employee.private_zip)
        country = (employee.private_country_id.code
                   or self.company_id.country_id.code or "CZ")
        return {
            "cit": city or "-",
            "str": street or city or "-",
            "num": num or "0",
            "pos": (city or "-")[:5],
            "pnu": zip_ or "00000",
            "cnt": country,
        }

    def _build_eldp_employees(self):
        """Per-employee eldp09 render dicts (declarative for the template)."""
        self.ensure_one()
        y_start, y_end = self._year_bounds()
        year = int(self.year)
        company = self.company_id
        vs = self._digits(company.l10n_cz_ossz_vs)
        ossz = (company.l10n_cz_ossz_code or "").strip()
        today = fields.Date.context_today(self).isoformat()
        out = []
        sqnr = 0
        for line in self._sheet_lines().sorted("sequence"):
            sqnr += 1
            emp = line.employee_id
            bno = self._digits(emp.identification_id)
            if not (9 <= len(bno) <= 10):
                raise UserError(_(
                    "Employee '%(name)s' needs a 9-10 digit birth number "
                    "in the Identification No. field for the "
                    "ELDP <client bno>.", name=emp.display_name))
            if not emp.birthday:
                raise UserError(_(
                    "Employee '%(name)s' needs a birthday for the ELDP "
                    "<birth dat>.", name=emp.display_name))
            surname, _sep, first = (emp.name or "").rpartition(" ")
            surname = surname or emp.name or "-"
            first = first or "-"
            days = self._employee_insured_days(emp, y_start, y_end)
            inc = int(round(abs(line.vz_base)))
            version = emp.version_id
            fro = (version.contract_date_start or y_start)
            fro = max(fro, y_start)
            end = version.contract_date_end
            to = min(end, y_end) if end else y_end
            out.append({
                "sqnr": sqnr,
                "yer": year,
                "typ": self._employee_typ(emp, y_start, y_end),
                "dep": ossz,
                "tco": ossz,
                "nam": (company.name or "")[:144],
                "bno": bno,
                "sur": surname[:50],
                "fir": first[:50],
                "birth_dat": emp.birthday.isoformat(),
                "birth_nam": surname[:50],
                "birth_cit": (emp.place_of_birth or "-")[:50],
                "adr": self._client_address(emp),
                "coun": 1,
                "sinc": inc,
                "row": 1,
                "cod": "1",
                "fro": fro.isoformat(),
                "to": to.isoformat(),
                "din": days,
                "inc": inc,
                "comp_nam": (company.name or "")[:144],
                "comp_id": self._digits(company.company_registry)[:35],
                "comp_vs": int(vs),
                "comp_cre": today,
                "comp_fro": fro.isoformat(),
            })
        return out

    def _declaration_render_context(self, data):
        self.ensure_one()
        return {
            "reldp_version": "2009.1",
            "eldp_employees": self._build_eldp_employees(),
        }
