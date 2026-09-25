from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..engine import depreciation as eng


class AccountAssetTaxClass(models.Model):
    """A statutory tax-depreciation group (odpisová skupina / odpisová skupina).

    Country localizations (``l10n_cz_account_asset_tax`` /
    ``l10n_sk_account_asset_tax``) ship one record per group with the verified
    coefficients. The record is the bridge between the Odoo asset and the pure
    :mod:`engine.depreciation` calculator.
    """

    _name = "account.asset.tax.class"
    _description = "Tax Depreciation Group"
    _order = "country_code, group_number"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(
        required=True,
        help="Stable technical code, e.g. CZ-1 / SK-0. Referenced by the "
        "localization spec; do not change after assets reference it.",
    )
    country_code = fields.Selection(
        [("CZ", "Czech Republic"), ("SK", "Slovakia")],
        string="Country",
        required=True,
    )
    group_number = fields.Integer(string="Group", required=True)
    useful_life_years = fields.Integer(string="Depreciation Period (years)", required=True)
    active = fields.Boolean(default=True)

    # Allowed methods -------------------------------------------------------
    allow_linear = fields.Boolean(string="Allows Straight-line", default=True)
    allow_accelerated = fields.Boolean(string="Allows Accelerated", default=False)
    allow_extraordinary = fields.Boolean(string="Allows Extraordinary (CZ §30a)", default=False)

    # CZ straight-line rates (% of entry price) -----------------------------
    linear_rate_first = fields.Float(string="Linear Rate – Year 1 (%)", digits=(6, 4))
    linear_rate_next = fields.Float(string="Linear Rate – Next Years (%)", digits=(6, 4))
    linear_rate_increased = fields.Float(
        string="Linear Rate – Increased Price (%)", digits=(6, 4),
        help="Rate applied to the increased entry price after a technical improvement (CZ §31).",
    )

    # Accelerated coefficients (both countries) -----------------------------
    accel_coeff_first = fields.Integer(string="Accel. Coefficient – Year 1")
    accel_coeff_next = fields.Integer(string="Accel. Coefficient – Next Years")
    accel_coeff_increased = fields.Integer(
        string="Accel. Coefficient – Increased Residual",
        help="Coefficient applied after a technical improvement (CZ §32 / SK §28).",
    )

    _sql_constraints = [
        ("code_uniq", "unique(code)", "The tax depreciation group code must be unique."),
    ]

    @api.depends("code", "name", "useful_life_years")
    def _compute_display_name(self):
        for rec in self:
            # The "N years" suffix is translated as a whole (msgid "(%s y)") so
            # each language renders its own unit — SK/CZ "(6 r.)", not "(6y)".
            rec.display_name = "%s — %s %s" % (
                rec.code or "?",
                rec.name or "",
                self.env._("(%s y)", rec.useful_life_years or 0),
            )

    @api.constrains("useful_life_years")
    def _check_life(self):
        for rec in self:
            if rec.useful_life_years <= 0:
                raise ValidationError(_("The depreciation period must be a positive number of years."))

    def to_engine(self):
        """Return the country-agnostic :class:`engine.depreciation.TaxClass`."""
        self.ensure_one()
        return eng.TaxClass(
            country=self.country_code,
            group_number=self.group_number,
            useful_life_years=self.useful_life_years,
            linear_rate_first=self.linear_rate_first,
            linear_rate_next=self.linear_rate_next,
            linear_rate_increased=self.linear_rate_increased,
            accel_coeff_first=self.accel_coeff_first,
            accel_coeff_next=self.accel_coeff_next,
            accel_coeff_increased=self.accel_coeff_increased,
        )

    def allowed_methods(self):
        """Return the list of method keys this group permits."""
        self.ensure_one()
        methods = []
        if self.allow_linear:
            methods.append(eng.METHOD_LINEAR)
        if self.allow_accelerated:
            methods.append(eng.METHOD_ACCELERATED)
        if self.allow_extraordinary:
            methods.append(eng.METHOD_EXTRAORDINARY)
        return methods
