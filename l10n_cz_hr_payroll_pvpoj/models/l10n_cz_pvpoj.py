# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""CZ PVPOJ — Přehled o výši pojistného (monthly social-insurance overview).

Employer-AGGREGATE filing to the ČSSZ (ns http://schemas.cssz.cz/POJ/PVPOJ2025).
Almost every value is a company-level sum; the only per-employee data is the
``slevaZamestnanci`` annex, which lists ONLY the employees for whom the employer
claims the part-time premium discount (§ sleva na pojistném).

Rule-code mapping (from ``l10n_cz_hr_payroll_ee`` / ``l10n_cz_hr_payroll_oca``):

* ``zakladZamestnavateleA``        ← the employer's assessment base, band A:
  Σ of the employees' bases (§ 5a odst. 1 písm. a) zák. 589/1992 Sb.), each
  rounded UP to whole crowns (§ 5d). Read straight off the ``SOCIALER`` line,
  whose amount IS the employee's capped base; no longer back-derived from the
  premium, which could not be exact once premiums were rounded.
* ``pojistneZamestnavateleA``      ← 24.8 % of that base (§ 7 odst. 1 písm. a)),
  rounded UP to whole crowns ONCE, on the company total (§ 7 odst. 3) — not
  the sum of per-payslip premiums. Band B/C (risk / rescue work) is out of
  scope.
* ``pojistneZamestnance``          ← Σ the employees' premiums (``SOCIALEETOT``),
  each rounded UP to whole crowns (§ 7 odst. 3).
* ``pojistneCelkem``               ← employer + employee premium
* ``pojistneUhrada``               ← ``pojistneCelkem`` − ``pojistneSleva``

Part-time premium-discount annex (§ sleva na pojistném, since 2023)
------------------------------------------------------------------
The CZ rule set now carries a ``SOCIAL_DISCOUNT`` line (5 % employer discount for
eligible part-time employees) plus the per-employee eligibility field
``l10n_cz_social_discount_category``. When any payslip in the period has a
``SOCIAL_DISCOUNT`` amount, this report emits:

* the aggregate ``slevaZamestnavatele`` block (count / Σ assessment base / Σ
  discount), and
* the per-employee ``slevaZamestnanci`` annex — one ``zamestnanec`` row per
  discounted employee (name, date of birth, assessment base, ``duvodSlevy``
  reason letter per § 7a odst. 1, and the shorter weekly working time).

