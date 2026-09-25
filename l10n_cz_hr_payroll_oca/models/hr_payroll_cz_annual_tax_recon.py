# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
# Annual tax reconciliation (roční zúčtování záloh na daň z příjmů ze závislé
# činnosti, §38ch / §38ča ZDP). The employer performs it, on the employee's
# written request (Žádost) filed by 15 Feb of the following year, for employees
# who had income only from this employer (or bring a Potvrzení from others).
#
# Procedure (§38ch odst. 1-5, computed per §16 / §35ba / §35c):
#   1. Annual tax base = Σ the year's monthly tax bases (gross).
#   2. minus nezdanitelné části základu daně (§15): state-supported old-age
#      products (penzijní/DPS/DIP + životní pojištění, joint cap 48 000),
#      mortgage interest (cap 150 000), gifts/dary (cap 30 % of the base).
#      NB: union dues and further-education exams were §15 items until 2023 but
#      were REPEALED by the 2024 consolidation package, so they are recorded for
#      documentation only and NOT deducted for tax years >= 2024.
#   3. Base rounded DOWN to whole 100 Kč (§16 odst. 1); annual tax 15 % up to
#      36x průměrná mzda, 23 % above it.
#   4. minus roční slevy na dani (§35ba): sleva na poplatníka 30 840 (always in
#      full), na manžela/manželku, ZTP/P, invalidita -> daň po slevě (>= 0).
#   5. minus roční daňové zvýhodnění na děti (§35c): the part up to the tax is a
#      sleva; the surplus is the roční daňový bonus (if annual income reaches
#      6x minimum wage).
#   6. Compared with Σ advances actually withheld after the monthly slevy and
#      child sleva -> přeplatek (refund, the common case; a nedoplatek is NOT
#      collected through RZ) and the doplatek na daňovém bonusu.
#
# Sources (2025 & 2026 figures / procedure, confirmed):
#   https://financnisprava.gov.cz/cs/dane/dane/dan-z-prijmu/zamestnanci-zamestnavatele/obecne-informace
#   https://www.pruvodcepodnikanim.cz/clanek/slevy-na-dani-a-nezdanitelne-polozky-2025/
#   https://www.pruvodcepodnikanim.cz/clanek/slevy-na-dani-a-nezdanitelne-polozky-2026/
#   https://www.podnikatel.cz/clanky/od-jake-vyse-mzdy-a-prijmu-se-bude-v-roce-2026-platit-23-sazba-dane-z-prijmu/
#   https://www.praceamzda.cz/clanky/19249/rocni-zuctovani-dane-za-rok-2025

from datetime import date

from odoo import api, fields, models


