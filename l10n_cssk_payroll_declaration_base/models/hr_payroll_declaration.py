# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Engine-neutral payroll declaration base.

This module ships the reusable machinery for the CZ/SK monthly payroll
e-submissions (social insurance overviews) WITHOUT binding to a specific
payroll engine:

* ``cssk.payroll.declaration.mixin`` — the declaration "sheet": period
  fields, a ``draft → generated → submitted`` state machine, the XSD-validated
  XML export pipeline, and — crucially — the *payslip adapter*
  (``_collect_payslip_totals``) that reads salary-line totals through the
  common ``hr.payslip`` read API shared by BOTH the ``payroll`` engine and
  the ``hr_payroll`` engine.
* ``cssk.payroll.employee.declaration`` — one row per employee per sheet (the
  per-employee annex source), holding that employee's rule-code totals.
* ``cssk.payroll.declaration.version`` — the form vintage: the QWeb template,
  the root element and the shipped XSD (loaded from ``data/`` so relative
  ``xs:import`` schemaLocations resolve). A new form vintage is a data change.

Engine neutrality
-----------------
The base depends ONLY on ``hr`` + ``mail`` (never ``payroll`` / ``hr_payroll``).
All payslip access goes through ``self.env['hr.payslip']`` resolved at RUNTIME
(guarded by ``'hr.payslip' in self.env``), reading only the common subset both
engines expose: ``line_ids`` → ``.code`` / ``.total``, ``employee_id``,
``company_id``, ``date_from`` / ``date_to``, ``state``. It does NOT call
``get_salary_line_total`` (present on the ``payroll`` engine, absent on the EE engine) and stores no relational
field that hard-binds to one engine's payslip table.

