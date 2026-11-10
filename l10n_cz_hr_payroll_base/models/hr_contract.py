# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The Czech payroll data of an employee, shared by both payroll engines.

The fields live on the contract (``hr.contract``, which 19.0 replaced with
``hr.version``), which is core ``hr_contract`` and therefore engine-neutral. Salary
rules read them as ``contract.<field>`` on the OCA engine and
``contract.<field>`` on Enterprise as well on 18.0; both hand the same record
to every rule.

Access: who may read and write these fields is a payroll question, and the
payroll groups belong to the engines, which this module cannot depend on. So
the fields are declared here with an HR-manager floor, and each engine module
re-declares them with ``groups=`` set to its own payroll-user group. The
engine's declaration wins (field attributes merge in load order), so the access
on an installed system is exactly what it was before the fields moved here.
The floor is deliberately narrow: it only applies when no engine is installed
(for instance after one was uninstalled), and the data — tax declaration,
disability, children — is not something every HR officer needs to see.
"""

from datetime import timedelta

from odoo import fields, models

#: Floor only — every engine module narrows it to its payroll-user group.
CZ_PAYROLL_GROUP = "hr.group_hr_manager"

#: The Czech fields, in the order the forms show them. Also the list the
#: engines re-declare with their group (and, on 19.0, the contract-template
#: whitelist, which 18.0 does not have).
CZ_VERSION_FIELDS = (
    "l10n_cz_tax_declaration",
    "l10n_cz_claim_ztpp",
    "l10n_cz_disability",
    "l10n_cz_children_t1",
    "l10n_cz_children_t2",
    "l10n_cz_children_t3",
    "l10n_cz_children_ztpp",
    "l10n_cz_is_state_insured",
    "l10n_cz_agreement_type",
    "l10n_cz_meal_allowance",
    "l10n_cz_garnishment_dependents",
    "l10n_cz_avg_hourly_earnings",
    "l10n_cz_social_discount_category",
    "l10n_cz_pensioner_discount",
)


#: Worked-day codes whose full-day absences shorten the minimální vyměřovací
#: základ of health insurance by calendar days (§ 3 odst. 9 zákona
#: č. 592/1992 Sb.): sickness, OČR and the § 199 obstacles are "pracovní volno
#: pro důležité osobní překážky v práci" (písm. b); during maternity, parental
#: and paternity leave the state pays the premium as well (písm. c). Unpaid
#: leave is deliberately absent: it does not reduce the minimum base.
CZ_HEALTH_MIN_BASE_EXCLUDED_CODES = (
    "CZSICK",
    "CZOCR",
    "CZOBSTACLE",
    "CZMATERSKA",
    "CZRODICOVSKA",
    "CZOTCOVSKA",
)


#: The child counts are used only while the employee has no child records
#: (``hr.employee.l10n_cz_child_ids``): counts cannot say in which months a
#: child was claimed.
CHILD_COUNT_HELP = ("Used only while no child is recorded under Children "
                    "(tax benefit); with records the payslip counts those, "
                    "month by month.")


class HrContract(models.Model):
    _inherit = "hr.contract"

    # --- Taxpayer declaration & tax credits -------------------------------
    l10n_cz_tax_declaration = fields.Boolean(
        "Taxpayer declaration signed",
        groups=CZ_PAYROLL_GROUP, tracking=True,
        help="If signed with this employer, monthly tax credits and the child "
             "tax benefit are applied on the payslip.")
    l10n_cz_claim_ztpp = fields.Boolean(
        "Employee Holds ZTP/P", groups=CZ_PAYROLL_GROUP, tracking=True,
        help="Employee is a ZTP/P card holder, entitled to the ZTP/P tax credit.")
    l10n_cz_disability = fields.Selection(
        selection=[
            ('none', 'None'),
            ('1_2', 'Invalidity I / II degree'),
            ('3', 'Invalidity III degree'),
        ], string="Invalidity Degree", default='none',
        groups=CZ_PAYROLL_GROUP, tracking=True,
        help="Determines the disability tax credit (basic / extended).")

    # --- Children -------------------------------------
    l10n_cz_children_t1 = fields.Integer(
        "Children (1st tier)", groups=CZ_PAYROLL_GROUP, tracking=True,
        help=CHILD_COUNT_HELP)
    l10n_cz_children_t2 = fields.Integer(
        "Children (2nd tier)", groups=CZ_PAYROLL_GROUP, tracking=True,
        help=CHILD_COUNT_HELP)
    l10n_cz_children_t3 = fields.Integer(
        "Children (3rd+ tier)", groups=CZ_PAYROLL_GROUP, tracking=True,
        help=CHILD_COUNT_HELP)
    l10n_cz_children_ztpp = fields.Integer(
        "of which ZTP/P Children", groups=CZ_PAYROLL_GROUP, tracking=True,
        help="Number of children holding a ZTP/P card (benefit doubled). "
             + CHILD_COUNT_HELP)

    # --- Insurance flags ---------------------------------------------------
    l10n_cz_is_state_insured = fields.Boolean(
        "State-insured person",
        groups=CZ_PAYROLL_GROUP, tracking=True,
        help="Pensioner / student / parental leave / jobseeker / disabled: "
             "the health-insurance minimum-base top-up does not apply.")

    # --- Agreement type (DPP/DPČ) ------------------------------------------
    l10n_cz_agreement_type = fields.Selection(
        selection=[
            ('standard', 'Standard employment'),
            ('dpp', 'DPP (agreement to perform work)'),
            ('dpc', 'DPČ (agreement to perform working activity)'),
        ], string="Agreement Type", default='standard',
        groups=CZ_PAYROLL_GROUP, tracking=True,
        help="Drives the insurance-liability threshold and the tax treatment. "
             "Below the threshold such an agreement pays no social/health insurance and, "
             "without a signed declaration, the 15 % withholding tax applies.")

    # --- Meal allowance (stravenkový paušál) -------------------------------
    l10n_cz_meal_allowance = fields.Monetary(
        "Meal allowance / shift",
        groups=CZ_PAYROLL_GROUP, tracking=True,
        help="Per-shift meal allowance. Tax-exempt up to the statutory limit; "
             "the excess (taxable) is P2.")

    # --- Wage garnishment (exekuční srážky) --------------------------------
    l10n_cz_garnishment_dependents = fields.Integer(
        "Garnishment dependents",
        groups=CZ_PAYROLL_GROUP, tracking=True,
        help="Number of dependents (spouse/children) counted for the "
             "non-attachable amount when computing a wage garnishment. Each "
             "adds 1/4 of the base protected amount.")

    # --- Employer social-insurance discount (sleva na pojistném, §7a) ------
    l10n_cz_social_discount_category = fields.Selection(
        selection=[
            ('none', 'None'),
            ('over55', 'Over 55 (§7a/1/a)'),
            ('parent_under10', 'Parent of a child under 10 (§7a/1/b)'),
            ('carer', 'Carer of a dependent person (§7a/1/c)'),
            ('student', 'Student preparing for a profession (§7a/1/d)'),
            ('retraining', 'Retraining participant (§7a/1/e)'),
            ('disabled', 'Person with a disability (§7a/1/f)'),
            ('under21', 'Younger than 21 (§7a/1/g)'),
        ], string="Social insurance discount category",
        default='none', groups=CZ_PAYROLL_GROUP, tracking=True,
        help="Eligibility category for the 5 % employer social-insurance discount "
             "(§7a of Act 589/1992). The discount applies only for a shorter working "
             "time of 8-30 h/week (except employees under 21) with a monthly "
             "assessment base up to 1.5x the average wage. Only one employer may "
             "claim it per employee; the intent must be notified to ČSSZ.")

    l10n_cz_pensioner_discount = fields.Boolean(
        "Working pensioner discount",
        groups=CZ_PAYROLL_GROUP, tracking=True,
        help="Lowers the employee's social insurance by 6.5 % of the assessment "
             "base. For an old-age pensioner at pension age, drawing the "
             "pension in full, for the whole calendar month. The employee "
             "applies to the employer with the proof; it cannot be applied "
             "retroactively and is claimed once across all jobs with one "
             "employer.")

    # --- Sickness compensation (náhrada mzdy) ------------------------------
    l10n_cz_avg_hourly_earnings = fields.Monetary(
        "Average hourly earnings",
        groups=CZ_PAYROLL_GROUP, tracking=True,
        help="Average hourly earnings from the previous quarter, used to "
             "compute the sickness compensation for the first "
             "14 calendar days of temporary incapacity.")

    def _l10n_cz_health_min_base_ratio(self, date_from, date_to, code_of_type):
        """Share of the period the health minimum base applies to.

        § 3 odst. 9 zákona č. 592/1992 Sb.: the minimální vyměřovací základ
        "se snižuje na poměrnou část odpovídající počtu kalendářních dnů" when
        the employment did not last the whole period (písm. a), for days of
        pracovní volno pro důležité osobní překážky (písm. b) and for days the
        state pays the premium too (písm. c).

        Counted in calendar days. Only whole-day time off counts: a doctor's
        visit of two hours does not take a calendar day off the minimum base.
        *code_of_type* maps an ``hr.leave.type`` to its Czech worked-day code;
        the two engines store it differently.
        """
        self.ensure_one()
        period_days = (date_to - date_from).days + 1
        if period_days <= 0:
            return 0.0
        start = max(date_from, self.date_start or date_from)
        end = min(date_to, self.date_end or date_to)
        if end < start:
            return 0.0
        days = {start + timedelta(days=n) for n in range((end - start).days + 1)}
        leaves = self.env["hr.leave"].sudo().search([
            ("employee_id", "=", self.employee_id.id),
            ("state", "=", "validate"),
            ("request_date_from", "<=", end),
            ("request_date_to", ">=", start),
        ])
        for leave in leaves:
            if leave.request_unit_hours or leave.request_unit_half:
                continue
            if code_of_type(leave.holiday_status_id) not in (
                CZ_HEALTH_MIN_BASE_EXCLUDED_CODES
            ):
                continue
            day = leave.request_date_from
            while day <= leave.request_date_to:
                days.discard(day)
                day += timedelta(days=1)
        return len(days) / period_days

    # --- Child tax benefit, month by month (§ 35c ZDP) --------------------
    def _l10n_cz_child_counts(self, day):
        """The children the benefit is claimed for in the month of *day*, as
        ``{order: [children, of which ZTP/P]}`` for the orders 1, 2 and 3.

        From the employee's child records when there are any: a child counts
        from the month of birth or of *Claimed from* to the month of *Claimed
        to* (see ``l10n.cz.employee.child._l10n_cz_maintained_in``). Without
        records, from this contract's counts, which hold for any month the
        contract is used for; a ZTP/P child is then doubled at the first
        child's amount, the counts saying nothing about its order.
        """
        self.ensure_one()
        counts = {"1": [0, 0], "2": [0, 0], "3": [0, 0]}
        kids = self.employee_id.sudo().l10n_cz_child_ids
        if kids:
            for kid in kids:
                if kid._l10n_cz_claimed_in(day.year, day.month):
                    counts[kid.order][0] += 1
                    counts[kid.order][1] += int(kid.ztpp)
            return counts
        if not (self.l10n_cz_children_t1 + self.l10n_cz_children_t2
                + self.l10n_cz_children_t3):
            return counts
        counts["1"] = [self.l10n_cz_children_t1, self.l10n_cz_children_ztpp]
        counts["2"][0] = self.l10n_cz_children_t2
        counts["3"][0] = self.l10n_cz_children_t3
        return counts

    def _l10n_cz_child_benefit(self, day, parameter):
        """The month's child tax benefit before it is set against the tax.

        *parameter* returns a rule parameter's value for the month (each
        engine reads its parameters its own way). A ZTP/P child counts twice
        at its own order's amount (§ 35c odst. 7 ZDP).
        """
        self.ensure_one()
        total = 0.0
        for order, (children, ztpp) in self._l10n_cz_child_counts(day).items():
            if children or ztpp:
                total += (children + ztpp) * parameter("l10n_cz_child_%s" % order)
        return total