class HrPayrollCzAnnualTaxRecon(models.Model):
    _name = "hr.payroll.cz.annual.tax.recon"
    _description = "CZ Annual Tax Reconciliation"
    _order = "year desc, employee_id"

    name = fields.Char(compute="_compute_name", store=True)
    employee_id = fields.Many2one(
        "hr.employee", required=True, ondelete="cascade")
    company_id = fields.Many2one(
        "res.company", required=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        related="company_id.currency_id", readonly=True)
    year = fields.Integer(
        required=True, default=lambda self: date.today().year - 1,
        help="Tax year that is being reconciled.")
    state = fields.Selection(
        [("draft", "Draft"), ("computed", "Computed"), ("done", "Settled")],
        default="draft", required=True)

    # --- §15 nezdanitelné části základu daně (annual inputs) ---------------
    l10n_cz_pension_contrib = fields.Monetary(
        "Pension / DPS / DIP Contributions",
        help="Contributions to state-supported old-age products (supplementary "
             "pension insurance / supplementary pension savings / DIP). Jointly with "
             "life insurance capped at 48 000 CZK/year (§15(5)).")
    l10n_cz_life_insurance = fields.Monetary(
        "Life insurance",
        help="Private life-insurance premiums. Jointly with pension "
             "contributions capped at 48 000 CZK/year (§15(6)).")
    l10n_cz_mortgage_interest = fields.Monetary(
        "Mortgage interest",
        help="Interest on a housing loan, capped at 150 000 CZK/year "
             "(300 000 for loans taken before 2021 - simplification: 150 000). "
             "§15(3)-(4).")
    l10n_cz_gifts = fields.Monetary(
        "Gifts (§15(1))",
        help="Value of donations; deductible from 1 000 CZK / 2 % of the base "
             "up to 30 % of the base.")
    l10n_cz_union_dues = fields.Monetary(
        "Union dues",
        help="Repealed by the 2024 consolidation package - recorded for "
             "documentation only, NOT deducted for years >= 2024.")
    l10n_cz_education = fields.Monetary(
        "Further-education exams",
        help="Repealed by the 2024 consolidation package - recorded for "
             "documentation only, NOT deducted for years >= 2024.")
    l10n_cz_spouse_credit = fields.Monetary(
        "Spouse credit",
        help="Annual spouse tax credit (24 840; 49 680 for a ZTP/P "
             "spouse). Enter the eligible amount: the spouse's own income must "
             "be below 68 000 CZK/year and (since 2024) the couple must care for "
             "a child under 3. §35ba(1)(b).")

    # --- Computed results (stored) ----------------------------------------
    l10n_cz_annual_gross_base = fields.Monetary(
        "Annual Gross Tax Base", readonly=True)
    l10n_cz_nontaxable_total = fields.Monetary(
        "Non-taxable Deductions (§15)", readonly=True)
    l10n_cz_annual_tax_base = fields.Monetary(
        "Annual Tax Base (rounded)", readonly=True)
    l10n_cz_annual_tax = fields.Monetary("Annual Tax (§16)", readonly=True)
    l10n_cz_annual_slevy = fields.Monetary(
        "Annual Credits (§35ba)", readonly=True)
    l10n_cz_annual_tax_after_slevy = fields.Monetary(
        "Tax after Credits", readonly=True)
    l10n_cz_annual_child_benefit = fields.Monetary(
        "Child Tax Credit (§35c)", readonly=True)
    l10n_cz_annual_final_tax = fields.Monetary(
        "Final Annual Tax", readonly=True)
    l10n_cz_annual_bonus = fields.Monetary(
        "Annual Child Bonus Entitlement", readonly=True)
    l10n_cz_advances_withheld = fields.Monetary(
        "Advances Withheld (net of monthly credits)", readonly=True)
    l10n_cz_bonus_paid = fields.Monetary(
        "Monthly Bonus Already Paid", readonly=True)
    l10n_cz_overpayment = fields.Monetary(
        "Overpayment", readonly=True,
        help="Refund paid to the employee in the March payslip. An underpayment "
             "is not collected through the annual reconciliation.")
    l10n_cz_bonus_doplatek = fields.Monetary(
        "Bonus top-up", readonly=True)
    l10n_cz_settlement_total = fields.Monetary(
        "Settlement Total", readonly=True,
        help="Overpayment + bonus top-up; posted onto a payslip via the "
             "ANNUAL_TAX_SETTLEMENT salary rule (increases net pay).")

    _sql_constraints = [
        ("employee_year_uniq", "unique(employee_id, year, company_id)",
         "An annual reconciliation already exists for this employee and year."),
    ]

    @api.depends("employee_id", "year")
    def _compute_name(self):
        for rec in self:
            rec.name = "%s / %s (%s)" % (
                self.env._("Annual tax reconciliation"),
                rec.year,
                rec.employee_id.name or "?",
            )

    # -- Engine-specific accessors -----------------------------------------

    def _l10n_cz_recon_version(self):
        """Return the record carrying the CZ payroll flags.

        The 19.0 port keeps the OCA payroll engine but stores the CZ fields on
        the employee version (hr.version, the 19.0 successor of hr.contract).
        """
        self.ensure_one()
        return self.employee_id.version_id

    def _l10n_cz_rule_parameter(self, code):
        self.ensure_one()
        return self.env["hr.rule.parameter"]._get_parameter_value(
            code, date(self.year, 12, 31))

    def _l10n_cz_year_payslips(self):
        """The employee's done payslips for the tax year."""
        self.ensure_one()
        return self.env["hr.payslip"].search([
            ("employee_id", "=", self.employee_id.id),
            ("state", "=", "done"),
            ("date_from", ">=", date(self.year, 1, 1)),
            ("date_to", "<=", date(self.year, 12, 31)),
        ])

    def _l10n_cz_sum_lines(self, payslips, codes):
        """Return {code: Σ line total} across the payslip recordset."""
        return {c: sum(p.get_salary_line_total(c) for p in payslips)
                for c in codes}

    # -- Reconciliation ----------------------------------------------------

    def action_compute(self):
        for rec in self:
            rec._l10n_cz_compute_one()
        return True

    def _l10n_cz_compute_one(self):
        self.ensure_one()
        version = self._l10n_cz_recon_version()
        payslips = self._l10n_cz_year_payslips()
        sums = self._l10n_cz_sum_lines(
            payslips,
            ["TAXBASE", "INCOMETAX", "TAXCREDIT", "CHILDBEN", "CHILDBONUS"])

        gross_base = sums["TAXBASE"]
        # INCOMETAX line totals are stored negative (a deduction); TAXCREDIT and
        # CHILDBEN are positive lines that offset the advance.
        advances_gross = -sums["INCOMETAX"]
        advances_net = advances_gross - sums["TAXCREDIT"] - sums["CHILDBEN"]
        bonus_paid = sums["CHILDBONUS"]

        # -- §15 non-taxable parts (union dues / education repealed from 2024) --
        pension_life = min(
            self.l10n_cz_pension_contrib + self.l10n_cz_life_insurance,
            self._l10n_cz_rule_parameter("l10n_cz_pension_max_year"))
        mortgage = min(
            self.l10n_cz_mortgage_interest,
            self._l10n_cz_rule_parameter("l10n_cz_mortgage_max_year"))
        gift_pct = self._l10n_cz_rule_parameter("l10n_cz_gift_max_pct")
        gifts = min(self.l10n_cz_gifts, gift_pct / 100.0 * gross_base)
        nontaxable = pension_life + mortgage + max(gifts, 0.0)
        if self.year < 2024:
            nontaxable += self.l10n_cz_union_dues + self.l10n_cz_education

        # -- Annual tax base rounded DOWN to whole 100 Kč (§16 odst. 1) --
        base_raw = max(gross_base - nontaxable, 0.0)
        tax_base = int(base_raw // 100) * 100

        thr = self._l10n_cz_rule_parameter("l10n_cz_tax_threshold_year")
        r1 = self._l10n_cz_rule_parameter("l10n_cz_tax_rate_1")
        r2 = self._l10n_cz_rule_parameter("l10n_cz_tax_rate_2")
        annual_tax = (r1 / 100.0 * min(tax_base, thr)
                      + r2 / 100.0 * max(tax_base - thr, 0))

        # -- §35ba personal credits (poplatník always in full) --
        slevy = self._l10n_cz_rule_parameter("l10n_cz_credit_taxpayer_year")
        slevy += self.l10n_cz_spouse_credit
        if version.l10n_cz_claim_ztpp:
            slevy += self._l10n_cz_rule_parameter("l10n_cz_credit_ztpp_year")
        if version.l10n_cz_disability == "1_2":
            slevy += self._l10n_cz_rule_parameter("l10n_cz_credit_disab_12_year")
        elif version.l10n_cz_disability == "3":
            slevy += self._l10n_cz_rule_parameter("l10n_cz_credit_disab_3_year")
        tax_after_slevy = max(annual_tax - slevy, 0.0)

        # -- §35c child tax benefit + annual daňový bonus --
        c1 = self._l10n_cz_rule_parameter("l10n_cz_child_1_year")
        c2 = self._l10n_cz_rule_parameter("l10n_cz_child_2_year")
        c3 = self._l10n_cz_rule_parameter("l10n_cz_child_3_year")
        entitlement = (version.l10n_cz_children_t1 * c1
                       + version.l10n_cz_children_t2 * c2
                       + version.l10n_cz_children_t3 * c3
                       + version.l10n_cz_children_ztpp * c1)
        child_benefit = min(entitlement, tax_after_slevy)
        final_tax = tax_after_slevy - child_benefit
        bonus_min = self._l10n_cz_rule_parameter("l10n_cz_bonus_min_income_year")
        if gross_base >= bonus_min:
            annual_bonus = max(entitlement - tax_after_slevy, 0.0)
        else:
            annual_bonus = 0.0

        # -- Settlement (přeplatek + doplatek na bonusu; nedoplatek not taken) --
        overpayment = max(advances_net - final_tax, 0.0)
        bonus_doplatek = max(annual_bonus - bonus_paid, 0.0)

        self.write({
            "l10n_cz_annual_gross_base": gross_base,
            "l10n_cz_nontaxable_total": nontaxable,
            "l10n_cz_annual_tax_base": tax_base,
            "l10n_cz_annual_tax": annual_tax,
            "l10n_cz_annual_slevy": slevy,
            "l10n_cz_annual_tax_after_slevy": tax_after_slevy,
            "l10n_cz_annual_child_benefit": child_benefit,
            "l10n_cz_annual_final_tax": final_tax,
            "l10n_cz_annual_bonus": annual_bonus,
            "l10n_cz_advances_withheld": advances_net,
            "l10n_cz_bonus_paid": bonus_paid,
            "l10n_cz_overpayment": overpayment,
            "l10n_cz_bonus_doplatek": bonus_doplatek,
            "l10n_cz_settlement_total": overpayment + bonus_doplatek,
            "state": "computed",
        })

    # -- Posting the settlement onto a payslip -----------------------------

    def _l10n_cz_settlement_input_vals(self, payslip):
        """Input-line vals for the ANNUAL_TAX_SETTLEMENT rule (OCA idiom:
        free-form input keyed by ``code``)."""
        self.ensure_one()
        return {
            "name": self.name,
            "code": "ANNUAL_TAX_SETTLEMENT",
            "amount": self.l10n_cz_settlement_total,
            "contract_id": payslip.contract_id.id,
        }

    def action_post_to_payslip(self, payslip):
        """Post the settlement onto ``payslip`` (usually the March slip) and
        recompute it, so the ANNUAL_TAX_SETTLEMENT line increases net pay."""
        self.ensure_one()
        payslip.ensure_one()
        vals = self._l10n_cz_settlement_input_vals(payslip)
        existing = payslip.input_line_ids.filtered(
            lambda l: l.code == "ANNUAL_TAX_SETTLEMENT")
        if existing:
            existing.write({"amount": vals["amount"], "name": vals["name"]})
        else:
            payslip.write({"input_line_ids": [(0, 0, vals)]})
        payslip.compute_sheet()
        self.state = "done"
        return payslip
