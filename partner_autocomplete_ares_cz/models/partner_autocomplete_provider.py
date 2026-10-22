###################################################################################
#
#    Copyright (c) 2022 Data Dance s.r.o.
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

import logging
from datetime import datetime

import requests
from odoo import _, api, models
from requests.exceptions import HTTPError

_logger = logging.getLogger(__name__)


class PartnerAutocompleteProviderRegistry(models.AbstractModel):
    _inherit = "partner.autocomplete.provider.registry"

    @api.model
    def _get_available_providers(self):
        return super()._get_available_providers() + [
            (
                self.env["partner.autocomplete.provider.ares_cz"]._name,
                "ARES.CZ",
            )
        ]


class PartnerAutocompleteProvider(models.AbstractModel):
    _inherit = "partner.autocomplete.provider"
    _name = "partner.autocomplete.provider.ares_cz"

    @api.model
    def read_by_vat(self, vat):
        """
        This code is reachable only with semantically correct VAT numbers
        It is ensured by JavaScript library used in partner_autocomplete
        See: partner_autocomplete/static/lib/jsvat.js
        """
        result = {}
        # TODO: find a method to search by VAT number
        return [result]

    @api.model
    def _enrich_dynamic_mapping(self, result, mapping):
        for parameter, value in mapping:
            field = self.env["ir.config_parameter"].sudo().get_param(parameter)
            field = self.env["ir.model.fields"].sudo().browse(int(field))
            if field and value and value != "":
                # convert date fields
                if parameter.endswith("_date"):
                    # value = {"date": value}
                    value = datetime.strptime(value, "%Y-%m-%d").date()
                result[field.name] = value
        return result

    @api.model
    def enrich_company(self, company_domain, partner_gid, vat):
        result = {}
        try:
            url = f"https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{partner_gid}"
            session = requests.Session()
            response = session.get(url)
            response.raise_for_status()
            record = response.json()
            if "kod" not in record:
                result["name"] = record.get("obchodniJmeno", "")
                if "sidlo" in record:
                    result["street"] = (
                        record["sidlo"].get("textovaAdresa").split(",")[0]
                    )
                    country_code = record["sidlo"].get("kodStatu", "")
                    if country_code:
                        country = self.env["res.country"].search(
                            [["code", "=ilike", country_code]]
                        )
                        if country:
                            result["country_id"] = {
                                "id": country.id,
                                "display_name": country.display_name,
                            }
                    result["zip"] = record["sidlo"].get("psc", "")
                    result["city"] = record["sidlo"].get("nazevObce", "")
                result["vat"] = record.get("dic", "")
                result["partner_gid"] = str(partner_gid)
                result["partner_autocomplete_provider"] = self._name
            mapping_pairs = [
                ("ares_cz.mapping.ico", record.get("ico")),
            ]
            self._enrich_dynamic_mapping(result, mapping_pairs)

        except HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            _logger.info(f"HTTP error occurred: {http_err}")
            # result.update(
            #     {
            #         "error": True,
            #         "error_message": f"HTTP error ocurred: {http_err}",
            #     }
            # )
        except KeyError as key_err:
            # do nothing - there was no answer part probably
            _logger.info(f"Key error occurred: {key_err}")
            pass
        except Exception as err:
            print(f"Other error occurred: {err}")
            _logger.info(f"Other error occurred: {err}")
            # result.update(
            #     {"error": True, "error_message": f"HTTP error ocurred: {err}"}
            # )
        return result

    @api.model
    def autocomplete(self, query):
        if len(query) < 3:
            return []
        results = []
        if query.isdigit():
            data = self.enrich_company(None, query, None)
            if data:
                results.append(
                    {
                        "country_id": False,
                        "ignored": False,
                        "logo": False,
                        "name": data.get("name", ""),
                        "legal_name": False,
                        "partner_gid": data.get("company_registry", ""),
                        "duns": data.get("company_registry", ""),
                        "state_id": False,
                        "vat": data.get("vat", ""),
                        "website": data.get("company_registry", "")
                        + " | "
                        + data.get("city"),
                    }
                )
        else:
            try:
                url = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/vyhledat"
                json_data = {
                    "accept": "application/json",
                    "Content-Type": "application/json",
                    "start": 0,
                    "pocet": 5,
                    "obchodniJmeno": query,
                }
                session = requests.Session()
                response = session.post(url, json=json_data)
                response.raise_for_status()
                records = response.json()

                if "ekonomickeSubjekty" in records:
                    for record in records["ekonomickeSubjekty"]:
                        if not record.get("ico"):
                            continue
                        results.append(
                            {
                                "country_id": False,
                                "ignored": False,
                                "logo": False,
                                "name": f"{record.get('obchodniJmeno', '')},  {'sidlo' in record and 'nazevObce' in record['sidlo'] and record['sidlo']['nazevObce'] or '-'} ({record['ico']})",
                                "legal_name": False,
                                "partner_gid": record.get("ico", ""),
                                "duns": record.get("ico", ""),
                                "state_id": False,
                                "vat": record.get("dic", ""),
                                "website": record.get("ico", "")
                                + " | "
                                + record["sidlo"].get("nazevObce", ""),
                            }
                        )
                return results
            except HTTPError as http_err:
                print(f"HTTP error occurred: {http_err}")
                _logger.info(f"HTTP error occurred: {http_err}")
            except KeyError as key_err:
                # do nothing - there was no answer part probably
                _logger.info(f"Key error occurred: {key_err}")
                pass
            except Exception as err:
                print(f"Other error occurred: {err}")
                _logger.info(f"Other error occurred: {err}")
        return results
