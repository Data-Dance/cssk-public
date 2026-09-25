# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""CZ ONZ — Oznámení o nástupu do zaměstnání (employment registration).

Event-driven ČSSZ filing (ns ``http://schemas.cssz.cz/ONZ2022``, root ``<ONZ>``)
notifying the start/end of an employment within 8 days. It is a BATCH of
per-employee registration events (akce nástup / skončení). The data source is
the EMPLOYEE + hr.version lifecycle (hire / termination dates, birth number,
name, address) — NOT payslip totals — so this model overrides the base payslip
pipeline and builds the events directly.

Field mapping (per ``<employee>``):

* ``@act`` (akce) ← ``1`` nástup / ``2`` skončení (the header ``event_type``).
* ``@dep`` (kód okresu) ← company OSSZ code; ``@dat`` ← today (fill date).
* ``client/name`` ← employee first / last name; ``client/birth`` ← birthday +
  birth surname; ``client/@bno`` ← birth number (Identification No.);
  ``client/fdr`` ← employee private CZ address.
* ``comp`` ← employer ČSSZ variable symbol / IČ / name.
* ``job/@fro`` ← contract start; ``job/@to`` ← contract end (skončení only);
  ``job/@rel`` ← 1 (standard employment).

Human-verify / assumptions (see README): the akce codes (1/2) and the activity
kind (``job/@rel`` = 1) are the common cases only; birth surname is approximated
by the current surname; a missing house number is split off the street string.
"""
from odoo import _, api, fields, models
from odoo.exceptions import UserError

# ONZ akce (C_AKCE) — the two common employment-lifecycle events.
ACT_NASTUP = "1"      # přihláška — start of employment
ACT_SKONCENI = "2"    # odhláška — end of employment


class L10nCzOnz(models.Model):
    _name = "l10n.cz.onz"
    _inherit = ["cssk.payroll.declaration.mixin", "mail.thread",
                "mail.activity.mixin"]
    _description = "Czech ONZ — Employment Registration"
    _order = "id desc"

    _report_code = "cz_onz"
    _country_code = "CZ"
    _xml_name_fallback = "onz"

    event_type = fields.Selection(
        [("nastup", "Start of employment"),
         ("skonceni", "End of employment")],
        required=True, default="nastup", tracking=True,
        help="ONZ event type applied to every employee in this filing.")
    employee_ids = fields.Many2many(
        "hr.employee", string="Employees",
        help="Employees whose employment start/end is being registered.")

    # ------------------------------------------------------------------
    @api.depends("event_type", "year", "company_id")
    def _compute_name(self):
        for rec in self:
            rec.name = "ONZ %s %s" % (
                (rec.event_type or ""),
                (rec.date_from and rec.date_from.year) or rec.year or "")

    # ------------------------------------------------------------------
    # ONZ is event-driven (employee lifecycle), NOT payslip-derived, so it
    # overrides the base generate pipeline instead of aggregating payslips.
    # ------------------------------------------------------------------
    def action_generate(self):
        self.ensure_one()
        self._ensure_not_submitted()
        if self.state != "draft":
            raise UserError(_(
                "Reset the declaration to draft before regenerating it."))
        if not self.version_id:
            raise UserError(_(
                "No ONZ version is configured. Check the shipped version "
                "data."))
        if not self.employee_ids:
            raise UserError(_("Select at least one employee to register."))
        self._preflight()
        data = {"aggregate": {}, "per_employee": {}}
        xml_bytes = self._render_xml(data)
        self._validate_against_schema(xml_bytes)
        self._attach_xml(xml_bytes)
        self.state = "generated"
        self.message_post(body=_("ONZ generated and XSD-validated."))
        return True

    def _preflight(self):
        super()._preflight()
        for rec in self:
            company = rec.company_id
            vs = rec._digits(company.l10n_cz_ossz_vs)
            if not (8 <= len(vs) <= 10):
                raise UserError(_(
                    "Company '%(company)s' needs an 8-10 digit ČSSZ variable "
                    "symbol for the ONZ <comp vs>. Set 'ČSSZ variable symbol "
                    "(VS)' on the company.", company=company.display_name))
            code = (company.l10n_cz_ossz_code or "").strip()
            if not (code.isdigit() and 100 <= int(code) <= 999):
                raise UserError(_(
                    "Company '%(company)s' needs a valid OSSZ code (100-999) "
                    "for the ONZ <employee dep>.",
                    company=company.display_name))
        return True

    # ------------------------------------------------------------------
    @staticmethod
    def _digits(value):
        return "".join(ch for ch in (value or "") if ch.isdigit())

    def _employee_cz_address(self, employee):
        street = (employee.private_street or "").strip()
        num = ""
        parts = street.rsplit(" ", 1)
        if len(parts) == 2 and any(c.isdigit() for c in parts[1]):
            street, num = parts[0], parts[1]
        city = (employee.private_city or "").strip()
        zip5 = self._digits(employee.private_zip)[:5].rjust(5, "0")
        fdr = {
            "num": (num or "0")[:12],
            "pnu": zip5,
            "cit": (city or "-")[:50],
            "pos": (city or "-")[:5],
        }
        if street:
            fdr["str"] = street[:50]
        return fdr

    def _build_onz_employees(self):
        self.ensure_one()
        company = self.company_id
        vs = self._digits(company.l10n_cz_ossz_vs)
        ossz = (company.l10n_cz_ossz_code or "").strip()
        today = fields.Date.context_today(self).isoformat()
        act = ACT_NASTUP if self.event_type == "nastup" else ACT_SKONCENI
        out = []
        sqnr = 0
        for emp in self.employee_ids:
            sqnr += 1
            if not emp.birthday:
                raise UserError(_(
                    "Employee '%(name)s' needs a birthday for the ONZ "
                    "<birth dat>.", name=emp.display_name))
            version = emp.version_id
            start = version.contract_date_start
            end = version.contract_date_end
            if act == ACT_NASTUP and not start:
                raise UserError(_(
                    "Employee '%(name)s' needs a contract start date for the "
                    "ONZ start-of-employment event.", name=emp.display_name))
            if act == ACT_SKONCENI and not end:
                raise UserError(_(
                    "Employee '%(name)s' needs a contract end date for the "
                    "ONZ end-of-employment event.", name=emp.display_name))
            surname, _sep, first = (emp.name or "").rpartition(" ")
            surname = surname or emp.name or "-"
            first = first or "-"
            bno = self._digits(emp.identification_id)

            employee_attrs = {
                "sqnr": str(sqnr),
                "dep": ossz,
                "act": act,
                "dat": today,
            }
            client_attrs = {}
            if 9 <= len(bno) <= 10:
                client_attrs["bno"] = bno
            name_attrs = {"sur": surname[:50], "fir": first[:50]}
            birth_attrs = {
                "dat": emp.birthday.isoformat(),
                "nam": surname[:50],
            }
            if emp.place_of_birth:
                birth_attrs["cit"] = emp.place_of_birth[:50]
            comp_attrs = {
                "vs": vs,
                "nam": (company.name or "")[:144],
            }
            comp_id = self._digits(company.company_registry)
            if comp_id:
                comp_attrs["id"] = comp_id[:35]
            job_attrs = {
                "fro": (start or end).isoformat(),
                "rel": "1",
                "per": (company.country_id.code or "CZ")[:2],
            }
            if act == ACT_SKONCENI and end:
                job_attrs["to"] = end.isoformat()
            out.append({
                "employee": employee_attrs,
                "client": client_attrs,
                "name": name_attrs,
                "birth": birth_attrs,
                "fdr": self._employee_cz_address(emp),
                "comp": comp_attrs,
                "job": job_attrs,
            })
        return out

    def _declaration_render_context(self, data):
        self.ensure_one()
        return {
            "onz_version": "1.2",
            "onz_employees": self._build_onz_employees(),
        }
