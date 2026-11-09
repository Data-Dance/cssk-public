# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.exceptions import UserError


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    fuel_type = fields.Selection(selection_add=[('lng', 'LNG')], ondelete={'lng': 'set null'})

    l10n_sk_eu_category = fields.Selection(
        [(key, key) for key in ('L1e', 'L2e', 'L3e', 'L4e', 'L5e', 'L6e', 'L7e',
                                'M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4')],
        string='EU vehicle category')
    l10n_sk_first_registration_date = fields.Date(string='First registration on technical certificate')
    l10n_sk_engine_cm3 = fields.Integer(string='Cylinder capacity (cm³)')
    l10n_sk_max_mass_kg = fields.Integer(string='Maximum permissible mass (kg)')
    l10n_sk_axles = fields.Integer(string='Number of axles')
    l10n_sk_dmv_taxpayer = fields.Selection([(key, key) for key in 'abcde'],
        string='Vehicle taxpayer under section 3', default='a')
    l10n_sk_registered_in_sk = fields.Boolean(string='Registration in Slovakia reviewed')
    l10n_sk_tax_exempt = fields.Boolean(string='Vehicle tax exemption reviewed')
    l10n_sk_not_taxable_reason = fields.Text(string='Exemption or outside-scope evidence')
    l10n_sk_hybrid_documented = fields.Boolean(string='Hybrid propulsion documented')
    l10n_sk_liability_from_override = fields.Date(string='Reviewed liability event override')
    l10n_sk_liability_override_reason = fields.Text(string='Section 8 liability override evidence')

    def _l10n_sk_vehicle_tax_facts(self):
        self.ensure_one()
        if (self.company_id.country_id.code != 'SK' or not self.l10n_sk_registered_in_sk
                or self.l10n_sk_tax_exempt or self.l10n_sk_not_taxable_reason
                or self.l10n_sk_dmv_taxpayer not in ('a', 'b')
                or not self.acquisition_date or not self.l10n_sk_first_registration_date):
            raise UserError(_('Review Slovak registration, ordinary taxpayer a/b and actual registration/acquisition dates on the fleet vehicle.'))
        fuel = self.fuel_type or ''
        propulsion = ('hybrid' if fuel == 'full_hybrid' or fuel.startswith('plug_in_hybrid') else
                      fuel if fuel in ('electric', 'cng', 'lng', 'hydrogen', 'lpg') else
                      'combustion' if fuel in ('diesel', 'gasoline') else False)
        if not propulsion or (propulsion == 'hybrid' and not self.l10n_sk_hybrid_documented):
            raise UserError(_('Review documented fleet propulsion before claiming vehicle-tax treatment.'))
        if propulsion == 'electric' and (self.power_unit != 'power' or self.power <= 0):
            raise UserError(_('Record the electric vehicle power in kW on its fleet record.'))
        start = max(self.acquisition_date, self.l10n_sk_first_registration_date)
        if self.l10n_sk_liability_from_override:
            if not (self.l10n_sk_liability_override_reason or '').strip():
                raise UserError(_('Retain the section 8 evidence for an overridden liability event.'))
            start = self.l10n_sk_liability_from_override
        return {'registration_number': self.license_plate or '', 'category': self.l10n_sk_eu_category,
            'first_registered': fields.Date.to_string(self.l10n_sk_first_registration_date),
            'liability_from': fields.Date.to_string(start),
            'liability_to': fields.Date.to_string(self.write_off_date),
            'propulsion': propulsion, 'engine_cm3': self.l10n_sk_engine_cm3,
            'power_kw': self.power if propulsion == 'electric' else 0,
            'weight_kg': self.l10n_sk_max_mass_kg, 'axles': self.l10n_sk_axles,
            'taxpayer': self.l10n_sk_dmv_taxpayer}

    def _l10n_sk_vehicle_tax_identity(self):
        self.ensure_one()
        return {'vehicle': self.id, 'company': self.company_id.id, 'vin': self.vin_sn or '',
            'facts': self._l10n_sk_vehicle_tax_facts(),
            'liability_override_evidence': self.l10n_sk_liability_override_reason or ''}
