# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""CZ PPPZ — Přehled o platbě pojistného zaměstnavatele.

Monthly employer HEALTH-premium overview filed to each health insurer (ns
``http://xmlns.vzp.cz/PrehledPlatbyZamestnavatele/v1``, root
``prehledPlatbyZamestnavatele``). Employer-AGGREGATE, NO personal data: the
number of insured employees, the sum of their health assessment bases and the
total premium.

Rule-code mapping (from ``l10n_cz_hr_payroll_ee`` / ``l10n_cz_hr_payroll_oca``):

* ``pocetZamestnancu``         ← count of employees (of the target insurer) with
  a non-zero health premium for the period.
* ``soucetPojistneho``         ← Σ (|``HEALTHEE``| + ``HEALTHER``) — the employee
  4.5 % withholding plus the employer 9 % premium, i.e. the full 13.5 % health
  premium, rounded to whole crowns (nonNegativeInteger).
* ``soucetZakladuPojistneho``  ← the health assessment base = premium / 0.135.
  Deriving the base from the *premium* (rather than from gross) is what makes the
  minimum-assessment-base top-up come out right: when gross < minimum, the
  employee bears the 13.5 % shortfall in ``HEALTHEE``, so |HEALTHEE|+HEALTHER
  equals 13.5 % of the true (minimum) base and the division recovers it.

Per-insurer filing
------------------
CZ health uses ONE common XML format but is filed PER insurer through that
insurer's own channel. Each employee belongs to one insurer
(``hr.employee.l10n_cz_health_insurer_code`` or the company default); a PPPZ
sheet targets one ``insurer_code`` and aggregates only that insurer's employees.
Generate one sheet per insurer the company employs.
"""
from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .l10n_cz_health_common import (
    CZ_HEALTH_INSURERS,
    health_employer_identification,
    health_payer_number,
)

# Total statutory CZ health-insurance rate (employee 4.5 % + employer 9 %).
HEALTH_TOTAL_RATE = 0.135


class L10nCzPppz(models.Model):
    _name = "l10n.cz.pppz"
    _inherit = ["cssk.payroll.declaration.mixin", "mail.thread",
                "mail.activity.mixin"]
    _description = "Czech PPPZ — Employer Health Premium Overview"
    _order = "date_from desc, id desc"

    _report_code = "cz_pppz"
    _country_code = "CZ"
    _xml_name_fallback = "pppz"

    insurer_code = fields.Selection(
        selection=CZ_HEALTH_INSURERS, string="Health insurer",
        required=True, tracking=True,
        default=lambda self: self.env.company.l10n_cz_health_insurer_code,
        help="Health insurer this overview is filed to. Only employees "
        "assigned to this insurer are aggregated.")
    # This form already had its own radny/opravny selection and did emit it as
    # <typPrehledu>. It is now driven by the shared correction_type instead, so
    # that "is this an amendment?" means one thing across all twelve forms and
    # the guard against amending a period never filed applies here too.
    # The zdravotní pojišťovny accept a corrective overview but no dodatečný
    # or storno, so only those two are offered.
    _supported_correction_types = ("regular", "corrective")

    @api.depends("year", "month", "company_id", "insurer_code")
    def _compute_name(self):
        for rec in self:
            rec.name = "PPPZ %s/%s (%s)" % (
                rec.month or "", rec.year or "", rec.insurer_code or "")

    # ------------------------------------------------------------------
    # Per-insurer payslip scope
    # ------------------------------------------------------------------
    def _get_period_payslips(self):
        """Restrict the period's payslips to employees of the target
        insurer (own insurer, or the company default when unset)."""
        payslips = super()._get_period_payslips()
        if not payslips:
            return payslips
        return payslips.filtered(
            lambda s: s.employee_id._l10n_cz_effective_health_insurer()
            == self.insurer_code)

    # ------------------------------------------------------------------
    def _preflight(self):
        super()._preflight()
        for rec in self:
            company = rec.company_id
            if not rec.insurer_code:
                raise UserError(_(
                    "Select the health insurer for this PPPZ overview."))
            if not health_payer_number(company):
                raise UserError(_(
                    "Company '%(company)s' needs a health payer number "
                    "(identifikacniCisloPlatce). Set the company IČ or the "
                    "'Health payer number' field.",
                    company=company.display_name))
            if not (company.city and company.zip):
                raise UserError(_(
                    "Company '%(company)s' needs a city and ZIP for the PPPZ "
                    "employer address.", company=company.display_name))
        return True

    # ------------------------------------------------------------------
    def _health_totals(self, data):
        """Return (insured_count, base_sum, premium_sum) from the collected
        per-employee totals — only employees with a non-zero health premium
        are counted as insured."""
        count = 0
        premium_sum = 0.0
        for bucket in data["per_employee"].values():
            totals = bucket["totals"]
            premium = abs(totals.get("HEALTHEE", 0.0)) + \
                abs(totals.get("HEALTHER", 0.0))
            if round(premium, 2) <= 0.0:
                continue
            count += 1
            premium_sum += premium
        base_sum = premium_sum / HEALTH_TOTAL_RATE if premium_sum else 0.0
        return count, round(base_sum, 2), round(premium_sum)

    def _declaration_render_context(self, data):
        self.ensure_one()
        count, base_sum, premium_sum = self._health_totals(data)
        if count <= 0:
            raise UserError(_(
                "No insured employees with a health premium were found for "
                "insurer %(code)s in %(month)s/%(year)s.",
                code=self.insurer_code, month=self.month, year=self.year))
        return {
            "insurer_code": self.insurer_code,
            # The wire spelling stays Czech; the concept is shared.
            "report_type": "opravny" if self.is_correction else "radny",
            "employer": health_employer_identification(self.company_id),
            "mesic": str(int(self.month)),
            "rok": str(int(self.year)),
            "pocet_zamestnancu": str(count),
            "soucet_zakladu": "%.2f" % base_sum,
            "soucet_pojistneho": str(int(premium_sum)),
        }
