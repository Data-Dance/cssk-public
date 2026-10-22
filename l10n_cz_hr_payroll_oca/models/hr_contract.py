# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# Czech payroll fields live on the contract; the salary rules read them as
# ``contract.<field>``.

from odoo import fields, models

CZ_PAYROLL_GROUP = "payroll.group_payroll_user"


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
    l10n_cz_dpp_notified = fields.Boolean(
        "Notified DPP", groups=CZ_PAYROLL_GROUP, tracking=True,
        help="A single notified DPP enjoys the higher insurance threshold "
             "(25 % of the average wage); a non-notified DPP uses the general "
             "decisive-income threshold.")

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
