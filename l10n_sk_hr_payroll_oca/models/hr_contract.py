# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# Slovak payroll fields live on the contract; the salary rules read them as
# ``contract.<field>``.

from odoo import _, api, fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"

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
        ],
        string="Agreement Type",
        default="none",
        help="Work-agreement type outside a standard employment relationship. "
        "DoVP (agreement to perform work) is treated as irregular income: the "
        "employee pays only old-age and disability "
        "insurance — no sickness or unemployment. DoPČ (agreement on work "
        "activity) is treated as regular income (full social set, like "
        "employment). Health insurance applies to both.",
        groups="payroll.group_payroll_user",
        tracking=True,
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

    # --- Agreements: regularity, hours and exemptions ----------------------
    # Backported from 19.0, where these live on hr.version.
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
    l10n_sk_hourly_wage = fields.Monetary(
        string="Hourly Wage (SK)",
        help="Gross hourly wage for an hourly-paid worker (e.g. a DoBPŠ "
        "student). When set (> 0), BASIC = actual worked hours (WORK100) × "
        "this rate, instead of the monthly wage with proration.",
        groups="payroll.group_payroll_user",
        tracking=True,
    )
    l10n_sk_guarantee_exempt = fields.Boolean(
        string="Guarantee-insurance exempt (≥50% statutory owner)",
        help="The worker is a statutory body or its member with at least a "
        "50% share in the employer, so is NOT guarantee-insured (garančné "
        "poistenie), per §102 z. 461/2003 — the employer pays no guarantee-"
        "fund premium for them. All other contributions are unaffected.",
        groups="payroll.group_payroll_user",
        tracking=True,
    )
    l10n_sk_health_exempt = fields.Boolean(
        string="Health-insurance exempt (štátny poistenec)",
        help="The worker is a state insuree (poistenec štátu) — typically a "
        "student on a DoBPŠ agreement or a working pensioner — so the "
        "agreement income carries no health insurance, per z. 580/2004. "
        "Independent of the pension OOP.",
        groups="payroll.group_payroll_user",
        tracking=True,
    )

    @api.depends("l10n_sk_agreement_type")
    def _compute_l10n_sk_income_regular(self):
        """Default the regularity from the agreement kind, but let it be set.

        A stored editable compute rather than a plain default, so a record
        created programmatically — imports, tests, a contract wizard — gets
        the usual treatment for its agreement kind instead of silently
        inheriting a default that happens to be wrong for it. DoVP is most
        often agreed as a single payment on completion and DoPC as monthly,
        but neither is required by law, so the value stays editable.
        """
        for contract in self:
            contract.l10n_sk_income_regular = (
                contract.l10n_sk_agreement_type != "dovp"
            )

    @api.depends("l10n_sk_agreement_type", "resource_calendar_id")
    def _compute_l10n_sk_agreement_hours_warning(self):
        # §§ 226 / 228a / 227 Zákonníka práce. The annual DoVP ceiling cannot
        # be checked from a calendar alone, so it is approximated by the
        # contracted weekly hours over a full year; the weekly ceilings are
        # exact.
        limits = {"dovp": ("annual", 350.0), "dopc": ("weekly", 10.0),
                  "dobps": ("weekly", 20.0)}
        for contract in self:
            contract.l10n_sk_agreement_hours_warning = False
            limit = limits.get(contract.l10n_sk_agreement_type)
            calendar = contract.resource_calendar_id
            if not limit or not calendar or not calendar.hours_per_week:
                continue
            basis, ceiling = limit
            weekly = calendar.hours_per_week
            value = weekly * 52.0 if basis == "annual" else weekly
            if value > ceiling:
                contract.l10n_sk_agreement_hours_warning = _(
                    "The contracted working time of %(value).1f hours "
                    "%(basis)s exceeds the statutory ceiling of %(ceiling).0f "
                    "for this agreement type.",
                    value=value,
                    basis="per year" if basis == "annual" else "per week",
                    ceiling=ceiling,
                )
