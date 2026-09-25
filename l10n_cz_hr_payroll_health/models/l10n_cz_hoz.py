# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""CZ HOZ — Hromadné oznámení zaměstnavatele (bulk employee notification).

Event-driven HEALTH-insurer filing (ns
``http://xmlns.vzp.cz/hromadneOznameniZamestnavatele/v1``, root
``hromadneOznameniZamestnavatele``) reporting employee enrol / terminate changes
within 8 days. It is a BATCH of per-employee change events (``zmenaZamestance``).
The data source is the EMPLOYEE + ``hr.version`` lifecycle (hire / termination
dates, birth number, name, private address) — NOT payslip totals — so this model
overrides the base payslip pipeline and builds the events directly.

Change-event mapping (per ``<zmenaZamestance>``):

* ``kodzmeny``       ← ``P`` nástup (enrol) / ``O`` ukončení (terminate), from
  the sheet ``event_type`` (the two common cases; the XSD allows many more).
* ``datumZmeny``     ← contract start (enrol) or contract end (terminate), or an
  explicit override date on the sheet.
* ``cisloPojistence``← the employee's birth number (rodné číslo) from
  ``identification_id`` (9-10 digits).
* ``jmeno`` / ``prijmeni`` ← first / last name (Czech "Jméno Příjmení" order).
* ``adresa`` (optional) ← the employee's private street / city / ZIP.

Human-verify / assumptions (see README): the ``P`` / ``O`` codes cover the
standard resident-employee enrol/terminate; the many special ``kodZmenyTyp``
codes (EU/third-country first enrolment A/E/C/Q, state-payer facts, corrections)
are out of scope. The name split assumes "First Last"; foreign-insured employees
without a rodné číslo (``M``/``Z`` + date-of-birth identifier) are not derived
automatically.
"""
from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .l10n_cz_health_common import (
    CZ_HEALTH_INSURERS,
    digits_only,
    health_employer_identification,
    health_payer_number,
)

# HOZ kodZmeny — the two common employment-lifecycle events.
CODE_ENROLL = "P"      # nástup do zaměstnání
CODE_TERMINATE = "O"   # ukončení zaměstnání


class L10nCzHoz(models.Model):
    _name = "l10n.cz.hoz"
    _inherit = ["cssk.payroll.declaration.mixin", "mail.thread",
                "mail.activity.mixin"]
    _description = "Czech HOZ — Bulk Employer Notification"
    _order = "id desc"

    _report_code = "cz_hoz"
    _country_code = "CZ"
    _xml_name_fallback = "hoz"

    insurer_code = fields.Selection(
        selection=CZ_HEALTH_INSURERS, string="Health insurer",
        required=True, tracking=True,
        default=lambda self: self.env.company.l10n_cz_health_insurer_code,
        help="Health insurer this notification is filed to. Only employees "
        "assigned to this insurer are reported.")
    event_type = fields.Selection(
        [("enroll", "Enrol (P)"),
         ("terminate", "Terminate (O)")],
        required=True, default="enroll", tracking=True,
        help="Change code applied to every employee in this notification.")
    event_date = fields.Date(
        help="Override date of change (datumZmeny). If empty, the contract "
        "start (enrol) or contract end (terminate) date is used per employee.")
    employee_ids = fields.Many2many(
        "hr.employee", string="Employees",
        help="Employees whose enrol/terminate change is being notified.")

    # ------------------------------------------------------------------
    @api.depends("event_type", "year", "month", "company_id", "insurer_code")
    def _compute_name(self):
        for rec in self:
            rec.name = "HOZ %s %s/%s (%s)" % (
                rec.event_type or "", rec.month or "", rec.year or "",
                rec.insurer_code or "")

    # ------------------------------------------------------------------
    # HOZ is lifecycle-driven (no payslip), so it overrides the base pipeline.
    # ------------------------------------------------------------------
    def action_generate(self):
        self.ensure_one()
        self._ensure_not_submitted()
        if self.state != "draft":
            raise UserError(_(
                "Reset the notification to draft before regenerating it."))
        if not self.version_id:
            raise UserError(_(
                "No HOZ version is configured. Check the shipped version "
                "data."))
        if not self.employee_ids:
            raise UserError(_("Select at least one employee to notify."))
        self._preflight()
        data = {"aggregate": {}, "per_employee": {}}
        xml_bytes = self._render_xml(data)
        self._validate_against_schema(xml_bytes)
        self._attach_xml(xml_bytes)
        self.state = "generated"
        self.message_post(body=_("HOZ generated and XSD-validated."))
        return True

    def _preflight(self):
        super()._preflight()
        for rec in self:
            company = rec.company_id
            if not rec.insurer_code:
                raise UserError(_(
                    "Select the health insurer for this HOZ notification."))
            if not health_payer_number(company):
                raise UserError(_(
                    "Company '%(company)s' needs a health payer number "
                    "(identifikacniCisloPlatce). Set the company IČ or the "
                    "'Health payer number' field.",
                    company=company.display_name))
            if not (company.city and company.zip):
                raise UserError(_(
                    "Company '%(company)s' needs a city and ZIP for the HOZ "
                    "employer address.", company=company.display_name))
        return True

    # ------------------------------------------------------------------
    def _build_hoz_change(self, employee, code):
        self.ensure_one()
        bno = digits_only(employee.identification_id)
        if len(bno) not in (9, 10):
            raise UserError(_(
                "Employee '%(name)s' needs a 9- or 10-digit birth number "
                "in Identification No. for the HOZ "
                "cisloPojistence.", name=employee.display_name))
        version = employee.version_id
        if self.event_date:
            change_date = self.event_date
        elif code == CODE_ENROLL:
            change_date = version.contract_date_start
        else:
            change_date = version.contract_date_end
        if not change_date:
            raise UserError(_(
                "Employee '%(name)s' needs a contract %(kind)s date (or set "
                "the override date of change) for the HOZ datumZmeny.",
                name=employee.display_name,
                kind=_("start") if code == CODE_ENROLL else _("end")))
        first, _sep, surname = (employee.name or "").rpartition(" ")
        surname = surname or employee.name or "-"
        first = first or "-"
        change = {
            "kodzmeny": code,
            "datumZmeny": change_date.isoformat(),
            "cisloPojistence": bno,
            "jmeno": first[:60],
            "prijmeni": surname[:60],
        }
        adresa = {}
        if employee.private_street:
            adresa["ulice"] = employee.private_street.strip()[:60]
        if employee.private_city:
            adresa["obec"] = employee.private_city.strip()[:60]
        psc = digits_only(employee.private_zip)
        if len(psc) == 5:
            adresa["psc"] = psc
        if adresa:
            change["adresa"] = adresa
        return change

    def _build_hoz_changes(self):
        self.ensure_one()
        code = CODE_ENROLL if self.event_type == "enroll" else CODE_TERMINATE
        return [self._build_hoz_change(emp, code)
                for emp in self.employee_ids]

    def _declaration_render_context(self, data):
        self.ensure_one()
        return {
            "insurer_code": self.insurer_code,
            "employer": health_employer_identification(self.company_id),
            "hoz_changes": self._build_hoz_changes(),
        }
