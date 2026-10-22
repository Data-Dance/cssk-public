###################################################################################
#
#    Copyright (c) 2022 Radovan Skolnik, Data Dance s.r.o.
#
#    Data Dance Proprietary License v1.0
#
#    This software and associated files (the "Software") may only be used
#    (executed, modified, executed after modifications) if you have
#    purchased a valid license from Data Dance s.r.o.
#
#    The above permissions are granted for a single database per purchased
#    license. Furthermore, with a valid license it is permitted to use the
#    software on other databases as long as the usage is limited to a testing
#    or development environment.
#
#    You may develop modules based on the Software or that use the Software
#    as a library (typically by depending on it, importing it and using its
#    resources), but without copying any source code or material from the
#    Software. You may distribute those modules under the license of your
#    choice, provided that this license is compatible with the terms of the
#    Data Dance Proprietary License (For example: LGPL, MIT, or proprietary
#    licenses similar to this one).
#
#    It is forbidden to publish, distribute, sublicense, or sell copies of
#    the Software or modified copies of the Software.
#
#    The above copyright notice and this permission notice must be included
#    in all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###################################################################################

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
