# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Dated statutory rates driving the garnishment allocator.

The base module cannot use ``hr.rule.parameter`` — that model belongs to the
payroll engines and this module depends on neither. It therefore carries its
own tiny dated-rate table, shipped as data for CZ and SK. A new statutory
vintage (a new životní minimum, a changed coefficient) is a data change.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .garnishment_calc import (
    CLASS_FINE,
    CLASS_MAINTENANCE,
    CLASS_ORDINARY,
    CLASS_PRIORITY,
)


class HrWageGarnishmentRate(models.Model):
    _name = "hr.wage.garnishment.rate"
    _description = "Wage Garnishment Statutory Rate"
    _order = "country_id, date_from desc"

    _country_date_uniq = models.Constraint(
        "unique(country_id, date_from)",
        "Only one wage-garnishment rate record per country and start date.",
    )

    name = fields.Char(compute="_compute_name", store=True)
    country_id = fields.Many2one("res.country", required=True, index=True)
    country_code = fields.Char(related="country_id.code")
    date_from = fields.Date(
        required=True,
        help="First day on which these figures apply. The Czech amounts change "
        "on 1 January; the Slovak subsistence minimum changes on 1 July.",
    )

    # --- Czech Republic: NV 595/2006 Sb. ----------------------------------
    cz_subsistence = fields.Float(
        "Životní minimum jednotlivce",
        digits=(16, 2),
        help="Monthly subsistence minimum for an individual (CZK).",
    )
    cz_normative_rent = fields.Float(
        "Normativní nájemné", digits=(16, 2),
        help="Normative rent for a one-person household (CZK).",
    )
    cz_energy = fields.Float(
        "Energetický paušál", digits=(16, 2),
        help="Flat energy allowance for a one-person household (CZK).",
    )
    cz_base_pct = fields.Float(
        "Base percentage", digits=(16, 2), default=85.0,
        help="Percentage of the sum of the three components that forms the "
        "non-attachable amount for the debtor (85 % from 2026).",
    )
    cz_dependent_fraction = fields.Float(
        "Per-dependent fraction", digits=(16, 4), default=0.25,
        help="Fraction of the debtor's non-attachable amount added per "
        "dependent (one quarter).",
    )
    cz_unlimited_limit = fields.Float(
        "Unlimited-seizure limit", digits=(16, 2),
        help="Amount of the remainder above which the wage is seized without "
        "limitation — 1.9× the sum of the three components (NV 595/2006 § 2).",
    )

    # --- Slovakia: NV 268/2006 Z. z. --------------------------------------
    sk_zivotne_minimum = fields.Float(
        "Životné minimum", digits=(16, 2),
        help="Monthly subsistence minimum for an adult individual (EUR).",
    )
    sk_basic_coeff = fields.Float(
        "Ordinary coefficient", digits=(16, 4), default=1.40,
        help="§ 1 ods. 1 — 140 % of the subsistence minimum.",
    )
    sk_priority_coeff = fields.Float(
        "Priority coefficient", digits=(16, 4), default=1.00,
        help="§ 2 ods. 2 — 100 % of the subsistence minimum for priority claims.",
    )
    sk_maintenance_outer_coeff = fields.Float(
        "Maintenance outer coefficient", digits=(16, 4), default=0.70,
        help="§ 2 ods. 1 — the 70 % applied on top of the inner coefficient "
        "for maintenance of a minor child.",
    )
    sk_maintenance_inner_coeff = fields.Float(
        "Maintenance inner coefficient", digits=(16, 4), default=0.60,
        help="§ 2 ods. 1 — the 60 % of the subsistence minimum.",
    )
    sk_fine_coeff = fields.Float(
        "Fine coefficient", digits=(16, 4), default=0.50,
        help="§ 2a — 50 % of the subsistence minimum for administrative fines.",
    )
    sk_dependent_coeff = fields.Float(
        "Per-dependant coefficient", digits=(16, 4), default=0.25,
    )
    sk_dependent_coeff_pensioner = fields.Float(
        "Per-dependant coefficient (pensioner)", digits=(16, 4), default=0.50,
    )
    sk_unlimited_mult = fields.Float(
        "Unlimited-seizure multiple", digits=(16, 4), default=3.0,
        help="§ 3 — multiple of the § 1 ods. 1 basic sum above which the "
        "remainder is seized without limitation.",
    )

    @api.depends("country_id", "date_from")
    def _compute_name(self):
        for rate in self:
            rate.name = "%s %s" % (
                rate.country_id.code or "",
                rate.date_from or "",
            )

    @api.model
    def _get_rate(self, country_code, date):
        """Return the rate record in force for *country_code* on *date*."""
        rate = self.search(
            [("country_id.code", "=", country_code), ("date_from", "<=", date)],
            order="date_from desc",
            limit=1,
        )
        if not rate:
            raise UserError(
                _(
                    "No wage-garnishment rates are configured for %(country)s "
                    "as of %(date)s. Add a Wage Garnishment Rate record before "
                    "computing garnishments.",
                    country=country_code,
                    date=date,
                )
            )
        return rate

    def _rates_dict(self):
        """Shape the record into the plain dict the allocator expects."""
        self.ensure_one()
        if self.country_id.code == "CZ":
            return {
                "subsistence": self.cz_subsistence,
                "normative_rent": self.cz_normative_rent,
                "energy": self.cz_energy,
                "base_pct": self.cz_base_pct,
                "dependent_fraction": self.cz_dependent_fraction,
                "unlimited_limit": self.cz_unlimited_limit,
            }
        return {
            "zivotne_minimum": self.sk_zivotne_minimum,
            "basic_coeff": self.sk_basic_coeff,
            "priority_coeff": self.sk_priority_coeff,
            "maintenance_outer_coeff": self.sk_maintenance_outer_coeff,
            "maintenance_inner_coeff": self.sk_maintenance_inner_coeff,
            "fine_coeff": self.sk_fine_coeff,
            "dependent_coeff": self.sk_dependent_coeff,
            "dependent_coeff_pensioner": self.sk_dependent_coeff_pensioner,
            "unlimited_mult": self.sk_unlimited_mult,
        }

    def _protected_amount(self, dependents, claim_class=CLASS_ORDINARY, is_pensioner=False):
        """Convenience accessor used by the views and the notice reports."""
        self.ensure_one()
        from .garnishment_calc import cz_protected_amount, sk_protected_amount

        rates = self._rates_dict()
        if self.country_id.code == "CZ":
            return cz_protected_amount(rates, dependents)
        return sk_protected_amount(rates, dependents, claim_class, is_pensioner)

    @api.model
    def _supported_classes(self, country_code):
        """Claim classes that make sense for a country."""
        if country_code == "CZ":
            return (CLASS_MAINTENANCE, CLASS_PRIORITY, CLASS_ORDINARY)
        return (CLASS_MAINTENANCE, CLASS_PRIORITY, CLASS_FINE, CLASS_ORDINARY)
