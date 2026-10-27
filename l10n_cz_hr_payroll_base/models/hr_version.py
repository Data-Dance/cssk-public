# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The Czech payroll data of an employee, shared by both payroll engines.

The fields live on the employee version (``hr.version``, the 19.0 successor of
``hr.contract``), which is core ``hr`` and therefore engine-neutral. Salary
rules read them as ``contract.<field>`` on the OCA engine and
``version.<field>`` on Enterprise; both hand the same record to every rule.

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

from odoo import api, fields, models

#: Floor only — every engine module narrows it to its payroll-user group.
CZ_PAYROLL_GROUP = "hr.group_hr_manager"

#: The Czech fields, in the order the forms show them. Also the contract
#: template whitelist and the list the engines re-declare with their group.
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


class HrVersion(models.Model):
    _inherit = "hr.version"

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
        "Children (1st tier)", groups=CZ_PAYROLL_GROUP, tracking=True)
    l10n_cz_children_t2 = fields.Integer(
        "Children (2nd tier)", groups=CZ_PAYROLL_GROUP, tracking=True)
    l10n_cz_children_t3 = fields.Integer(
        "Children (3rd+ tier)", groups=CZ_PAYROLL_GROUP, tracking=True)
    l10n_cz_children_ztpp = fields.Integer(
        "of which ZTP/P Children", groups=CZ_PAYROLL_GROUP, tracking=True,
        help="Number of children holding a ZTP/P card (benefit doubled).")

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
        start = max(date_from, self.contract_date_start or date_from)
        end = min(date_to, self.contract_date_end or date_to)
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

    @api.model
    def _get_whitelist_fields_from_template(self):
        # Let these Czech attributes propagate from a contract template to the
        # employee's working version (only for CZ companies).
        whitelisted_fields = super()._get_whitelist_fields_from_template() or []
        if self.env.company.country_id.code == "CZ":
            whitelisted_fields += list(CZ_VERSION_FIELDS)
        return whitelisted_fields
