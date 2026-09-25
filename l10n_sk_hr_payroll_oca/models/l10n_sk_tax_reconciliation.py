# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
# Ročné zúčtovanie preddavkov na daň z príjmov zo závislej činnosti (§38 zákona
# č. 595/2003 Z. z. o dani z príjmov). The employer performs the annual tax
# reconciliation on the employee's written request (Žiadosť o vykonanie RZ,
# submitted by 15 February of the following year) for employees who had only
# Slovak dependent-activity (employment) income in the tax year.
#
# The record is keyed per (employee, tax year). It gathers the year's monthly
# tax bases (Σ TAXBASE), advance income tax withheld (Σ preddavky) and child
# bonus already paid from the employee's monthly payslips, then recomputes the
# annual tax liability using the ANNUAL statutory figures — the annual NČZD with
# its high-income taper, the annual progressive tax bands, and the annual child
# bonus entitlement — and compares it to what was withheld to produce a
# preplatok (refund) or nedoplatok (underpayment).
#
# Confirmed 2025/2026 annual figures (cited in data/hr_rule_parameter_data.xml):
#   * NČZD na daňovníka 2025 = 5 753,79 € (21× ŽM 273,99); full up to a tax base
#     of 25 426,27 €, then 12 110,36 − ¼ × base, reaching 0 at 48 441,43 €.
#     Finančná správa "Nezdaniteľná časť základu dane na daňovníka za rok 2025"
#     <https://podpora.financnasprava.sk/844317>, podnikajte.sk
#     "Nezdaniteľné časti základu dane 2025".
#   * 2026 = 5 966,73 € (21× ŽM 284,13); full up to 26 083,13 €.
#   * 19 %/25 % annual band boundary 2025 = 48 441,43 € (176,8× ŽM 273,99).
#     2026 reform bands 154,8×/212,4×/264,0× ŽM (19/25/30/35 %).
#   * DDS / III. pilier annual cap = 180 € (§11 ods. 8 ZDP); NČZD na manželku up
#     to 5 260,61 € (19,2× ŽM 273,99) — both are annual inputs on the record.
#     podnikajte.sk "Ročné zúčtovanie dane 2026 (za rok 2025)".
#
# NOTE: ročné zúčtovanie zdravotného poistenia (the annual health-insurance
# reconciliation) is a SEPARATE, insurer-side procedure (§19 zákona
# č. 580/2004 Z. z.) performed by the health insurer, not the employer — it is
# out of scope for this payroll model.

from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Salary-rule codes read from the monthly payslips.
L10N_SK_TAXBASE_CODE = "TAXBASE"
L10N_SK_INCOMETAX_CODES = ("INCOMETAX", "INCOMETAX19", "INCOMETAX25")
L10N_SK_CHILD_BONUS_CODE = "CHILD_BONUS"
# Input code the settlement salary rule is driven by.
L10N_SK_SETTLEMENT_INPUT_CODE = "ANNUAL_TAX_SETTLEMENT"


