# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# Slovak payroll fields live on the contract/version; the salary rules read them
# as ``contract.<field>`` (the payslip ``contract_id`` is an ``hr.version``).

from odoo import _, api, fields, models


class HrVersion(models.Model):
    _inherit = "hr.version"

    # --- Income tax ---------------------------------------------------------
    l10n_sk_tax_declaration_signed = fields.Boolean(
        string="Tax Declaration Signed",
        help="The employee signed the taxpayer's declaration with this "
        "employer, so the monthly non-taxable part (NČZD) and the child tax "
        "bonus are applied here. Only one employer at a time may apply them.",
        groups="payroll.group_payroll_user",
        tracking=True,
    )

    # --- Child tax bonus ----------------------------------------------------
    l10n_sk_children_under_15 = fields.Integer(
        string="Children < 15y (tax bonus)",
        help="Number of dependent children under 15 for the child tax bonus "
        "(€100/child in 2025 & 2026).",
        groups="payroll.group_payroll_user",
        tracking=True,
    )
    l10n_sk_children_15_18 = fields.Integer(
        string="Children 15–17y (tax bonus)",
        help="Number of dependent children aged 15 to under 18 for the child "
        "bonus (€50/child in 2025 & 2026).",
        groups="payroll.group_payroll_user",
        tracking=True,
    )

    # --- Health insurance ---------------------------------------------------
    l10n_sk_ztp = fields.Boolean(
        string="ZŤP / Disabled",
        help="Person with a health disability (>=50% functional impairment). "
        "Applies the halved health-insurance rate (2%/2.5% employee).",
        groups="payroll.group_payroll_user",
        tracking=True,
    )
    l10n_sk_health_oop_claim = fields.Boolean(
        string="Claim Health OOP",
        help="Claim the health-insurance deductible allowance (OOP) "
        "for low earners in a "
        "regular employment relationship. It reduces ONLY the employee's health "
        "assessment base: max 380 €/mo, phased out by 2 € of base per 1 € of "
        "income above 380 €, reaching 0 at 570 €. Must be claimed in writing; "
        "it does not apply to an agreement.",
        groups="payroll.group_payroll_user",
        tracking=True,
    )
    l10n_sk_health_exempt = fields.Boolean(
        string="Health-insurance exempt (štátny poistenec)",
        help="The worker is a state insuree (poistenec štátu) — typically a "
        "student on a DoBPŠ agreement or a working pensioner — so the agreement "
        "income carries no health insurance (employee, employer, or minimum-base "
        "top-up), per z. 580/2004. Independent of the pension OOP: a student is "
        "health-exempt even in a month where the OOP is not claimed.",
        groups="payroll.group_payroll_user",
        tracking=True,
    )
    l10n_sk_guarantee_exempt = fields.Boolean(
        string="Guarantee-insurance exempt (≥50% statutory owner)",
        help="The worker is a statutory body or its member with at least a 50% "
        "share in the employer, so is NOT guarantee-insured (garančné poistenie), "
        "per §102 z. 461/2003 — the employer pays no guarantee-fund premium for "
        "them. All other social/health contributions are unaffected.",
        groups="payroll.group_payroll_user",
        tracking=True,
    )
    l10n_sk_hourly_wage = fields.Monetary(
        string="Hourly Wage (SK)",
        help="Gross hourly wage for an hourly-paid worker (e.g. a DoBPŠ student). "
        "When set (> 0), BASIC = actual worked hours (WORK100) × this rate, "
        "instead of the monthly wage with day-proration.",
        groups="payroll.group_payroll_user",
        tracking=True,
    )

    # --- Meal allowance (stravné) ------------------------------------------
    l10n_sk_meal_allowance_type = fields.Selection(
        selection=[
            ("none", "None"),
            ("voucher", "Meal voucher"),
            ("financial", "Financial contribution"),
        ],
        string="Meal Allowance Type",
        default="none",
        help="Legal meal-allowance option. The employer contributes >=55% of "
        "the statutory meal allowance; the contribution is exempt from income tax and from both the "
        "social and health assessment bases.",
        groups="payroll.group_payroll_user",
        tracking=True,
    )
    l10n_sk_meal_days = fields.Integer(
        string="Meal Days / Month",
        help="Number of days the meal allowance is provided. Leave 0 to use the "
        "worked days (WORK100) of the payslip.",
        groups="payroll.group_payroll_user",
        tracking=True,
    )
    # Backward-compatible manual per-day overrides (were flat per-slip amounts in
    # the original port). If > 0 they override the computed per-day amounts.
    l10n_sk_meal_voucher_employee = fields.Monetary(
        string="Meal Voucher Employee Share (per day, override)",
        groups="payroll.group_payroll_user",
        tracking=True,
    )
    l10n_sk_meal_voucher_employer = fields.Monetary(
        string="Meal Employer Contribution (per day, override)",
        groups="payroll.group_payroll_user",
        tracking=True,
    )

    # --- Agreements (dohody) ------------------------------------------------
    l10n_sk_agreement_type = fields.Selection(
        selection=[
            ("none", "Employment (not an agreement)"),
            ("dovp", "DoVP — agreement to perform work"),
            ("dopc", "DoPČ — agreement on work activity"),
            ("dobps", "DoBPŠ — student work agreement"),
        ],
        string="Agreement Type",
        compute="_compute_l10n_sk_agreement_type",
        store=True,
        readonly=False,
        help="Work-agreement type outside a standard employment relationship. "
        "The fund set follows the INCOME REGULARITY rather than the kind "
        "of agreement — see the Regular monthly income flag. Health "
        "insurance applies to all of them unless the worker is a state "
        "insuree.",
        groups="payroll.group_payroll_user",
        tracking=True,
    )

    l10n_sk_income_regular = fields.Boolean(
        string="Regular monthly income",
        compute="_compute_l10n_sk_income_regular",
        store=True,
        readonly=False,
        help="Whether the agreed remuneration is a PRAVIDELNY (regular "
        "monthly) income. This — not the kind of agreement — decides the "
        "social-insurance fund set: a worker with irregular income pays only "
        "old-age and disability insurance, with no sickness, unemployment or "
        "short-time contribution. Both DoVP and DoPC can lawfully be agreed "
        "either way, so it is recorded separately. Always true for a standard "
        "employment relationship.",
        groups="payroll.group_payroll_user",
        tracking=True,
    )
    l10n_sk_agreement_hours_warning = fields.Char(
        string="Agreement Hours Warning",
        compute="_compute_l10n_sk_agreement_hours_warning",
        help="Set when the contracted working time exceeds the statutory "
        "ceiling for this kind of agreement.",
    )

    @api.depends("l10n_sk_agreement_type")
    def _compute_l10n_sk_income_regular(self):
        """Default the regularity from the agreement kind, but let it be set.

        A stored editable compute rather than a plain default, so a record
        created programmatically — imports, tests, the contract wizard — gets
        the usual treatment for its agreement kind instead of silently
        inheriting a default that happens to be wrong for it. DoVP is most
        often agreed as a single payment on completion and DoPC as monthly,
        but neither is required by law, so the value remains editable.
        """
        for version in self:
            version.l10n_sk_income_regular = (
                version.l10n_sk_agreement_type != "dovp"
            )

    @api.depends("l10n_sk_agreement_type", "resource_calendar_id")
    def _compute_l10n_sk_agreement_hours_warning(self):
        # SS 226 / 228a / 227 Zakonnika prace. The annual DoVP ceiling cannot
        # be checked from a calendar alone, so it is approximated by the
        # contracted weekly hours over a full year; the weekly ceilings are
        # exact.
        limits = {"dovp": ("annual", 350.0), "dopc": ("weekly", 10.0),
                  "dobps": ("weekly", 20.0)}
        for version in self:
            version.l10n_sk_agreement_hours_warning = False
            limit = limits.get(version.l10n_sk_agreement_type)
            calendar = version.resource_calendar_id
            if not limit or not calendar or not calendar.hours_per_week:
                continue
            basis, ceiling = limit
            weekly = calendar.hours_per_week
            value = weekly * 52.0 if basis == "annual" else weekly
            if value > ceiling:
                version.l10n_sk_agreement_hours_warning = _(
                    "The contracted working time of %(value).1f hours "
                    "%(basis)s exceeds the statutory ceiling of %(ceiling).0f "
                    "for this agreement type.",
                    value=value,
                    basis="per year" if basis == "annual" else "per week",
                    ceiling=ceiling,
                )

    l10n_sk_agreement_oop = fields.Boolean(
        string="OOP Agreement (student/pensioner)",
        help="Claim the pension deductible allowance (OOP) on an agreement for "
        "an eligible pensioner or student. It reduces the assessment base for "
        "old-age, disability and the reserve fund by up to 200 €/month. Only "
        "one such agreement per month may claim it.",
        groups="payroll.group_payroll_user",
        tracking=True,
    )

    # --- Wage garnishment (exekučné zrážky) --------------------------------
    l10n_sk_garnishment_dependents = fields.Integer(
        string="Garnishment Dependents",
        help="Number of dependants the debtor supports, used "
        "to raise the non-seizable amount of a wage "
        "garnishment. Each dependant adds 25% of the basic non-seizable amount. "
        "Only used when a garnishment input (GARNISHMENT / GARNISHMENT_PRIORITY) "
        "is present on the payslip.",
        groups="payroll.group_payroll_user",
        tracking=True,
    )

    @api.model
    def _get_whitelist_fields_from_template(self):
        """Allow the Slovak payroll fields to be copied from a contract template.

        On 19.0 a contract is an ``hr.version`` and new versions may be created
        from a template; the engine only carries over whitelisted fields.
        """
        whitelisted_fields = super()._get_whitelist_fields_from_template() or []
        whitelisted_fields += [
            "l10n_sk_tax_declaration_signed",
            "l10n_sk_children_under_15",
            "l10n_sk_children_15_18",
            "l10n_sk_ztp",
            "l10n_sk_health_oop_claim",
            "l10n_sk_health_exempt",
            "l10n_sk_guarantee_exempt",
            "l10n_sk_hourly_wage",
            "l10n_sk_meal_allowance_type",
            "l10n_sk_meal_days",
            "l10n_sk_meal_voucher_employee",
            "l10n_sk_meal_voucher_employer",
            "l10n_sk_agreement_type",
            "l10n_sk_agreement_oop",
            "l10n_sk_garnishment_dependents",
        ]
        return whitelisted_fields
