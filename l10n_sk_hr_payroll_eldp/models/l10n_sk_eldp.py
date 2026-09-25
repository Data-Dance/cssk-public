# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""SK ELDP — Evidenčný list dôchodkového poistenia (annual pension record).

Filed to the Sociálna poisťovňa (ns http://socpoist.sk/xsd/eldpzec, root
``spELDPZec`` — the *hromadný* batch of per-employee pension records). Unlike
the monthly MVP/VPP, ELDP is **annual and per-employee**: for each employee it
reports, for the calendar year, the pension assessment base (vymeriavací základ
dôchodkového poistenia) and the insured period.

This report reuses the engine-neutral payslip adapter but over a **whole-year**
period: ``_compute_period`` spans 1 Jan – 31 Dec of ``year`` (the ``month``
field is ignored), so ``action_generate`` aggregates every payslip of the year
per employee. The annual pension base ``vzDP`` is taken from the summed GROSS
(``vz_base`` on each employee line) — the Slovak pension assessment base equals
gross earnings minus the statutory exemptions already netted out in GROSS.

One ``eldpZec`` element is emitted per employee, mapping directly onto
``cssk.payroll.employee.declaration``.
"""
import calendar as _calendar
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class L10nSkEldp(models.Model):
    _name = "l10n.sk.eldp"
    _inherit = ["cssk.payroll.declaration.mixin", "mail.thread",
                "mail.activity.mixin"]
    _description = "SK ELDP annual pension-insurance record sheet"
    _order = "year desc, id desc"

    _report_code = "sk_eldp"
    _country_code = "SK"
    _xml_name_fallback = "eldp"

    # ------------------------------------------------------------------
    # Annual period (the whole calendar year, month is irrelevant).
    # ------------------------------------------------------------------
    @api.depends("year")
    def _compute_period(self):
        for rec in self:
            if rec.year:
                y = int(rec.year)
                rec.date_from = date(y, 1, 1)
                rec.date_to = date(y, 12, _calendar.monthrange(y, 12)[1])
            else:
                rec.date_from = rec.date_to = False

    @api.depends("year", "company_id")
    def _compute_name(self):
        for rec in self:
            rec.name = "ELDP %s" % (rec.year or "")

    # ------------------------------------------------------------------
    def _preflight(self):
        super()._preflight()
        for rec in self:
            company = rec.company_id
            if not rec._company_icz(company):
                raise UserError(_(
                    "Company '%(company)s' needs a 10-digit Sociálna poisťovňa "
                    "identification number for the ELDP "
                    "<icz> element. Set 'Sociálna poisťovňa variable symbol' "
                    "on the company.", company=company.display_name))
            if not rec._company_ico(company):
                raise UserError(_(
                    "Company '%(company)s' needs an 8-digit IČO (Company "
                    "Registry) for the ELDP <ico> element.",
                    company=company.display_name))
            if not (company.city and rec._company_psc(company)):
                raise UserError(_(
                    "Company '%(company)s' needs a city and a 5-digit ZIP for "
                    "the ELDP employer address (korAdresa).",
                    company=company.display_name))
        return True

    @staticmethod
    def _digits(value):
        return "".join(ch for ch in (value or "") if ch.isdigit())

    def _company_icz(self, company):
        icz = self._digits(company.l10n_sk_sp_vs)
        return icz if len(icz) == 10 else False

    def _company_ico(self, company):
        ico = self._digits(company.company_registry)
        return ico if len(ico) == 8 else False

    def _company_psc(self, company):
        psc = self._digits(company.zip)
        return psc if len(psc) == 5 else False

    @staticmethod
    def _split_name(name):
        parts = (name or "").split()
        meno = parts[0] if parts else "-"
        priezvisko = parts[-1] if len(parts) > 1 else (parts[0] if parts else "-")
        return priezvisko[:36], meno[:24]

    @staticmethod
    def _fmt(d):
        return d.strftime("%d.%m.%Y") if d else False

    def _employee_period(self, employee):
        """(datVzniku, datZaniku|None, datOd, datDo) for the employee's insured
        relationship, clamped to the reporting year for the obdobie row."""
        hire = getattr(employee, "first_contract_date", False) or self.date_from
        departure = getattr(employee, "departure_date", False)
        dat_od = max(hire, self.date_from)
        if departure and departure <= self.date_to:
            dat_do = min(departure, self.date_to)
            zanik = departure
        else:
            dat_do = self.date_to
            zanik = None
        return hire, zanik, dat_od, dat_do

    def _declaration_render_context(self, data):
        self.ensure_one()
        company = self.company_id
        rows = []
        for line in self._sheet_lines().sorted("sequence"):
            employee = line.employee_id
            rc = self._digits(employee.identification_id)
            if not (9 <= len(rc) <= 10):
                raise UserError(_(
                    "Employee '%(name)s' needs a 9-10 digit birth number "
                    "in the Identification No. field for the "
                    "ELDP.", name=employee.display_name))
            if not employee.birthday:
                raise UserError(_(
                    "Employee '%(name)s' needs a date of birth for the ELDP "
                    "<datNarodenia> element.", name=employee.display_name))
            priezvisko, meno = self._split_name(employee.name)
            hire, zanik, dat_od, dat_do = self._employee_period(employee)
            rows.append({
                "rc": rc,
                "priezvisko": priezvisko,
                "meno": meno,
                "dat_narodenia": self._fmt(employee.birthday),
                "dat_vzniku": self._fmt(hire),
                "trva": zanik is None,
                "dat_zaniku": self._fmt(zanik),
                "rok": self.year,
                "znak_poist": "A",  # A = zamestnanec
                "dat_od": self._fmt(dat_od),
                "dat_do": self._fmt(dat_do),
                "vz_dp": "%.2f" % abs(round(line.vz_base, 2)),
                "dni_vyluc": 0,
            })
        user = self.env.user
        kontakt_priez, kontakt_meno = self._split_name(user.name or "Odoo")
        return {
            "icz": self._company_icz(company),
            "ico": self._company_ico(company),
            "nazov": (company.name or "")[:144],
            "obec": (company.city or "")[:50],
            "psc": self._company_psc(company),
            "ulica": (company.street or "")[:30],
            "eldp_rows": rows,
            "dat_odoslania": fields.Date.context_today(self).strftime(
                "%d.%m.%Y"),
            "kontakt": {
                "priezvisko": kontakt_priez,
                "meno": kontakt_meno,
                "email": (company.email or user.email or "-")[:64] or "-",
                "tel": (company.phone or "-")[:20] or "-",
            },
        }