``pojistneUhrada`` is reduced by the discount. When nobody has a discount the
optional blocks are omitted entirely (all ``minOccurs="0"``) and the report is
unchanged. ``slevyZamestnancu`` (employee-side discounts) stays out of scope.
"""
import math
from datetime import date

from odoo import _, fields, models
from odoo.exceptions import UserError

# The unified monthly employer report (JMHZ, zákon č. 323/2025 Sb.) replaces
# PVPOJ from January 2026. Only an employer that stopped being one before
# 1 April 2026 still files PVPOJ for January-March 2026 (zákon č. 360/2025
# Sb., čl. IX bod 3).
JMHZ_FIRST_PERIOD = date(2026, 1, 1)
JMHZ_LIVE = date(2026, 4, 1)

# § 7a odst. 1 písm. a)-g) reason letters for duvodSlevy (single character).
_SOCIAL_DISCOUNT_REASON = {
    "over55": "a",
    "parent_under10": "b",
    "carer": "c",
    "student": "d",
    "retraining": "e",
    "disabled": "f",
    "under21": "g",
}


class L10nCzPvpoj(models.Model):
    _name = "l10n.cz.pvpoj"
    _inherit = ["cssk.payroll.declaration.mixin", "mail.thread",
                "mail.activity.mixin"]
    _description = "Czech PVPOJ — Social Insurance Overview"
    _order = "date_from desc, id desc"

    _report_code = "cz_pvpoj"
    _country_code = "CZ"
    _xml_name_fallback = "pvpoj"

    # Employer social premium rate for band A, § 7 odst. 1 písm. a) zák.
    # 589/1992 Sb. (24.8 %).
    _EMPLOYER_SOCIAL_RATE_A = 0.248
    # Employer discount, § 7b odst. 1: 5 % of the discounted employees' bases.
    _SOCIAL_DISCOUNT_RATE = 0.05

    @staticmethod
    def _ceil_czk(value):
        """Round UP to whole crowns (§ 5d / § 7 odst. 3 / § 7b odst. 1),
        absorbing float noise so 1234.000001 stays 1234. Signed values are
        expected positive; a net negative (a refund payslip outweighing the
        month) reports zero rather than flipping into a liability."""
        return int(math.ceil(round(max(0.0, value or 0.0), 2)))

    def _employee_base(self, bucket):
        """The employee's assessment base for the month (§ 5, rounded up per
        § 5d): the amount of the ``SOCIALER`` line, which the rule computes
        as the insurable gross capped at the annual maximum. Zero for an
        employee who is not insured this month (no ``SOCIALER`` line)."""
        return self._ceil_czk(bucket["bases"].get("SOCIALER", 0.0))

    def _employees_on(self, day):
        """The company's employees whose employment covers *day*."""
        self.ensure_one()
        employees = self.env["hr.employee"].with_context(
            active_test=False).search([("company_id", "=", self.company_id.id)])

        def employed(emp):
            version = emp._get_version(day)
            start = version.contract_date_start
            end = version.contract_date_end
            return bool(start and start <= day and (not end or end >= day))

        return employees.filtered(employed)

    def _check_jmhz_transition(self):
        """PVPOJ for January-March 2026 only for an employer that ceased.

        Zákon č. 360/2025 Sb., čl. IX bod 3: whoever was an employer at least
        one day between 1 January and 31 March 2026 and "v den 1. dubna 2026
        již není zaměstnavatelem" files the přehled for those months. Anyone
        still employing on 1 April 2026 reports them through JMHZ instead.
        """
        for rec in self:
            if not rec.date_from or rec.date_from < JMHZ_FIRST_PERIOD:
                continue
            still = rec._employees_on(JMHZ_LIVE)
            if still:
                raise UserError(_(
                    "PVPOJ for %(month)s/%(year)s is filed only by an employer "
                    "that was no longer an employer on 1 April 2026 (Act No. "
                    "360/2025 Coll., Art. IX point 3). %(count)s employee(s) "
                    "of %(company)s are still employed on that day, so the "
                    "period is reported in the monthly employer report (JMHZ).",
                    month=rec.month, year=rec.year, count=len(still),
                    company=rec.company_id.display_name))

    def _successor_hint(self):
        # ČSSZ, "Přehled informací k jednotlivým agendám ČSSZ v přechodném
        # období" (5. 3. 2026): "PVPOJ se zasílali zaměstnavatelé naposledy
        # za prosinec 2025" (doprovodný zákon č. 360/2025 Sb. to the JMHZ
        # act, zákon č. 323/2025 Sb.).
        return _(
            "From January 2026 the social insurance premium is reported in "
            "the monthly employer report (JMHZ, Act No. 323/2025 Coll.).")

    def _preflight(self):
        super()._preflight()
        self._check_jmhz_transition()
        for rec in self:
            company = rec.company_id
            vs = (company.l10n_cz_ossz_vs or "").strip()
            if not (vs.isdigit() and len(vs) == 10):
                raise UserError(_(
                    "Company '%(company)s' needs a 10-digit ČSSZ variable "
                    "symbol for the PVPOJ <vs> element. "
                    "Set 'ČSSZ variable symbol (VS)' on the company.",
                    company=company.display_name))
            code = (company.l10n_cz_ossz_code or "").strip()
            if not (code.isdigit() and 100 <= int(code) <= 999):
                raise UserError(_(
                    "Company '%(company)s' needs a valid OSSZ code (100-999) "
                    "for the PVPOJ <kodOSSZ> element.",
                    company=company.display_name))
            if not (company.city and company.zip):
                raise UserError(_(
                    "Company '%(company)s' needs a city and ZIP for the PVPOJ "
                    "employer address.", company=company.display_name))
        return True

    @staticmethod
    def _weekly_hours(calendar):
        """Shorter working time in h/week (engine-neutral; 0.0 if unknown)."""
        if not calendar:
            return 0.0
        if "hours_per_week" in calendar._fields:
            return calendar.hours_per_week or 0.0
        weeks = 2.0 if calendar.two_weeks_calendar else 1.0
        atts = calendar.attendance_ids
        return (sum(a.hour_to - a.hour_from for a in atts) / weeks) if atts else 0.0

    def _collect_social_discount(self, data):
        """Build the per-employee §7a discount annex + its aggregate totals.

        Reads the ``SOCIAL_DISCOUNT`` payslip line (already gathered by the base
        adapter) per employee; the assessment base is that employee's ``GROSS``.
        """
        rows = []
        base_total = 0
        for bucket in data.get("per_employee", {}).values():
            totals = bucket["totals"]
            disc = abs(totals.get("SOCIAL_DISCOUNT", 0.0))
            if not disc:
                continue
            employee = bucket["employee"]
            base = self._employee_base(bucket)
            base_total += base
            # Same rule as ELDP and ONZ: the last word is the surname.
            first, last = self._split_person_name(employee)
            first = first or last or "-"
            last = last or first
            category = getattr(
                employee, "l10n_cz_social_discount_category", False)
            hpw = self._weekly_hours(employee.resource_calendar_id)
            rows.append({
                "jmeno": first,
                "prijmeni": last,
                "datum_narozeni": employee.birthday.isoformat()
                if employee.birthday else False,
                "vymerovaci_zaklad": base,
                "duvod_slevy": _SOCIAL_DISCOUNT_REASON.get(category, "g"),
                "kratsi_pracovni_doba": round(hpw, 2) if hpw else False,
            })
        # § 7b odst. 1: 5 % of the TOTAL of the discounted employees' bases,
        # rounded up once — not the sum of the payslips' own discount lines.
        return {
            "sleva_rows": rows,
            "sleva_pocet": len(rows),
            "sleva_uhrn_vz": base_total,
            "sleva_pojistne": self._ceil_czk(
                base_total * self._SOCIAL_DISCOUNT_RATE) if rows else 0,
        }

    def _declaration_render_context(self, data):
        buckets = data.get("per_employee", {}).values()
        base_a = sum(self._employee_base(b) for b in buckets)
        pojistne_er_total = self._ceil_czk(
            base_a * self._EMPLOYER_SOCIAL_RATE_A)
        pojistne_ee_total = sum(
            # SOCIALEETOT is a deduction line, so its total is negative.
            self._ceil_czk(-b["totals"].get("SOCIALEETOT", 0.0))
            for b in buckets)
        pojistne_celkem = pojistne_er_total + pojistne_ee_total
        sleva = self._collect_social_discount(data)
        return {
            "mesic": str(int(self.month)),
            "rok": str(int(self.year)),
            "psc": (self.company_id.zip or "").replace(" ", ""),
            "today": fields.Date.context_today(self).isoformat(),
            # integer Kč values (castkaType = nonneg integer)
            "zaklad_zamestnavatele_a": base_a,
            "pojistne_zamestnavatele_a": pojistne_er_total,
            "pojistne_zamestnavatele_celkem": pojistne_er_total,
            "pojistne_zamestnance": pojistne_ee_total,
            "pojistne_celkem": pojistne_celkem,
            # §7a employer discount annex (omitted entirely when nobody qualifies)
            "has_discount": bool(sleva["sleva_rows"]),
            "sleva_pocet": sleva["sleva_pocet"],
            "sleva_uhrn_vz": sleva["sleva_uhrn_vz"],
            "sleva_pojistne": sleva["sleva_pojistne"],
            "sleva_zamestnanci": sleva["sleva_rows"],
            "pojistne_uhrada": pojistne_celkem - sleva["sleva_pojistne"],
        }