Field / method names deliberately mirror Odoo master's
``hr.payroll.declaration.mixin`` / ``hr.payroll.employee.declaration`` (``year``,
``line_ids``, ``lines_count``, ``_country_restriction``, ``_get_rendering_data``,
``action_generate_declarations`` …) so a future master (hr_payroll) port is a superclass
swap rather than a rewrite. Distinct ``_name``s (``cssk.payroll.*``) avoid a
model collision when the ``hr_payroll`` models are present in the same DB.
"""
import base64
import calendar as _calendar
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta

from lxml import etree

from markupsafe import Markup

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import file_path

_logger = logging.getLogger(__name__)


class CSSKPayrollDeclarationVersion(models.Model):
    """A versioned declaration template (mirrors ``cssk.vat.return.version``).

    Carries, as DATA, everything form-vintage specific: the QWeb template, the
    expected XML root element and the official XSD (module + relative filename,
    so ``etree.parse`` resolves any ``xs:import`` against the on-disk ``data/``
    directory). New form year = new version record + new XSD file, no code.
    """

    _name = "cssk.payroll.declaration.version"
    _description = "Payroll Declaration Version"
    _order = "country_id, code, valid_from desc"

    name = fields.Char(required=True)
    code = fields.Char(
        required=True,
        help="Report code shared with the declaration model, e.g. "
        "'cz_pvpoj' / 'sk_mvp'. Selects the version for a report.")
    country_id = fields.Many2one("res.country", required=True)
    active = fields.Boolean(default=True)
    valid_from = fields.Date(required=True)
    valid_to = fields.Date()

    xml_template_ref_id = fields.Many2one(
        "ir.ui.view", string="XML template", required=True,
        domain="[('type', '=', 'qweb')]",
        help="QWeb template (ir.ui.view) that renders this version's XML.")
    xml_root_element = fields.Char(
        required=True, help="Expected root element, e.g. 'pvpoj' / 'mvpp'.")
    xml_schema_module = fields.Char(
        help="Technical name of the module shipping the XSD in its data/ "
        "directory (so relative xs:import schemaLocations resolve on disk).")
    xml_schema_filename = fields.Char(
        help="XSD path relative to xml_schema_module, e.g. "
        "'data/PVPOJ25.xsd'.")
    xml_schema_data = fields.Binary(
        attachment=True,
        help="Optional copy of the XSD for download/reference; validation "
        "loads xml_schema_filename from disk to resolve imports.")


class CSSKPayrollEmployeeDeclaration(models.Model):
    """One row per employee per declaration sheet (per-employee annex source).

    Field/method names mirror master's ``hr.payroll.employee.declaration``
    (``res_model``, ``res_id``, ``employee_id``, ``company_id``, ``state``); the
    payroll figures are stashed in ``values_json`` (``{rule_code: total}``) plus
    a few pre-resolved annex helpers so the QWeb template stays declarative.
    """

    _name = "cssk.payroll.employee.declaration"
    _description = "Payroll Employee Declaration"
    _order = "res_model, res_id, sequence, id"
    _rec_name = "employee_id"

    res_model = fields.Char("Declaration Model Name", required=True, index=True)
    res_id = fields.Many2oneReference(
        "Declaration Model Id", index=True, model_field="res_model",
        required=True)
    sequence = fields.Integer(default=10)
    employee_id = fields.Many2one("hr.employee", required=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company)
    values_json = fields.Json(
        help="Per-employee salary-rule totals for the period, {code: total}.")
    insured_days = fields.Integer(
        help="Calendar days the employer owes insurance for (annex pocDni).")
    worked_hours = fields.Float(
        help="Hours from the employee's payslips for the period (annex "
        "pocetHodin).")
    vz_base = fields.Float(
        help="Assessment base for the period, taken from GROSS.")
    state = fields.Selection(
        [("draft", "Draft"), ("generated", "Generated")],
        default="draft")

    _unique_employee_sheet = models.Constraint(
        "unique(employee_id, res_model, res_id)",
        "An employee can only have one declaration per sheet.")

    def total(self, code):
        """Per-employee total for ``code`` (0.0 if absent)."""
        self.ensure_one()
        return (self.values_json or {}).get(code, 0.0)


# Every Czech and Slovak payroll authority accepts amendments to a filing it
# has already received, and every one of them spells it differently — riadny /
# řádný, opravný, dodatočný / dodatečný, storno. The CONCEPTS are the same four
# everywhere, so they are named once here and the wire spelling is left to each
# form's template.
#
#   regular       the ordinary filing for the period
#   corrective    REPLACES a filing already sent (the authority keeps the last)
#   supplementary ADDS to it, leaving the original standing
#   cancellation  withdraws a filing that should never have been sent
#
# Not every authority accepts all four. A form declares what it supports in
# ``_supported_correction_types`` and the selection narrows to that, so a user
# cannot pick a type the receiving system will reject.
CORRECTION_TYPES = [
    ("regular", "Regular"),
    ("corrective", "Corrective"),
    ("supplementary", "Supplementary"),
    ("cancellation", "Cancellation"),
]

# Anything other than a plain regular filing amends something already sent.
AMENDING_CORRECTION_TYPES = ("corrective", "supplementary", "cancellation")

# Payslip states that mean "this payroll was run", per engine. A declaration
# reports payroll that happened; a draft payslip is a calculation somebody may
# still change or delete, and counting it filed figures nobody had paid.
#   OCA ``payroll``:          draft / verify (waiting) / done / cancel
#   Enterprise ``hr_payroll``: draft / validated / paid / cancel
CONFIRMED_PAYSLIP_STATES = {
    "oca": ("done",),
    "ee": ("validated", "paid"),
}


class CSSKPayrollDeclarationMixin(models.AbstractModel):
    """Engine-neutral declaration sheet (the reusable base for each report).

    Concrete country reports inherit this + ``mail.thread`` and set:
    ``_report_code`` (selects the version), ``_country_code`` (restriction),
    and provide the QWeb template referenced by their version record. They may
    override ``_declaration_render_context`` to add template variables and
    ``_preflight`` to add master-data checks.
    """

    _name = "cssk.payroll.declaration.mixin"
    _description = "Payroll Declaration Mixin"
    # Delivery tracking for every payroll declaration at once: thirteen concrete
    # reports inherit this mixin, so wiring it here rather than module by module
    # is both less work and impossible to do inconsistently. Retention already
    # lives below (submitted_attachment_id / filed_history_ids); this adds the
    # other half — whether it arrived, and what the authority sent back.
    _inherit = ["cssk.submittable.mixin"]

    # Overridden by concrete reports.
    _report_code = False
    _country_code = False
    _xml_name_fallback = "declaration"

    # ------------------------------------------------------------------
    # Fields (master-compatible names)
    # ------------------------------------------------------------------
    def _get_year_selection(self):
        current_year = datetime.now().year
        return [(str(i), str(i)) for i in range(2020, current_year + 2)]

    name = fields.Char(compute="_compute_name")
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company)
    country_id = fields.Many2one(
        related="company_id.country_id", store=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    year = fields.Selection(
        selection="_get_year_selection", required=True,
        default=lambda self: str(datetime.now().year))
    month = fields.Selection(
        [(str(i), "%02d" % i) for i in range(1, 13)],
        required=True, default=lambda self: str(datetime.now().month))
    date_from = fields.Date(compute="_compute_period", store=True)
    date_to = fields.Date(compute="_compute_period", store=True)
    payment_date = fields.Date(
        help="Payday reported to the authority (SK denVyplaty). Defaults to "
        "the period end.")
    # Not required: the default is chosen from TODAY, before the user has
    # picked the period, and today may lie after a form was discontinued
    # while the period lies before. Generate resolves the vintage from the
    # period (``_ensure_period_version``) and refuses when none applies.
    version_id = fields.Many2one(
        "cssk.payroll.declaration.version",
        default=lambda self: self._default_version_id(),
        domain="[('country_id', '=', country_id), ('code', '=', report_code)]")
    # Technical: lets the version picker offer only THIS form's vintages.
    # Every form shares one version table, so filtering on the country alone
    # offered the PVPOJ vintage on an ELDP.
    report_code = fields.Char(compute="_compute_report_code")
    line_ids = fields.One2many(
        "cssk.payroll.employee.declaration", "res_id",
        string="Employee declarations")
    lines_count = fields.Integer(
        compute="_compute_lines_count", string="Employees")
    state = fields.Selection(
        [("draft", "Draft"), ("generated", "Generated"),
         ("submitted", "Submitted")],
        default="draft", tracking=True)
    xml_attachment_id = fields.Many2one("ir.attachment", readonly=True)

    def _submission_ready_states(self):
        """`generated` is this vocabulary's `exported` — the XML exists."""
        return ("generated", "submitted")

    # --- Corrections ---------------------------------------------------
    correction_type = fields.Selection(
        selection="_selection_correction_type",
        default="regular", required=True, tracking=True,
        help="Whether this is the ordinary filing for the period or an "
        "amendment to one already sent. The choices are limited to what this "
        "particular authority accepts.",
    )
    correction_reference = fields.Char(
        copy=False,
        help="The authority's reference for the filing being amended, where "
        "the receiving system needs it to match the two up.",
    )
    is_correction = fields.Boolean(
        compute="_compute_is_correction", store=True,
        help="Technical: true for anything that amends an earlier filing.",
    )

    # Retention / filed-copy trail (mirrors the l10n_cssk submission mixin).
    submitted_date = fields.Datetime(readonly=True, copy=False)
    submission_reference = fields.Char(copy=False)
    submitted_attachment_id = fields.Many2one(
        "ir.attachment", string="Filed XML", readonly=True, copy=False)
    filed_history_ids = fields.Many2many(
        "ir.attachment", string="Filed history", readonly=True, copy=False)

    # ------------------------------------------------------------------
    # Defaults / computes
    # ------------------------------------------------------------------
    @api.model
    def default_get(self, fields_list):
        restriction = self._country_restriction()
        if restriction and self.env.company.country_id.code != restriction:
            raise UserError(_(
                "You must be logged in a %s company to use this feature.",
                restriction))
        return super().default_get(fields_list)

    def _country_restriction(self):
        return self._country_code

    # ------------------------------------------------------------------
    # Corrections
    # ------------------------------------------------------------------
    # Widened per form. Defaulting to regular-only is deliberate: a form that
    # has not been checked against its authority's rules offers nothing, rather
    # than offering an amendment the receiving system will bounce.
    _supported_correction_types = ("regular",)

    def _selection_correction_type(self):
        supported = self._supported_correction_types
        return [(key, label) for key, label in CORRECTION_TYPES
                if key in supported]

    @api.depends("correction_type")
    def _compute_is_correction(self):
        for rec in self:
            rec.is_correction = rec.correction_type in AMENDING_CORRECTION_TYPES

    def _prior_submitted(self):
        """Filings for the same company and period that were already sent.

        Matched on the PERIOD (``date_from`` / ``date_to``), not on the
        ``year`` / ``month`` fields. An annual form spans the whole year and
        ignores ``month``, which still defaults to the month the record was
        created in — so a corrective annual filing prepared in June never
        found the regular one created in March, and was refused.
        """
        self.ensure_one()
        if not (self.company_id and self.date_from and self.date_to):
            return self.browse()
        return self.search([
            ("id", "!=", self.id or 0),
            ("company_id", "=", self.company_id.id),
            ("date_from", "=", self.date_from),
            ("date_to", "=", self.date_to),
            ("state", "=", "submitted"),
        ])

    @api.constrains("correction_type")
    def _check_correction_type_supported(self):
        for rec in self:
            supported = rec._supported_correction_types
            if rec.correction_type not in supported:
                raise ValidationError(_(
                    "%(report)s does not accept a %(kind)s filing. This "
                    "authority accepts: %(supported)s.",
                    report=(rec._report_code or rec._name).upper(),
                    kind=rec.correction_type,
                    supported=", ".join(supported),
                ))

    def _check_amends_something(self):
        """Refuse to generate an amendment with nothing to amend.

        Sending an opravný for a period never filed is a rejection at best and
        a duplicate at worst, and it is an easy mistake: the form looks exactly
        like the regular one. Called from the generate preflight rather than as
        a constraint, so the record can be prepared while the original is still
        being finished.
        """
        for rec in self:
            if not rec.is_correction:
                continue
            if not rec._prior_submitted():
                raise UserError(_(
                    "There is no submitted %(report)s for %(month)s/%(year)s "
                    "to amend. File the regular declaration first, or set this "
                    "one back to Regular.",
                    report=(rec._report_code or rec._name).upper(),
                    month=rec.month, year=rec.year,
                ))

    @api.model
    def _default_version_id(self):
        # The period defaults to the current month, so today is the period.
        return self._find_version(
            fields.Date.context_today(self), self.env.company.country_id).id

    @api.model
    def _find_version(self, on_date, country):
        """The form version in force on *on_date* (empty if none)."""
        Version = self.env["cssk.payroll.declaration.version"]
        if not (self._report_code and on_date):
            return Version
        return Version.search([
            ("code", "=", self._report_code),
            ("country_id", "=", country.id),
            ("valid_from", "<=", on_date),
            "|", ("valid_to", "=", False), ("valid_to", ">=", on_date),
        ], order="valid_from desc", limit=1)

    def _version_reference_date(self):
        """The day that decides which form version applies: the period's
        first day. A form for a past period is filed in the vintage that was
        in force for that period, not in the one in force on the day it is
        prepared."""
        self.ensure_one()
        return self.date_from

    @api.onchange("year", "month", "company_id")
    def _onchange_period_version(self):
        for rec in self:
            version = rec._find_version(
                rec._version_reference_date(), rec.company_id.country_id)
            if version:
                rec.version_id = version

    def _ensure_period_version(self):
        """Make sure ``version_id`` is a vintage valid for the period.

        The default is chosen when the record is created, from today; the
        period is usually changed afterwards (last month's filing, last
        year's annual one). A version that does not cover the period is
        replaced by the one that does — as is a version of ANOTHER form,
        which the selection offers too — and a period no version covers —
        before the first vintage we ship, or after a form was discontinued —
        is refused rather than rendered in the wrong vintage.
        """
        for rec in self:
            ref = rec._version_reference_date()
            if rec.version_id and ref and (
                    rec.version_id.code == rec._report_code
                    and rec.version_id.valid_from <= ref
                    and (not rec.version_id.valid_to
                         or rec.version_id.valid_to >= ref)):
                continue
            version = rec._find_version(ref, rec.company_id.country_id)
            if version:
                rec.version_id = version
                continue
            ended = self.env["cssk.payroll.declaration.version"].search([
                ("code", "=", rec._report_code),
                ("country_id", "=", rec.company_id.country_id.id),
                ("valid_to", "!=", False),
                ("valid_to", "<", ref),
            ], order="valid_to desc", limit=1) if ref else False
            if ended:
                raise UserError(_(
                    "%(form)s is not filed for periods after %(end)s: the "
                    "form was discontinued. %(successor)s",
                    form=ended.name,
                    end=ended.valid_to,
                    successor=rec._successor_hint(),
                ))
            raise UserError(_(
                "No declaration version is configured for %(code)s in the "
                "period starting %(date)s. Check the shipped version data.",
                code=rec._report_code, date=ref))

    def _successor_hint(self):
        """Hook: tell the user what replaced a discontinued form."""
        return ""

    def _compute_report_code(self):
        for rec in self:
            rec.report_code = rec._report_code or False

    @api.depends("year", "month", "company_id")
    def _compute_name(self):
        for rec in self:
            rec.name = "%s %s/%s" % (
                (rec._report_code or "").upper(), rec.month or "", rec.year or "")

    @api.depends("year", "month")
    def _compute_period(self):
        for rec in self:
            if rec.year and rec.month:
                y, m = int(rec.year), int(rec.month)
                last = _calendar.monthrange(y, m)[1]
                rec.date_from = date(y, m, 1)
                rec.date_to = date(y, m, last)
            else:
                rec.date_from = rec.date_to = False

    @api.depends("line_ids")
    def _compute_lines_count(self):
        for rec in self:
            rec.lines_count = len(rec._sheet_lines())

    def _sheet_lines(self):
        self.ensure_one()
        return self.line_ids.filtered(lambda l: l.res_model == self._name)

    # ------------------------------------------------------------------
    # Engine-neutral payslip adapter
    # ------------------------------------------------------------------
    @api.model
    def _payslip_states(self):
        """Confirmed payslip states of the installed engine.

        Only payroll that was actually run is reported: OCA ``done``,
        Enterprise ``validated`` / ``paid``. Draft payslips (and the OCA
        ``verify`` step) are calculations that may still change; cancelled
        ones never happened. Intersected with the live selection so a state
        one engine lacks is never searched for.
        """
        if "hr.payslip" not in self.env:
            return ()
        available = {
            value for value, _label in
            self.env["hr.payslip"]._fields["state"]._description_selection(
                self.env)
        }
        return tuple(
            state for states in CONFIRMED_PAYSLIP_STATES.values()
            for state in states if state in available)

    @api.model
    def _payslip_period_domain(self, company, date_from, date_to):
        """Payslips of *company* that belong to [date_from, date_to].

        A payslip belongs to the period its END date falls in. Requiring the
        whole payslip inside the period dropped every payslip that straddles
        a month or year boundary (15 March - 14 April, a December payslip
        running into January) from every declaration; keying on one date
        reports each payslip exactly once.
        """
        return [
            ("company_id", "=", company.id),
            ("date_to", ">=", date_from),
            ("date_to", "<=", date_to),
            ("state", "in", self._payslip_states()),
        ]

    def _get_period_payslips(self):
        """The company's confirmed payslips for the reporting period, read
        through the engine-neutral ``hr.payslip`` API (``None`` if no engine
        is installed)."""
        self.ensure_one()
        if "hr.payslip" not in self.env:
            return None
        return self.env["hr.payslip"].search(self._payslip_period_domain(
            self.company_id, self.date_from, self.date_to))

    @api.model
    def _employee_contract_intervals(self, employee, date_from, date_to):
        """Employment periods of *employee* inside [date_from, date_to].

        Built from EVERY version's contract dates, not from the current one:
        the current version describes today, and an employee who left and
        came back, or whose contract was renewed, has periods the current
        version does not show. Overlapping and adjacent periods are merged.
        A version without a start date contributes nothing; an employee with
        no start date on any version is taken as employed for the whole
        period, as before, rather than reported with no insured days.
        """
        spans = []
        versions = employee.sudo().with_context(active_test=False).version_ids
        if not any(versions.mapped("contract_date_start")):
            return [(date_from, date_to)] if date_from <= date_to else []
        for version in versions:
            start = version.contract_date_start
            if not start:
                continue
            end = version.contract_date_end or date_to
            lo, hi = max(start, date_from), min(end, date_to)
            if lo <= hi:
                spans.append((lo, hi))
        merged = []
        for lo, hi in sorted(set(spans)):
            if merged and lo <= merged[-1][1] + timedelta(days=1):
                merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
            else:
                merged.append((lo, hi))
        return merged

    @api.model
    def _employee_insured_days(self, employee, date_from, date_to):
        """Calendar days of employment of *employee* in the period."""
        return sum(
            (hi - lo).days + 1 for lo, hi in
            self._employee_contract_intervals(employee, date_from, date_to))

    def _collect_payslip_totals(self, payslips):
        """THE adapter — reduce payslips to code totals without binding to an
        engine. Reads ``payslip.line_ids`` and each line's ``.code`` / ``.total``
        (the only fields both engines guarantee). Returns::

            {'aggregate': {code: total},
             'aggregate_bases': {code: Σ amount x quantity},
             'per_employee': {employee: {'employee', 'payslips', 'totals',
                                         'bases', 'hours'}}}
        """
        aggregate = defaultdict(float)
        aggregate_bases = defaultdict(float)
        per_employee = {}
        empty = self.env["hr.payslip"] if "hr.payslip" in self.env else None
        for slip in payslips:
            emp = slip.employee_id
            bucket = per_employee.get(emp)
            if bucket is None:
                bucket = per_employee[emp] = {
                    "employee": emp,
                    "payslips": empty,
                    "totals": defaultdict(float),
                    "bases": defaultdict(float),
                    "hours": 0.0,
                }
            if empty is not None:
                bucket["payslips"] |= slip
            for line in slip.line_ids:
                code = line.code
                if not code:
                    continue
                total = line.total
                aggregate[code] += total
                bucket["totals"][code] += total
                # The amount the rule's rate was applied to (both engines:
                # ``amount`` x ``quantity``). For a percentage rule this is
                # its base: SOCIALER carries the capped assessment base.
                base = (line.amount or 0.0) * (
                    line.quantity if line.quantity is not None else 1.0)
                bucket["bases"][code] += base
                aggregate_bases[code] += base
            # worked hours (both engines: worked_days_line_ids.number_of_hours)
            if "worked_days_line_ids" in slip._fields:
                bucket["hours"] += sum(
                    abs(wd.number_of_hours)
                    for wd in slip.worked_days_line_ids)
        return {
            "aggregate": dict(aggregate),
            "aggregate_bases": dict(aggregate_bases),
            "per_employee": per_employee,
        }

    # ------------------------------------------------------------------
    # Generate (orchestration)
    # ------------------------------------------------------------------
    def action_generate_declarations(self):
        """Master-compatible entrypoint (kept for port parity)."""
        return self.action_generate()

    def action_generate(self):
        self.ensure_one()
        self._ensure_not_submitted()
        if self.state != "draft":
            raise UserError(_(
                "Reset the declaration to draft before regenerating it."))
        self._ensure_period_version()
        self._preflight()
        payslips = self._get_period_payslips()
        if payslips is None:
            raise UserError(_(
                "No payroll engine is installed (hr.payslip is unavailable), "
                "so there are no payslips to aggregate."))
        if not payslips:
            raise UserError(_(
                "No payslips found for %(company)s in %(month)s/%(year)s.",
                company=self.company_id.display_name,
                month=self.month, year=self.year))
        data = self._collect_payslip_totals(payslips)
        self._prepare_employee_declarations(data)
        xml_bytes = self._render_xml(data)
        self._validate_against_schema(xml_bytes)
        self._attach_xml(xml_bytes)
        self.state = "generated"
        self.message_post(body=_("Declaration generated and XSD-validated."))
        return True

    def _preflight(self):
        """Master-data checks the XML template relies on. Concrete reports
        extend with form-specific checks (employer id, address …)."""
        self.ensure_one()
        self._check_amends_something()
        return True

    def _prepare_employee_declarations(self, data):
        """(Re)build the per-employee rows from the collected totals."""
        self.ensure_one()
        self._sheet_lines().unlink()
        Decl = self.env["cssk.payroll.employee.declaration"]
        seq = 0
        vals_list = []
        for emp, bucket in sorted(
                data["per_employee"].items(),
                key=lambda kv: (kv[0].name or "", kv[0].id)):
            seq += 10
            totals = {k: v for k, v in bucket["totals"].items()}
            vals_list.append({
                "res_model": self._name,
                "res_id": self.id,
                "sequence": seq,
                "employee_id": emp.id,
                "company_id": self.company_id.id,
                "values_json": totals,
                # Days the employee was actually employed in the period, not
                # the length of the period: someone who joined on the 20th
                # is insured for 12 days of a 31-day month.
                "insured_days": self._employee_insured_days(
                    emp, self.date_from, self.date_to),
                "worked_hours": bucket["hours"],
                "vz_base": abs(totals.get("GROSS", 0.0)),
                "state": "generated",
            })
        if vals_list:
            Decl.create(vals_list)

    @api.model
    def _split_person_name(self, employee):
        """``(first name, surname)`` of *employee* for the authority forms.

        Uses separate first / last name fields when a module provides them
        (OCA ``hr_employee_firstname``). Otherwise the single Odoo name is
        read the way it is written, "Jan Novák": the LAST word is the
        surname and everything before it the first name(s). The forms
        carry them in separate elements, so swapping them files the
        employee under the wrong person.
        """
        first = last = ""
        fields_ = employee._fields
        if "lastname" in fields_ and "firstname" in fields_:
            first = (employee.firstname or "").strip()
            last = (employee.lastname or "").strip()
        if not last:
            first, _sep, last = (employee.name or "").strip().rpartition(" ")
        return first.strip(), last.strip()

    def _get_rendering_data(self, employees):
        """Master-compatible accessor: ``{employee: {code: total}}`` for the
        given employees (used by a future PDF port; the XML export uses the
        richer context in ``_render_xml``)."""
        self.ensure_one()
        out = {}
        for line in self._sheet_lines():
            if line.employee_id in employees:
                out[line.employee_id] = line.values_json or {}
        return out

    # ------------------------------------------------------------------
    # Export pipeline (XSD-validated)
    # ------------------------------------------------------------------
    def _render_xml(self, data):
        self.ensure_one()
        content = self.env["ir.qweb"]._render(
            self.version_id.xml_template_ref_id.id,
            self._base_render_context(data))
        body = str(content).strip()
        return ('<?xml version="1.0" encoding="UTF-8"?>\n' + body).encode(
            "utf-8")

    def _base_render_context(self, data):
        self.ensure_one()
        ctx = {
            "declaration": self,
            # Templates emit the authority's own spelling from this.
            "correction_type": self.correction_type,
            "is_correction": self.is_correction,
            "correction_reference": self.correction_reference or "",
            "company": self.company_id,
            "aggregate": data["aggregate"],
            "lines": self._sheet_lines().sorted("sequence"),
            "per_employee": data["per_employee"],
            # formatting helpers used by the templates
            "i0": lambda v: str(int(round(abs(v or 0.0)))),
            "d2": lambda v: "%.2f" % abs(round(v or 0.0, 2)),
        }
        ctx.update(self._declaration_render_context(data))
        return ctx

    def _declaration_render_context(self, data):
        """Hook: concrete reports add template variables."""
        return {}

    def _validate_against_schema(self, xml_bytes):
        self.ensure_one()
        version = self.version_id
        root = etree.fromstring(xml_bytes)
        got = etree.QName(root).localname
        if version.xml_root_element and got != version.xml_root_element:
            raise UserError(_(
                "Rendered XML root <%(got)s> does not match expected "
                "<%(exp)s>.", got=got, exp=version.xml_root_element))
        schema = self._load_schema(version)
        if schema is None:
            return
        try:
            schema.assertValid(root)
        except etree.DocumentInvalid as exc:
            raise UserError(_(
                "The %(code)s XML failed XSD validation:\n%(err)s",
                code=(self._report_code or "").upper(), err=exc)) from exc

    def _load_schema(self, version):
        """Load the XSD. Prefer the on-disk file (module + filename) so
        relative ``xs:import`` schemaLocations resolve; fall back to the stored
        base64 blob."""
        if version.xml_schema_module and version.xml_schema_filename:
            path = file_path(
                "%s/%s" % (version.xml_schema_module,
                           version.xml_schema_filename))
            return etree.XMLSchema(etree.parse(path))
        if version.xml_schema_data:
            return etree.XMLSchema(
                etree.fromstring(base64.b64decode(version.xml_schema_data)))
        return None

    def _attach_xml(self, xml_bytes):
        self.ensure_one()
        self.xml_attachment_id = self.env["ir.attachment"].create({
            "name": "%s.xml" % (self.name or self._xml_name_fallback),
            "datas": base64.b64encode(xml_bytes),
            "res_model": self._name,
            "res_id": self.id,
            "mimetype": "application/xml",
        })

    # ------------------------------------------------------------------
    # State machine / retention
    # ------------------------------------------------------------------
    def _ensure_not_submitted(self):
        for rec in self:
            if rec.state == "submitted":
                raise UserError(_(
                    "This declaration was marked submitted on %s and is "
                    "locked. Reset it to draft to change it (the filed copy is "
                    "preserved).", rec.submitted_date))

    def action_submit(self):
        for rec in self:
            if rec.state != "generated":
                raise UserError(_(
                    "Generate the XML before marking the declaration "
                    "submitted."))
            if not rec.xml_attachment_id:
                raise UserError(_("There is no generated XML to submit."))
            rec.submitted_attachment_id = rec.xml_attachment_id
            rec.filed_history_ids = [Command.link(rec.xml_attachment_id.id)]
            rec.submitted_date = fields.Datetime.now()
            rec.state = "submitted"
            # Markup on the TEMPLATE and ``%`` for the value: a plain str
            # posts the tags as visible text, and Markup(_(..., arg)) would
            # render whatever the attachment name contains.
            rec.message_post(body=Markup(
                _("Marked <b>submitted</b>. Filed copy: %s")
            ) % (rec.submitted_attachment_id.name or "—"))
        return True

    def action_reset_to_draft(self):
        for rec in self:
            if rec.state == "draft":
                continue
            was = rec.state
            rec.state = "draft"
            rec.message_post(body=_(
                "Reset to draft (from %s). Filed copy preserved: %s",
                was, rec.submitted_attachment_id.name or "—"))
        return True

    def unlink(self):
        for rec in self:
            if rec.state == "submitted":
                raise UserError(_(
                    "%s is marked submitted and cannot be deleted. Reset it "
                    "to draft first.", rec.display_name))
        # remove the per-employee child rows (they are linked by reference)
        self._all_sheet_lines().unlink()
        return super().unlink()

    def _all_sheet_lines(self):
        return self.env["cssk.payroll.employee.declaration"].search([
            ("res_model", "=", self._name), ("res_id", "in", self.ids)])
