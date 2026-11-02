# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, exceptions, fields, models


# Autocomplete Providers Registry
class PartnerAutocompleteProviderRegistry(models.AbstractModel):
    _name = "partner.autocomplete.provider.registry"

    @api.model
    def _get_available_providers(self):
        """Hook for extension"""
        return [(self.env["partner.autocomplete.provider"]._name, "None")]


# Boilerplate for all autocomplete providers
class PartnerAutocompleteProvider(models.AbstractModel):
    _name = "partner.autocomplete.provider"

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
