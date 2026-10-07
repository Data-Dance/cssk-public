# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""SK Hlásenie — annual employer wrap-up of withheld tax (§ 39 ods. 9).

Full name: "Hlásenie o vyúčtovaní dane a o úhrne príjmov zo závislej činnosti …
o zrazených preddavkoch na daň, o zamestnaneckej prémii, o daňovom bonuse a o
daňovom bonuse na zaplatené úroky" filed to the Finančná správa by the end of
the fourth month after the year end (§ 39 ods. 9 zák. 595/2003 Z. z.).

It is the ANNUAL counterpart of the monthly Prehľad (``l10n.sk.prehlad``): it
reuses the same tax-rule derivations (r00 income ← Σ GROSS, withheld advance ←
INCOMETAX / INCOMETAX19+25, daňový bonus ← CHILD_BONUS) but aggregates over the
whole calendar YEAR *and* carries a full per-employee annex (Časť V — one row
per employee with the year's income, withheld advance and daňový bonus). The
per-employee rows are ``cssk.payroll.employee.declaration`` records, exactly as
in the MVP annex pattern.

The XML matches the official schema ``data/rh2023.xsd`` (root ``dokument``, no
target namespace, ``elementFormDefault="qualified"``). Časť V is paginated two
employees per page (``cast5`` → ``c5stlpec1`` + ``c5stlpec2``); an odd trailing
column is emitted empty (every annex element is an optional type).
"""
import calendar as _calendar
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_cssk_payroll_declaration_base.rule_codes import sum_concept

# The rule codes carrying the income-tax advance differ per engine (Enterprise
# splits it into 19 %/25 % bands, the OCA engine emits one line). That mapping
# lives once, in the declaration base, rather than being restated here.
# Daňový bonus (§ 33) paid to employees.
BONUS_CODE = "CHILD_BONUS"
# Zamestnanecká prémia (§ 32a). No dedicated SK rule code today, so it resolves
# to 0.0 until an engine emits it; the mapping stays here for a future port.
EMPLOYEE_PREMIUM_CODE = "EMPLOYEEPREMIUM"


class L10nSkHlasenie(models.Model):
    _name = "l10n.sk.hlasenie"
    _inherit = ["cssk.payroll.declaration.mixin", "mail.thread",
                "mail.activity.mixin"]
    _description = "SK annual tax reconciliation statement (§ 39 ods. 9)"
    _order = "year desc, id desc"

    _report_code = "sk_hlasenie"
    # druhHlaseniaType in the shipped XSD is three mutually exclusive flags —
    # rh (riadne) / oh (opravné) / dh (dodatočné) — so the Hlásenie accepts a
    # corrective AND a supplementary filing, but there is no storno.
    _supported_correction_types = ("regular", "corrective", "supplementary")
    _country_code = "SK"
    _xml_name_fallback = "hlasenie"

    # ------------------------------------------------------------------
    # Annual period (the whole calendar year; the month field is ignored).
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
            rec.name = "Annual tax statement %s" % (rec.year or "")

    # ------------------------------------------------------------------
    # Preflight
    # ------------------------------------------------------------------
    def _preflight(self):
        super()._preflight()
        for rec in self:
            dic = rec._company_dic(rec.company_id)
            if not (dic.isdigit() and len(dic) == 10):
                raise UserError(_(
                    "Company '%(company)s' needs a 10-digit DIČ (tax "
                    "identification number) for the annual tax reconciliation "
                    "statement <dic> element. Set 'DIČ' on the company.",
                    company=rec.company_id.display_name))
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _digits(value):
        return "".join(ch for ch in (value or "") if ch.isdigit())

    def _company_dic(self, company):
        return self._digits(company.l10n_sk_dic)

    def _tax_advance_total(self, totals):
        """Withheld income-tax advance (before the daňový bonus) from a
        ``{code: total}`` mapping — engine-neutral (split bands or single)."""
        return sum_concept(totals, "INCOME_TAX")

    @staticmethod
    def _split_name(name):
        parts = (name or "").split()
        meno = parts[0] if parts else ""
        priezvisko = parts[-1] if len(parts) > 1 else (parts[0] if parts else "")
        return priezvisko[:36], meno[:24]

    # ------------------------------------------------------------------
    # Render context
    # ------------------------------------------------------------------
    def _declaration_render_context(self, data):
        self.ensure_one()
        agg = data["aggregate"]
        company = self.company_id
        user = self.env.user

        def a(code):
            return abs(round(agg.get(code, 0.0), 2))

        r00 = a("GROSS")
        r01 = self._tax_advance_total(agg)
        bonus = a(BONUS_CODE)
        premium = a(EMPLOYEE_PREMIUM_CODE)
        r04 = r01  # úhrn preddavkov na daň (r02/r03 have no annual rule source)
        r05 = round(min(bonus, r04), 2)  # daňový bonus § 33 vyplatený

        pages, emp_count = self._build_annex_pages()
        today = fields.Date.context_today(self)

        header = {
            "dic": self._company_dic(company),
            "rok": str(int(self.year)),
            # PO identification
            "nazov": (company.name or "")[:255],
            "pravna_forma": company.l10n_sk_legal_form()
            if hasattr(company, "l10n_sk_legal_form") else "",
            # sídlo
            "ulica": (company.street or "")[:255],
            "cislo": (company.street2 or "")[:20],
            "psc": self._digits(company.zip)[:5],
            "obec": (company.city or "")[:255],
            "stat": (company.country_id.code or "SK"),
            "tel": (company.phone or "")[:30],
            "email": (company.email or "")[:255],
            "vypracoval": (user.name or "Odoo Payroll")[:255],
            "datum": today.strftime("%d.%m.%Y"),
            # counts (we emit only Časť V, never Časť IV)
            "pocet_stran_c4": "0",
            "pocet_zam_c4": "0",
            "pocet_stran_c5": str(len(pages)),
            "pocet_zam_c5": str(emp_count),
        }
        body = {
            # I. časť — vyúčtovanie preddavkov na daň (aggregate)
            "r00": "%.2f" % r00,
            "r01": "%.2f" % r01,
            "r04": "%.2f" % r04,
            "r05": "%.2f" % r05,
            "r06": "%.2f" % premium,
            # bank IBAN for the žiadosť o vrátenie preplatku
            "iban": self._company_iban(company),
        }
        return {"h": header, "b": body, "pages": pages}

    def _company_iban(self, company):
        banks = company.partner_id.bank_ids
        if banks:
            return (banks[0].acc_number or "").replace(" ", "")[:34]
        return ""

    # ------------------------------------------------------------------
    # Per-employee annex (Časť V) — two employees per page/column pair.
    # ------------------------------------------------------------------
    def _build_annex_column(self, line):
        """One filled Časť V column (``c5stlpecType``) from an employee row."""
        employee = line.employee_id
        rc = self._digits(employee.identification_id)
        if not (9 <= len(rc) <= 10):
            raise UserError(_(
                "Employee '%(name)s' needs a 9-10 digit birth number "
                "in the Identification No. field for the annual tax "
                "reconciliation statement per-employee annex (Part V).",
                name=employee.display_name))
        totals = line.values_json or {}
        priezvisko, meno = self._split_name(employee.name)
        income = abs(round(totals.get("GROSS", 0.0), 2))
        advance = self._tax_advance_total(totals)
        bonus = abs(round(totals.get(BONUS_CODE, 0.0), 2))
        premium = abs(round(totals.get(EMPLOYEE_PREMIUM_CODE, 0.0), 2))
        return {
            "empty": False,
            "rodne_cislo": rc,          # c5rodneCislo (optInt)
            "dopln_udaj": "0",          # c5doplnUdaj (only_0_1)
            "priezvisko": priezvisko,
            "meno": meno,
            "ulica": (employee.private_street or "")[:255]
            if "private_street" in employee._fields else "",
            "psc": self._digits(getattr(employee, "private_zip", "") or "")[:5],
            "obec": (getattr(employee, "private_city", "") or "")[:255],
            "stat": "SK",
            "r3a": "%.2f" % income,     # úhrn zdaniteľných príjmov
            "r4a": "%.2f" % advance,    # úhrn zrazených preddavkov na daň
            "r6": "%.2f" % premium,     # zamestnanecká prémia
            "r8suma": "%.2f" % bonus,   # daňový bonus § 33
        }

    @staticmethod
    def _empty_annex_column():
        """A blank trailing column (odd employee count). ``c5doplnUdaj`` is a
        mandatory 0/1 flag; every other element is an optional type emitted as
        an empty string (an explicit "" so QWeb keeps the element — a ``None``
        value would drop it)."""
        keys = ("rodne_cislo", "priezvisko", "meno", "ulica", "psc", "obec",
                "stat", "r3a", "r4a", "r6", "r8suma")
        col = {k: "" for k in keys}
        col["empty"] = True
        col["dopln_udaj"] = "0"
        return col

    def _build_annex_pages(self):
        """Return ``(pages, employee_count)`` where each page is
        ``{'aktualna', 'celkovo', 'col1', 'col2'}`` holding two annex columns."""
        self.ensure_one()
        columns = [
            self._build_annex_column(line)
            for line in self._sheet_lines().sorted("sequence")
        ]
        emp_count = len(columns)
        # pad to an even number so every page has both columns
        if emp_count % 2:
            columns.append(self._empty_annex_column())
        total_pages = len(columns) // 2
        pages = []
        for idx in range(total_pages):
            pages.append({
                "aktualna": str(idx + 1),
                "celkovo": str(total_pages),
                "col1": columns[2 * idx],
                "col2": columns[2 * idx + 1],
            })
        return pages, emp_count
