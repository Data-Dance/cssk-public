# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""CZ PVPOJ — Přehled o výši pojistného (monthly social-insurance overview).

Employer-AGGREGATE filing to the ČSSZ (ns http://schemas.cssz.cz/POJ/PVPOJ2025).
Almost every value is a company-level sum; the only per-employee data is the
``slevaZamestnanci`` annex, which lists ONLY the employees for whom the employer
claims the part-time premium discount (§ sleva na pojistném).

Rule-code mapping (from ``l10n_cz_hr_payroll_ee`` / ``l10n_cz_hr_payroll_oca``):

* ``pojistneZamestnavateleCelkem`` ← ``SOCIALERTOT`` (Σ employer social premium)
* ``pojistneZamestnance``          ← ``SOCIALEETOT`` (Σ employee social premium)
* ``pojistneCelkem``               ← ``SOCIALERTOT`` + ``SOCIALEETOT``
* ``zakladZamestnavateleA``        ← employer assessment base, band A, derived
  as ``SOCIALERTOT / 0.248`` (the standard 24.8 % employer rate); most employers
  are band A only, and the band B/C selectors are out of scope here.
* ``pojistneZamestnavateleA``      ← ``SOCIALERTOT`` (single-band employer)
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
from odoo import _, fields, models
from odoo.exceptions import UserError

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

    # Employer social premium rate for band A (used to derive the assessment
    # base the schema wants alongside the premium).
    _EMPLOYER_SOCIAL_RATE_A = 0.248

    def _preflight(self):
        super()._preflight()
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
        disc_total = 0.0
        base_total = 0.0
        for bucket in data.get("per_employee", {}).values():
            totals = bucket["totals"]
            disc = abs(totals.get("SOCIAL_DISCOUNT", 0.0))
            if not disc:
                continue
            employee = bucket["employee"]
            base = abs(totals.get("GROSS", 0.0))
            disc_total += disc
            base_total += base
            name_parts = (employee.name or "").split()
            first = name_parts[0] if name_parts else (employee.name or "-")
            last = " ".join(name_parts[1:]) if len(name_parts) > 1 else first
            category = getattr(
                employee, "l10n_cz_social_discount_category", False)
            hpw = self._weekly_hours(employee.resource_calendar_id)
            rows.append({
                "jmeno": first,
                "prijmeni": last,
                "datum_narozeni": employee.birthday.isoformat()
                if employee.birthday else False,
                "vymerovaci_zaklad": round(base),
                "duvod_slevy": _SOCIAL_DISCOUNT_REASON.get(category, "g"),
                "kratsi_pracovni_doba": round(hpw, 2) if hpw else False,
            })
        return {
            "sleva_rows": rows,
            "sleva_pocet": len(rows),
            "sleva_uhrn_vz": round(base_total),
            "sleva_pojistne": round(disc_total),
        }

    def _declaration_render_context(self, data):
        agg = data["aggregate"]
        social_ee = abs(agg.get("SOCIALEETOT", 0.0))
        social_er = abs(agg.get("SOCIALERTOT", 0.0))
        pojistne_er_total = round(social_er)
        pojistne_ee_total = round(social_ee)
        pojistne_celkem = pojistne_er_total + pojistne_ee_total
        base_a = round(social_er / self._EMPLOYER_SOCIAL_RATE_A) if social_er \
            else 0
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
