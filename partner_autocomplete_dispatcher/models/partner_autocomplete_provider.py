# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, exceptions, fields, models


# Autocomplete Providers Registry
class PartnerAutocompleteProviderRegistry(models.AbstractModel):
    _name = "partner.autocomplete.provider.registry"

    @api.model
    def _get_available_providers(self):
        """Hook for extension.

        ``partner.autocomplete.provider`` is not "no provider": the dispatcher
        hands its searches back to core, which asks Odoo's IAP service. It
        used to be labelled "None", which read as switched off while every
        search still left for Odoo. The real "off" is
        ``partner.autocomplete.provider.none``.
        """
        return [
            (self.env["partner.autocomplete.provider"]._name, "Odoo IAP"),
            (self.env["partner.autocomplete.provider.none"]._name, "None"),
        ]


# Boilerplate for all autocomplete providers
class PartnerAutocompleteProvider(models.AbstractModel):
    _name = "partner.autocomplete.provider"

    @api.model
    def _autocomplete_country_codes(self):
        """Countries whose register this provider reads.

        A partner in one of them is looked up here whatever the company's own
        provider is, so a Slovak company can still autocomplete a Czech
        partner from ARES. Empty: used only as a company's chosen provider.
        """
        return ()

    @api.model
    def read_by_vat(self, vat):
        """Hook for extension"""
        return []

    @api.model
    def enrich_company(self, company_domain, partner_gid, vat):
        """Hook for extension"""
        return []

    @api.model
    def autocomplete(self, query):
        """Hook for extension"""
        return []


class PartnerAutocompleteProviderNone(models.AbstractModel):
    """No lookup at all outside the registers a provider claims by country.

    Every hook keeps the base's empty answer, so a search for a partner whose
    country no installed provider reads returns nothing and nothing is sent
    to Odoo IAP. A Czech or Slovak partner is still looked up in ARES / ORSF
    when those are installed: country dispatch comes first.
    """

    _name = "partner.autocomplete.provider.none"
    _inherit = "partner.autocomplete.provider"
    _description = "Partner autocomplete: no provider"
