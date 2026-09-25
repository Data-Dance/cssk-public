# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from datetime import datetime

import requests
from odoo import _, api, models
from requests.exceptions import HTTPError, RequestException

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

    #: ARES answers a miss with 404 and ``{"kod": "NENALEZENO"}``.
    ARES_BASE = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty"
    ARES_TIMEOUT = 15

    @api.model
    def _ares_probe(self, ico):
        """GET one company and say *why* it did not answer — ``(outcome, body)``.

        The counterpart of ORSF's ``_orsf_probe``, and it exists for the same
        reason: ``enrich_company`` below swallows every exception into an empty
        dict, so it cannot tell "no such company" from "ARES is down". A gate
        built on that distinction would be silently wrong.

        ``("ok", {...})`` the register answered; ``("absent", None)`` it holds
        no such subject; ``("unavailable", None)`` we could not ask.
        """
        try:
            response = requests.get(
                f"{self.ARES_BASE}/{ico}",
                timeout=self.ARES_TIMEOUT,
                headers={"Accept": "application/json"},
            )
        except RequestException as err:
            _logger.info("ARES request for %s failed: %s", ico, err)
            return "unavailable", None
        if response.status_code == 404:
            return "absent", None
        if response.status_code != 200:
            _logger.info("ARES returned HTTP %s for %s", response.status_code, ico)
            return "unavailable", None
        try:
            body = response.json()
        except ValueError:
            _logger.info("ARES returned a non-JSON body for %s", ico)
            return "unavailable", None
        if not isinstance(body, dict):
            return "unavailable", None
        # A 200 carrying `kod` is an error object, not a company. Treating it
        # as a hit would hand the caller a record with no name.
        if body.get("kod"):
            return ("absent" if body["kod"] == "NENALEZENO" else "unavailable"), None
        return "ok", body

    @api.model
    def _ares_lookup_probe(self, ico):
        """Named to match ORSF's, so the verification layer can treat the two
        providers identically instead of special-casing each."""
        return self._ares_probe(ico)

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
