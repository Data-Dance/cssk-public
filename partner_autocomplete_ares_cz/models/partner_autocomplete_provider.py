# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from datetime import datetime

import requests
from odoo import Command, _, api, fields, models
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

    @api.model
    def _autocomplete_country_codes(self):
        return ("CZ",)

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

    ARES_RES_BASE = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty-res"

    ARES_VR_BASE = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty-vr"

    #: Mapping parameter -> partner field it points at by default, when that
    #: field exists (it lives in a module this one does not depend on).
    DEFAULT_MAPPINGS = {
        "ares_cz.mapping.nace": "nace_code",
        "ares_cz.mapping.register": "l10n_cz_register_name",
        "ares_cz.mapping.register_office": "l10n_cz_register_office",
        "ares_cz.mapping.register_number": "l10n_cz_register_number",
        "ares_cz.mapping.status": "l10n_cz_register_status",
        "ares_cz.mapping.established_date": "l10n_cz_established_on",
        "ares_cz.mapping.dissolved_date": "l10n_cz_dissolved_on",
    }

    #: The mappings that need the subject's entry in the veřejný rejstřík,
    #: which is one more request.
    VR_MAPPINGS = (
        "ares_cz.mapping.register",
        "ares_cz.mapping.register_office",
        "ares_cz.mapping.register_number",
    )

    #: ARES's ``TypRejstriku`` codelist: the six veřejné rejstříky.
    VR_REGISTERS = {
        "OR": "Obchodní rejstřík",
        "SR": "Spolkový rejstřík",
        "NR": "Nadační rejstřík",
        "RU": "Rejstřík ústavů",
        "RSVJ": "Rejstřík společenství vlastníků jednotek",
        "ROPS": "Rejstřík obecně prospěšných společností",
    }

    #: ARES's ``SoudVr`` codelist: the rejstříkové soudy. A spisová značka
    #: names the court itself, never one of its pobočky.
    VR_COURTS = {
        "MSPH": "Městský soud v Praze",
        "KSCB": "Krajský soud v Českých Budějovicích",
        "KSPL": "Krajský soud v Plzni",
        "KSUL": "Krajský soud v Ústí nad Labem",
        "KSHK": "Krajský soud v Hradci Králové",
        "KSBR": "Krajský soud v Brně",
        "KSOS": "Krajský soud v Ostravě",
    }

    #: ``cinnosti`` of a veřejný rejstřík entry -> the kind of activity row.
    VR_ACTIVITY_KINDS = (
        ("predmetPodnikani", "business"),
        ("predmetCinnosti", "activity"),
        ("doplnkovaCinnost", "secondary"),
        ("ucel", "purpose"),
    )

    @api.model
    def _ares_apply_default_mappings(self):
        """Point unset mappings at their default field where it exists."""
        ICP = self.env["ir.config_parameter"].sudo()
        for parameter, field_name in self.DEFAULT_MAPPINGS.items():
            if ICP.get_param(parameter):
                continue
            field = self.env["ir.model.fields"].sudo().search(
                [("model", "=", "res.partner"), ("name", "=", field_name)], limit=1)
            if field:
                ICP.set_param(parameter, str(field.id))

    @api.model
    def _ares_prevailing_nace(self, ico):
        """The subject's prevailing activity in CZ-NACE 2025, from ARES's copy
        of the statistical register (RES), or ``""``.

        The basic ARES record lists activities without saying which one
        prevails; RES does (``czNacePrevazujici``, the 2025 classification
        that tax filings use from 1. 1. 2026). One extra request, so it is
        made only when a field is mapped to receive it.
        """
        try:
            response = requests.get(
                f"{self.ARES_RES_BASE}/{ico}", timeout=self.ARES_TIMEOUT,
                headers={"Accept": "application/json"})
            if response.status_code != 200:
                return ""
            records = response.json().get("zaznamy") or []
        except (RequestException, ValueError, AttributeError) as err:
            _logger.info("ARES RES request for %s failed: %s", ico, err)
            return ""
        primary = next((r for r in records if r.get("primarniZaznam")),
                       records[0] if records else {})
        return primary.get("czNacePrevazujici") or ""

    @api.model
    def _ares_public_register(self, ico):
        """The subject's entry in the veřejný rejstřík.

        ARES answers with one record per register the IČO was ever entered
        in; the primary one is the entry in force. ``{}`` when the subject is
        in no public register (a živnostník, say: ARES answers 404, which is
        an answer and not an error), ``None`` when ARES could not be asked —
        the caller must not take that for "nothing entered".
        """
        try:
            response = requests.get(
                f"{self.ARES_VR_BASE}/{ico}", timeout=self.ARES_TIMEOUT,
                headers={"Accept": "application/json"})
            if response.status_code == 404:
                return {}
            if response.status_code != 200:
                return None
            records = response.json().get("zaznamy") or []
        except (RequestException, ValueError, AttributeError) as err:
            _logger.info("ARES VR request for %s failed: %s", ico, err)
            return None
        records = [r for r in records if isinstance(r, dict)]
        return next((r for r in records if r.get("primarniZaznam")),
                    records[0] if records else {})

    @api.model
    def _ares_current(self, items):
        """The entry in force among a veřejný rejstřík list: the last one
        that has not been deleted (``datumVymazu``)."""
        live = [i for i in items or [] if isinstance(i, dict) and not i.get("datumVymazu")]
        return live[-1] if live else {}

    @api.model
    def _ares_register_values(self, record, entry):
        """Register coordinates, status and dates as ``{mapping: value}``.

        ``record`` is the basic ARES record, ``entry`` the veřejný rejstřík
        one (``{}`` when it was not asked for or the subject has none).
        Codes are spelled out from ARES's own codelists; a code that is not
        in them yields nothing rather than a code in a text field.
        """
        sources = record.get("seznamRegistraci") or {}
        znacka = self._ares_current(entry.get("spisovaZnacka"))
        register = self.VR_REGISTERS.get(entry.get("rejstrik") or "", "")
        if not entry and sources.get("stavZdrojeRzp") in (
                "AKTIVNI", "POZASTAVENY") and sources.get(
                "stavZdrojeVr") in (None, "NEEXISTUJICI"):
            # In no public register, but in the živnostenský rejstřík: the
            # "jiná evidence" such a subject states on its documents.
            register = "Živnostenský rejstřík"
        number = ""
        if znacka.get("oddil") and znacka.get("vlozka"):
            number = f"{znacka['oddil']} {znacka['vlozka']}"
        # The status of the register the subject is entered in: the public
        # register if it is in one, else the živnostenský rejstřík, else the
        # registr osob. "NEEXISTUJICI" says the source holds no such subject.
        status = next(
            (code for code in (
                entry.get("stavSubjektu"), sources.get("stavZdrojeVr"),
                sources.get("stavZdrojeRzp"), sources.get("stavZdrojeRos"))
             if code and code != "NEEXISTUJICI"),
            "")
        partner = self.env["res.partner"]
        if status and hasattr(partner, "_l10n_cz_parse_register_status"):
            status = partner._l10n_cz_parse_register_status(status, status)
        return {
            "ares_cz.mapping.register": register,
            "ares_cz.mapping.register_office": self.VR_COURTS.get(znacka.get("soud") or "", ""),
            "ares_cz.mapping.register_number": number,
            "ares_cz.mapping.status": status,
            "ares_cz.mapping.established_date": record.get("datumVzniku"),
            "ares_cz.mapping.dissolved_date": record.get("datumZaniku"),
        }

    @api.model
    def _ares_register_lists(self, result, entry, partner_fields):
        """Mirror the entry's scope of business and its previous names and
        seats, where ``l10n_cz_trade_registry`` gives them somewhere to go.

        ``Command.clear()`` first: these are what the register says today,
        not an accumulating log, and re-enriching must not double every row.
        """
        if "l10n_cz_activity_ids" in partner_fields:
            rows = []
            activities = entry.get("cinnosti")
            activities = activities if isinstance(activities, dict) else {}
            for key, kind in self.VR_ACTIVITY_KINDS:
                for item in activities.get(key) or []:
                    if not isinstance(item, dict) or not item.get("hodnota"):
                        continue
                    rows.append(Command.create({
                        "kind": kind,
                        # The register breaks lines at a fixed width.
                        "name": " ".join(str(item["hodnota"]).split()),
                        "valid_from": self._ares_date(item.get("datumZapisu")),
                        "valid_to": self._ares_date(item.get("datumVymazu")),
                        "source": "ARES VR",
                    }))
            result["l10n_cz_activity_ids"] = [Command.clear()] + rows
        if "l10n_cz_history_ids" in partner_fields:
            rows = []
            for item in entry.get("obchodniJmeno") or []:
                if isinstance(item, dict) and item.get("datumVymazu") and item.get("hodnota"):
                    rows.append(Command.create({
                        "kind": "name",
                        "value": item["hodnota"],
                        "valid_from": self._ares_date(item.get("datumZapisu")),
                        "valid_to": self._ares_date(item.get("datumVymazu")),
                    }))
            for item in entry.get("adresy") or []:
                if not isinstance(item, dict) or not item.get("datumVymazu"):
                    continue
                address = item.get("adresa")
                value = address.get("textovaAdresa") if isinstance(address, dict) else ""
                if value:
                    rows.append(Command.create({
                        "kind": "address",
                        "value": value,
                        "valid_from": self._ares_date(item.get("datumZapisu")),
                        "valid_to": self._ares_date(item.get("datumVymazu")),
                    }))
            result["l10n_cz_history_ids"] = [Command.clear()] + rows
        return result

    @api.model
    def _ares_date(self, value):
        try:
            return datetime.strptime(str(value or "")[:10], "%Y-%m-%d").date()
        except ValueError:
            return False

    @api.model
    def _ares_enrich_register(self, result, record):
        """Add what ``l10n_cz_trade_registry`` stores, where it is installed
        or a mapping was pointed elsewhere by hand. Feature detection rather
        than a dependency: this stays a Tools module."""
        ICP = self.env["ir.config_parameter"].sudo()
        partner_fields = self.env["res.partner"]._fields
        wants_lists = "l10n_cz_register_checked_on" in partner_fields
        wants_entry = wants_lists or any(ICP.get_param(p) for p in self.VR_MAPPINGS)
        entry = self._ares_public_register(record["ico"]) if wants_entry else None
        values = self._ares_register_values(record, entry or {})
        self._enrich_dynamic_mapping(result, list(values.items()))
        if wants_lists:
            # Records *when we asked*, which is what separates "the register
            # holds nothing" from "we never looked".
            result["l10n_cz_register_checked_on"] = fields.Datetime.now()
            if entry is not None:
                self._ares_register_lists(result, entry, partner_fields)
        return result

    @api.model
    def _ares_lookup_probe(self, ico):
        """Named to match ORSF's, so the verification layer can treat the two
        providers identically instead of special-casing each."""
        return self._ares_probe(ico)

    @api.model
    def read_by_vat(self, vat):
        """Suggest the company behind a Czech DIČ.

        ARES has no search by DIČ, but a legal person's DIČ is ``CZ`` + its
        IČO, so an eight-digit DIČ is looked up as an IČO and offered only if
        ARES confirms that very DIČ for it. A ten-digit DIČ (a natural person,
        derived from the birth number) has no IČO to try and finds nothing.

        Returns a list of suggestions; it used to return ``[{}]``, a single
        empty suggestion the widget then offered as a nameless row.
        """
        digits = (vat or "").replace(" ", "").upper()
        if digits.startswith("CZ"):
            digits = digits[2:]
        if len(digits) != 8 or not digits.isdigit():
            return []
        data = self.enrich_company(None, digits, None)
        if not data.get("name") or (data.get("vat") or "").replace(" ", "").upper() != "CZ" + digits:
            return []
        return [self._ares_suggestion(data, digits)]

    @api.model
    def _ares_suggestion(self, data, ico):
        """A dropdown suggestion for one enriched ARES record.

        ``partner_gid``/``duns`` carry the IČO the suggestion was found by:
        picking it sends that number back to :meth:`enrich_company`. They
        used to read ``company_registry`` from the enrichment, which exists
        only when the IČO mapping points at that very field, so with any
        other setting the picked suggestion enriched nothing.
        """
        return {
            "country_id": False,
            "ignored": False,
            "logo": False,
            "name": data.get("name", ""),
            "legal_name": False,
            "partner_gid": ico,
            "duns": ico,
            "state_id": False,
            "vat": data.get("vat", ""),
            # A subject with no seat in ARES has no city: "" rather than a
            # TypeError on ``str + None``.
            "website": f"{ico} | {data.get('city') or ''}",
            "partner_autocomplete_provider": self._name,
        }

    @api.model
    def _enrich_dynamic_mapping(self, result, mapping):
        for parameter, value in mapping:
            field = self.env["ir.config_parameter"].sudo().get_param(parameter)
            field = self.env["ir.model.fields"].sudo().browse(int(field)).exists()
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
            if record.get("ico") and self.env["ir.config_parameter"].sudo().get_param(
                    "ares_cz.mapping.nace"):
                mapping_pairs.append((
                    "ares_cz.mapping.nace",
                    self._ares_prevailing_nace(record["ico"])))
            self._enrich_dynamic_mapping(result, mapping_pairs)
            if record.get("ico"):
                self._ares_enrich_register(result, record)

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
            if data and data.get("name"):
                results.append(self._ares_suggestion(data, query))
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
                                + ((record.get("sidlo") or {}).get("nazevObce") or ""),
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
