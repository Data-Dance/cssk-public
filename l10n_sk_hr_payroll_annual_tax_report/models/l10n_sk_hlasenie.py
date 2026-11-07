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
whole calendar YEAR *and* carries a per-employee annexes (Časť IV/V — one row
per employee with the year's income, withheld advance and daňový bonus). The
per-employee rows are ``cssk.payroll.employee.declaration`` records, exactly as
in the MVP annex pattern.

The XML matches the official schema ``data/rh2023.xsd`` (root ``dokument``, no
target namespace, ``elementFormDefault="qualified"``). Each annex section is paginated two
employees per page (``cast5`` → ``c5stlpec1`` + ``c5stlpec2``); an odd trailing
column is emitted empty (every annex element is an optional type).
"""
import calendar as _calendar
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_cssk_core.tools import split_street, split_street_text
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

    # ------------------------------------------------------------------
    # Render context
    # ------------------------------------------------------------------
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
        # III. časť — rekapitulácia daňového bonusu § 33. The poučenie: r. A
        # is the whole bonus paid (from the advances AND the employer's own
        # money), r. B the part paid out of the withheld advances, and
        # "Riadok C = Riadok A – Riadok B". r. 5 is capped at r. 4, so the
        # bonus beyond the advances only ever showed up here — and these
        # three rows used to be emitted empty, so it was reported nowhere.
        r_a = bonus
        r_b = r05
        r_c = round(r_a - r_b, 2)

        pages4, pages5, count4, count5 = self._build_annex_sections()
        today = fields.Date.context_today(self)
        # The house number is split off the street (l10n_cssk_core), never
        # Street 2 — a building, a floor or a c/o line.
        ulica, cislo = split_street(company)

        header = {
            "dic": self._company_dic(company),
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
            "vypracoval": (user.name or "Odoo Payroll")[:255],
            "datum": today.strftime("%d.%m.%Y"),
            "datum_zuctovania": max((col['completed_on'] for page in pages5
                for col in (page['col1'], page['col2']) if col.get('completed_on')),
                key=lambda value: tuple(reversed(value.split('.'))), default=''),
            # independent counts for the two statutory employee groups
            "pocet_stran_c4": str(len(pages4)),
            "pocet_zam_c4": str(count4),
            "pocet_stran_c5": str(len(pages5)),
            "pocet_zam_c5": str(count5),
        }
        body = {
            # I. časť — vyúčtovanie preddavkov na daň (aggregate)
            "r00": "%.2f" % r00,
            "r01": "%.2f" % r01,
            "r04": "%.2f" % r04,
            "r05": "%.2f" % r05,
            "r06": "%.2f" % premium,
            # III. časť — rekapitulácia daňového bonusu § 33
            "rA": "%.2f" % r_a,
            "rB": "%.2f" % r_b,
            "rC": "%.2f" % r_c,
            # bank IBAN for the žiadosť o vrátenie preplatku
            "iban": self._company_iban(company),
        }
        return {"h": header, "b": body, "pages": pages5, "pages4": pages4}

    def _company_iban(self, company):
        banks = company.partner_id.bank_ids
        if banks:
            return (banks[0].acc_number or "").replace(" ", "")[:34]
        return ""

    # ------------------------------------------------------------------
    # Per-employee annexes (Časť IV/V) — two employees per page/column pair.
    # ------------------------------------------------------------------
    def _annex_identity(self, employee):
        rc = self._digits(employee.identification_id)
        if not (9 <= len(rc) <= 10):
            raise UserError(_(
                "Employee '%(name)s' needs a 9-10 digit Slovak birth number "
                "for the annual tax annex.", name=employee.display_name))
        first, last = self._split_person_name(employee)
        street, number = split_street_text(
            getattr(employee, 'private_street', '') or '',
            getattr(employee, 'private_street2', '') or '')
        country = getattr(employee, 'private_country_id', False)
        if country and country.code != 'SK':
            raise UserError(_('Review foreign residence and identification before exporting this employee.'))
        return {'empty': False, 'rodne_cislo': rc, 'meno': first[:24],
                'priezvisko': last[:36], 'ulica': street[:255], 'cislo': number[:20],
                'psc': self._digits(getattr(employee, 'private_zip', '') or '')[:5],
                'obec': (getattr(employee, 'private_city', '') or '')[:255],
                'stat': 'Slovensko', 'kod_statu': '703'}

    def _annual_settlement_column(self, line):
        """Engine bridge hook: reviewed Part V values, or None for Part IV.

        A computed RZD is not equivalent to a payment. An installed engine
        must supply its own reviewed annual values rather than map monthly
        tax to Part V's insurance fields. Fail on known RZD without a bridge.
        """
        if 'l10n.sk.tax.reconciliation' in self.env:
            rec = self.env['l10n.sk.tax.reconciliation'].search([
                ('company_id', '=', self.company_id.id),
                ('employee_id', '=', line.employee_id.id),
                ('year', '=', int(self.year)), ('state', 'in', ['computed', 'posted'])], limit=1)
            if rec:
                raise UserError(_('An annual settlement exists. Install its reviewed Hlásenie Part V bridge before exporting.'))
        return None

    def _build_part4_column(self, line):
        col = self._annex_identity(line.employee_id)
        totals = line.values_json or {}
        # The declaration adapter is the source of both the selected payroll
        # and its historical versions; never use today's employee contract.
        slips = self._get_period_payslips().filtered(lambda slip: slip.employee_id == line.employee_id)
        months = set()
        for slip in slips:
            start, end = max(slip.date_from, self.date_from), min(slip.date_to, self.date_to)
            if start <= end:
                months.update(range(start.month, end.month + 1))
        nczd = any(getattr(self._payslip_version(slip), 'l10n_sk_tax_declaration_signed', False)
                   for slip in slips)
        bonus = abs(round(totals.get(BONUS_CODE, 0.0), 2))
        if bonus:
            raise UserError(_('Child bonus requires reviewed child identities and entitlement months in the annual annex.'))
        health = sum_concept(totals, 'HEALTH_EE') + sum_concept(totals, 'HEALTH_TOPUP')
        # Like MVP, remove health from the misleadingly named payroll total:
        # SOCIALEMPLOYEETOTAL includes BOTH employee social and health.
        social = sum_concept(totals, 'SOCIAL_EE_TOTAL') - health
        col.update({'r3a': '%.2f' % abs(totals.get('GROSS', 0)),
                    'r5a': '%.2f' % abs(social), 'r5b': '%.2f' % abs(health),
                    'r6': '%.2f' % self._tax_advance_total(totals),
                    'r7suma': '0.00', 'r7deti': '0', 'r8ano': '1' if nczd else '0',
                    'months': {str(n): '1' if (len(months) == 12 if n == 0 else n in months and len(months) != 12)
                               else '0' for n in range(13)}})
        return col

    @staticmethod
    def _empty_annex_column():
        return {'empty': True, 'dopln_udaj': '0', 'r8ano': '0',
                'months': {str(n): '0' for n in range(13)}}

    def _paginate_annex(self, columns):
        count = len(columns)
        columns = list(columns)
        if count % 2:
            columns.append(self._empty_annex_column())
        pages = [{'aktualna': str(n + 1), 'celkovo': str(len(columns) // 2),
                  'col1': columns[2 * n], 'col2': columns[2 * n + 1]}
                 for n in range(len(columns) // 2)]
        return pages, count

    def _build_annex_sections(self):
        self.ensure_one()
        part4, part5 = [], []
        for line in self._sheet_lines().sorted('sequence'):
            annual = self._annual_settlement_column(line)
            if annual is None:
                part4.append(self._build_part4_column(line))
            else:
                identity = self._annex_identity(line.employee_id)
                identity.update(annual)
                part5.append(identity)
        pages4, count4 = self._paginate_annex(part4)
        pages5, count5 = self._paginate_annex(part5)
        return pages4, pages5, count4, count5

    def _build_annex_pages(self):
        """Compatibility hook for consumers that specifically ask for Part V."""
        _pages4, pages5, _count4, count5 = self._build_annex_sections()
        return pages5, count5