class L10nSkTaxReconciliation(models.Model):
    _name = "l10n.sk.tax.reconciliation"
    _description = "Slovak Annual Tax Reconciliation"
    _order = "year desc, employee_id"

    name = fields.Char(compute="_compute_name", store=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
    )
    year = fields.Integer(
        string="Tax Year",
        required=True,
        default=lambda self: fields.Date.context_today(self).year - 1,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("computed", "Computed"), ("posted", "Posted")],
        default="draft",
        required=True,
    )
    gather_from_payslips = fields.Boolean(
        string="Gather from Payslips",
        default=True,
        help="When set, computing the reconciliation reads the annual tax base, "
        "advance tax and child bonus already paid from the employee's monthly "
        "payslips of the tax year. Untick to enter those totals manually.",
    )

    # --- Gathered / entered annual totals ----------------------------------
    annual_tax_base = fields.Monetary(
        string="Annual Tax Base",
        help="Sum of the monthly income tax bases (Σ (gross − employee "
        "insurance)) for the tax year.",
    )
    annual_advance_tax = fields.Monetary(
        string="Advance Tax Withheld",
        help="Sum of the monthly income tax advances withheld during the year.",
    )
    annual_child_bonus_paid = fields.Monetary(
        string="Child Tax Bonus Paid",
        help="Sum of the child tax bonus already paid out monthly.",
    )

    # --- Annual reconciliation inputs (per §38 / §11 ZDP) ------------------
    nczd_spouse = fields.Monetary(
        string="Spouse Non-taxable Part (NČZD)",
        help="Annual non-taxable part for a spouse (§11 ods. 3 ZDP), up to "
        "5 260,61 € for 2025 (19.2× subsistence minimum), reduced by the spouse's "
        "own income and tapered for high earners. Enter the eligible amount.",
    )
    dds_contributions = fields.Monetary(
        string="Supplementary Pension Contributions (DDS, 3rd pillar)",
        help="Supplementary pension savings (3rd pillar) contributions paid in "
        "the year; deductible from the tax base up to the annual cap of 180 € "
        "(§11 ods. 8 ZDP). Amounts above the cap are ignored.",
    )
    employee_premium = fields.Monetary(
        string="Employee Premium",
        help="Employee premium (§32a ZDP), if the employee qualifies. Added to "
        "the settlement as a credit. Usually 0.",
    )
    asignacia_note = fields.Char(
        string="Tax Assignation Note (2%/3%)",
        help="Informational note for the 2 %/3 % tax assignation (§50 ZDP) — "
        "the share of paid tax the employee may assign to an NGO. Not computed "
        "here; recorded for the employer's annual tax payment certificate.",
    )

    # --- Computed annual results -------------------------------------------
    nczd_taxpayer = fields.Monetary(
        string="Taxpayer Non-taxable Part (NČZD)",
        compute="_compute_reconciliation",
        store=True,
    )
    nczd_total = fields.Monetary(
        string="Total Non-taxable Part (NČZD)",
        compute="_compute_reconciliation",
        store=True,
    )
    taxable_base = fields.Monetary(
        string="Taxable Base",
        compute="_compute_reconciliation",
        store=True,
    )
    annual_tax = fields.Monetary(
        string="Annual Tax",
        compute="_compute_reconciliation",
        store=True,
    )
    child_bonus_entitlement = fields.Monetary(
        string="Child Tax Bonus Entitlement",
        compute="_compute_reconciliation",
        store=True,
    )
    result_amount = fields.Monetary(
        string="Overpayment (+) / Underpayment (−)",
        compute="_compute_reconciliation",
        store=True,
        help="Positive = overpayment (refund credited to the employee); "
        "negative = underpayment (withheld).",
    )
    result_type = fields.Selection(
        [("none", "Settled"), ("preplatok", "Overpayment"), ("nedoplatok", "Underpayment")],
        compute="_compute_reconciliation",
        store=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
    )

    # --- Settlement posting -------------------------------------------------
    settlement_payslip_id = fields.Many2one(
        "hr.payslip",
        string="Settlement Payslip",
        help="Payslip of the annual-reconciliation month onto which the "
        "overpayment/underpayment is posted (via the ANNUAL_TAX_SETTLEMENT input).",
    )
    settlement_line_posted = fields.Boolean(readonly=True)

    _sql_constraints = [
        (
            "employee_year_uniq",
            "unique (employee_id, year, company_id)",
            "An annual tax reconciliation already exists for this employee and "
            "year.",
        ),
    ]

    @api.depends("employee_id", "year")
    def _compute_name(self):
        for rec in self:
            rec.name = _("Annual tax reconciliation %(name)s / %(year)s") % {
                "name": rec.employee_id.name or "?",
                "year": rec.year,
            }

    # ------------------------------------------------------------------
    # Statutory parameter accessor (dated, at year end)
    # ------------------------------------------------------------------
    def _l10n_sk_rule_parameter(self, code):
        """Return the dated statutory parameter ``code`` at the tax-year end."""
        self.ensure_one()
        return self.env["hr.rule.parameter"]._get_parameter_value(
            code, date(self.year, 12, 31)
        )

    # ------------------------------------------------------------------
    # Core computation (pure, shared across both SK payroll builds)
    # ------------------------------------------------------------------
    @api.depends(
        "annual_tax_base",
        "annual_advance_tax",
        "annual_child_bonus_paid",
        "nczd_spouse",
        "dds_contributions",
        "employee_premium",
        "year",
        "employee_id",
    )
    def _compute_reconciliation(self):
        for rec in self:
            if not rec.employee_id or not rec.year:
                rec.nczd_taxpayer = rec.nczd_total = rec.taxable_base = 0.0
                rec.annual_tax = rec.child_bonus_entitlement = 0.0
                rec.result_amount = 0.0
                rec.result_type = "none"
                continue
            base = max(0.0, rec.annual_tax_base)

            # --- NČZD na daňovníka (annual) with the high-income taper -----
            full = rec._l10n_sk_rule_parameter("l10n_sk_nczd_annual")
            threshold = rec._l10n_sk_rule_parameter("l10n_sk_nczd_taper_threshold")
            if base <= threshold:
                nczd_tp = full
            else:
                const = rec._l10n_sk_rule_parameter("l10n_sk_nczd_taper_const")
                nczd_tp = max(0.0, const - 0.25 * base)
            nczd_tp = round(nczd_tp, 2)

            # --- Other NČZD: na manželku + DDS (capped) --------------------
            dds_cap = rec._l10n_sk_rule_parameter("l10n_sk_dds_annual_cap")
            dds = min(max(0.0, rec.dds_contributions), dds_cap)
            spouse = max(0.0, rec.nczd_spouse)
            nczd_total = round(nczd_tp + spouse + dds, 2)

            taxable = max(0.0, round(base - nczd_total, 2))

            # --- Annual progressive tax bands ------------------------------
            bands = rec._l10n_sk_rule_parameter("l10n_sk_income_tax_bands_annual")
            tax = 0.0
            prev = 0.0
            for band_rate, ceiling in bands:
                if taxable > prev:
                    tax += (min(taxable, ceiling) - prev) * band_rate
                prev = ceiling
            annual_tax = round(tax, 2)

            # --- Annual child bonus entitlement (cap + taper) --------------
            entitlement = rec._l10n_sk_annual_child_bonus(base)

            # --- Settlement ------------------------------------------------
            tax_settlement = round(rec.annual_advance_tax - annual_tax, 2)
            bonus_settlement = round(entitlement - rec.annual_child_bonus_paid, 2)
            result = round(
                tax_settlement + bonus_settlement + max(0.0, rec.employee_premium), 2
            )

            rec.nczd_taxpayer = nczd_tp
            rec.nczd_total = nczd_total
            rec.taxable_base = taxable
            rec.annual_tax = annual_tax
            rec.child_bonus_entitlement = entitlement
            rec.result_amount = result
            if result > 0.005:
                rec.result_type = "preplatok"
            elif result < -0.005:
                rec.result_type = "nedoplatok"
            else:
                rec.result_type = "none"

    def _l10n_sk_annual_child_bonus(self, base):
        """Annual daňový bonus entitlement, with the %-of-base cap and taper."""
        self.ensure_one()
        n_young, n_teen = self._l10n_sk_children_counts()
        n = n_young + n_teen
        if n <= 0:
            return 0.0
        amount = (
            n_young * self._l10n_sk_rule_parameter("l10n_sk_child_bonus_under_15") * 12
            + n_teen * self._l10n_sk_rule_parameter("l10n_sk_child_bonus_15_18") * 12
        )
        caps = self._l10n_sk_rule_parameter("l10n_sk_child_bonus_pct_caps")
        cap_pct = caps[min(n, len(caps)) - 1]
        amount = min(amount, base * cap_pct / 100.0)
        cb_threshold = self._l10n_sk_rule_parameter(
            "l10n_sk_child_bonus_taper_threshold"
        )
        if base > cb_threshold:
            coeff = self._l10n_sk_rule_parameter("l10n_sk_child_bonus_taper_coeff")
            amount -= coeff * (base - cb_threshold)
        return round(max(0.0, amount), 2)

    def _l10n_sk_children_counts(self):
        """Children counts (< 15 / 15–17) from the employee's latest contract."""
        self.ensure_one()
        contract = self._l10n_sk_reference_contract()
        if not contract:
            return 0, 0
        return (
            contract.l10n_sk_children_under_15 or 0,
            contract.l10n_sk_children_15_18 or 0,
        )

    def _l10n_sk_reference_contract(self):
        """The record carrying the l10n_sk_children_* fields (contract/version).

        On the 18.0 build this is an ``hr.contract`` (``employee.contract_id`` /
        ``payslip.contract_id``); on the 19.0 port it is an ``hr.version``. The
        ``getattr`` fallbacks keep this model identical across both builds.
        """
        self.ensure_one()
        slips = self._l10n_sk_year_payslips()
        if slips:
            return slips.sorted("date_from")[-1].contract_id
        return getattr(self.employee_id, "version_id", False) or getattr(
            self.employee_id, "contract_id", False
        )

    # ------------------------------------------------------------------
    # Gathering from the monthly payslips
    # ------------------------------------------------------------------
    def _l10n_sk_year_payslips(self):
        self.ensure_one()
        return self.env["hr.payslip"].search(
            [
                ("employee_id", "=", self.employee_id.id),
                ("date_from", ">=", date(self.year, 1, 1)),
                ("date_to", "<=", date(self.year, 12, 31)),
                ("state", "!=", "cancel"),
                ("id", "!=", self.settlement_payslip_id.id),
            ]
        )

    def action_compute(self):
        for rec in self:
            if rec.gather_from_payslips:
                base = advance = bonus = 0.0
                for slip in rec._l10n_sk_year_payslips():
                    for line in slip.line_ids:
                        if line.code == L10N_SK_TAXBASE_CODE:
                            base += line.total
                        elif line.code in L10N_SK_INCOMETAX_CODES:
                            advance += -line.total  # withheld tax stored negative
                        elif line.code == L10N_SK_CHILD_BONUS_CODE:
                            bonus += line.total
                rec.annual_tax_base = round(base, 2)
                rec.annual_advance_tax = round(advance, 2)
                rec.annual_child_bonus_paid = round(bonus, 2)
            rec.state = "computed"
        return True

    # ------------------------------------------------------------------
    # Posting the settlement onto a payslip
    # ------------------------------------------------------------------
    def action_post_settlement(self):
        for rec in self:
            if not rec.settlement_payslip_id:
                raise UserError(
                    _("Set the settlement payslip before posting the result.")
                )
            payslip = rec.settlement_payslip_id
            existing = payslip.input_line_ids.filtered(
                lambda i: i.code == L10N_SK_SETTLEMENT_INPUT_CODE
            )
            existing.unlink()
            rec._l10n_sk_create_settlement_input(payslip)
            payslip.compute_sheet()
            rec.settlement_line_posted = True
            rec.state = "posted"
        return True

    def _l10n_sk_create_settlement_input(self, payslip):
        """Create the ANNUAL_TAX_SETTLEMENT input (OCA free-code input model)."""
        self.ensure_one()
        self.env["hr.payslip.input"].create(
            {
                "payslip_id": payslip.id,
                "contract_id": payslip.contract_id.id,
                "name": _("Annual tax reconciliation %s") % self.year,
                "code": L10N_SK_SETTLEMENT_INPUT_CODE,
                "amount": self.result_amount,
                "sequence": 10,
            }
        )
