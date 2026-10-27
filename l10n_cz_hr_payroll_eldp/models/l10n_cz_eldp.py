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
* ``items/t1/@inc`` (vyměřovací základ / assessment base) ← Σ of the monthly
  assessment bases of the employee's confirmed payslips in the period, each
  rounded UP to whole Kč (§ 5d zák. 589/1992 Sb.). The monthly base is the
  amount of the ``SOCIALER`` line — the insurable gross already capped at the
  annual maximum assessment base (§ 15a), and absent for a month that was not
  insured (a DPP / DPČ under the threshold). GROSS was used before: uncapped,
  and including months that were not insured at all.
* ``items/t1/@din`` (dny / days) ← calendar days of the employment period
  inside the year.
* One ``t1`` row per employment period in the year, built from EVERY contract
  version (``contract_date_start`` .. ``contract_date_end``), not just the
  current one: an employee who left and came back, or whose earlier contract
  ended, has periods today's version does not show.
* ``items/@coun`` = number of ``t1`` rows; ``items/@sinc`` = Σ inc.

Header / identification (employee + hr.version lifecycle, NOT payslips):
``client`` ← employee name / birthday / birth number / private address;
``comp`` ← employer name / IČ / ČSSZ variable symbol; ``eldp09/@yer`` ← year;
``eldp09/@typ`` ← 1 (ongoing) / 2 (employment ended in the year);
``eldp09/@tco`` + ``@dep`` ← company OSSZ code.

Human-verify / assumptions (see README): excluded / deducted day columns
(``dex`` / ``dar``) emitted as ``0``; every period carries code 1 (employment).
"""
import math
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Zákon č. 360/2025 Sb., čl. V: from 2026 the ČSSZ compiles the ELDP from the
# unified monthly employer report (JMHZ). The employer still files one for
# 2026 only for an employee whose pension insurance ended before this day
# (or when the ČSSZ asks for it, which this module does not cover).
JMHZ_LIVE = date(2026, 4, 1)

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

    @api.depends("year")
    def _compute_period(self):
        """The record covers the whole calendar year; ``month`` is ignored.
        This is also what selects the form version (1 January)."""
        for rec in self:
            if rec.year:
                rec.date_from, rec.date_to = rec._year_bounds()
            else:
                rec.date_from = rec.date_to = False

    def _successor_hint(self):
        # ČSSZ, "Přehled informací k jednotlivým agendám ČSSZ v přechodném
        # období" (5. 3. 2026): "období před rokem 2026 jsou vykazována pouze
        # prostřednictvím ELDP; období od roku 2026 a později jsou vykazována
        # prostřednictvím JMHZ" (zákon č. 323/2025 Sb.).
        return _(
            "Pension insurance periods from 1 January 2026 are reported in "
            "the monthly employer report (JMHZ, Act No. 323/2025 Coll.). The "
            "ČSSZ may still ask for an ELDP in individual cases; prepare that "
            "one outside this module.")

    def _get_period_payslips(self):
        self.ensure_one()
        if "hr.payslip" not in self.env:
            return None
        y_start, y_end = self._year_bounds()
        payslips = self.env["hr.payslip"].search(self._payslip_period_domain(
            self.company_id, y_start, y_end))
        if y_start.year >= JMHZ_LIVE.year:
            payslips = payslips.filtered(
                lambda s: self._ended_before_jmhz(s.employee_id, y_start))
            if not payslips:
                raise UserError(_(
                    "An ELDP for %(year)s is filed only for an employee whose "
                    "pension insurance ended before 1 April 2026 (Act No. "
                    "360/2025 Coll., Art. V), and no employee with payslips "
                    "in %(year)s left before that day. The year is reported "
                    "in the monthly employer report (JMHZ); an ELDP the ČSSZ "
                    "asks for has to be prepared outside this module.",
                    year=self.year))
        return payslips

    def _ended_before_jmhz(self, employee, y_start):
        """Whether the employee's employment ended before 1 April 2026, read
        from all contract periods of the year, not the current version."""
        periods = self._employee_contract_intervals(
            employee, y_start, date(y_start.year, 12, 31))
        if not periods:
            return False
        return periods[-1][1] < JMHZ_LIVE

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

    def _employee_typ(self, periods, y_end):
        """2 when the last employment period ended inside the year."""
        if periods and periods[-1][1] < y_end:
            return TYP_ENDED
        return TYP_ONGOING

    @staticmethod
    def _monthly_base(slip):
        """The payslip's pension assessment base (§ 5): the ``SOCIALER``
        line amount, signed, so a refund payslip reduces the period. Zero
        for an uninsured month."""
        return sum(
            (line.amount or 0.0) * (
                line.quantity if line.quantity is not None else 1.0)
            for line in slip.line_ids if line.code == "SOCIALER")

    def _period_rows(self, periods, payslips):
        """One ``t1`` dict per employment period, with the bases of the
        payslips ending in it. A payslip ending outside every period (a
        final settlement paid after the last day) goes to the latest period
        that started before it, else to the first."""
        incs = [0.0] * len(periods)
        for slip in payslips:
            idx = 0
            for i, (lo, _hi) in enumerate(periods):
                if lo <= slip.date_to:
                    idx = i
            incs[idx] += self._monthly_base(slip)
        return [{
            "row": i + 1,
            "cod": "1",
            "fro": lo.isoformat(),
            "to": hi.isoformat(),
            "din": (hi - lo).days + 1,
            # Rounded UP to whole crowns (§ 5d); never negative.
            "inc": int(math.ceil(round(max(0.0, incs[i]), 2))),
        } for i, (lo, hi) in enumerate(periods)]

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

    def _build_eldp_employees(self, data):
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
            first, surname = self._split_person_name(emp)
            surname = surname or "-"
            first = first or "-"
            periods = self._employee_contract_intervals(emp, y_start, y_end)
            bucket = data["per_employee"].get(emp) or {}
            slips = bucket.get("payslips") or []
            if not periods:
                # Payslips but no employment in the year by the contract
                # dates: report the year rather than drop the base.
                periods = [(y_start, y_end)]
            if len(periods) > 3:
                # ELDP09.xsd: <t1> maxOccurs="3" per ELDP.
                raise UserError(_(
                    "Employee '%(name)s' has %(count)s separate employment "
                    "periods in %(year)s; one ELDP holds at most three. "
                    "Prepare the ELDP for this employee by hand.",
                    name=emp.display_name, count=len(periods), year=year))
            rows = self._period_rows(periods, slips)
            sinc = sum(r["inc"] for r in rows)
            out.append({
                "sqnr": sqnr,
                "yer": year,
                "typ": self._employee_typ(periods, y_end),
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
                "coun": len(rows),
                "sinc": sinc,
                "rows": rows,
                "comp_nam": (company.name or "")[:144],
                "comp_id": self._digits(company.company_registry)[:35],
                "comp_vs": int(vs),
                "comp_cre": today,
                "comp_fro": rows[0]["fro"],
            })
        return out

    def _declaration_render_context(self, data):
        self.ensure_one()
        return {
            "reldp_version": "2009.1",
            "eldp_employees": self._build_eldp_employees(data),
        }
