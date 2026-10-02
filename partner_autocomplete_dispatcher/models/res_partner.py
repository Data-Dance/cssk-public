# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Command

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    partner_gid = fields.Char("Company database ID")

    partner_autocomplete_provider = fields.Char(
        "Partner Autocomplete Provider",
    )

    import_enrich_company = fields.Char(
        "Import Enrich Company",
        inverse="_inverse_import_enrich_company",
        store=False,
        default=False,
    )

    def _inverse_import_enrich_company(self):
        # The inverse runs on EVERY create, not only on an import: the field's
        # default puts it into the create values. Without this filter, saving
        # a new company with an IČO looked it up in the register — overwriting
        # the name and address the user had just typed, or, with no answer,
        # warning them about a lookup they never asked for.
        imported = self.filtered("import_enrich_company")
        if imported:
            imported._update_partner_info()

    def _autocomplete_lookup_key(self):
        """The registry number this partner may be looked up by, or "".

        Every provider here searches a **company** register by IČO, so the key
        has to be a number that identifies *this* record. Two of the three
        candidates always do; the third does not, and that is the whole reason
        this method exists:

        * ``partner_gid`` — set only by the autocomplete dropdown, so it is
          this record's own.
        * ``import_enrich_company`` — supplied deliberately by an import.
        * ``company_registry`` — **not necessarily this record's**. Core lists
          it in ``res.partner._commercial_fields()``, so every contact under a
          company is given its parent's number automatically. Looking that up
          fetches the *company* and would overwrite the person's name, street
          and VAT number with it.

        So the fallback applies only where the number can be the record's own:
        a partner with no parent, or one that is itself a company. That still
        covers the case the fallback was added for — a hand-typed or migrated
        company — and it keeps sole traders working, who are ``person`` records
        with a real IČO and no parent.

        Returns "" when there is nothing to look up, and the caller must then
        not call the provider at all: a register asked for an empty number
        answers with an error, which costs a paid API call and reads exactly
        like "this company is not in the register".
        """
        self.ensure_one()
        key = self.partner_gid or self.import_enrich_company
        if not key and (self.is_company or not self.parent_id):
            key = self.company_registry
        return (key or "").strip()

    def _update_partner_info(self):
        """Enrich each partner from the configured provider.

        Reports a summary at the end, and counts three outcomes rather than
        two. Every provider here reads a rate-limited register — ORSF allows 30
        full-record reads a minute — so a bulk run stops returning data partway
        through, and without a count that is indistinguishable from the
        partners simply not being in the register. For a large selection use
        the provider's own bulk action instead.
        """
        enriched = 0
        empty = 0
        failed = 0
        skipped = 0
        for partner in self:
            key = partner._autocomplete_lookup_key()
            if not key:
                # Not an error and not an empty answer: there was no question
                # to ask. Counted separately so the notification can say so,
                # and skipped before the HTTP call so it costs nothing.
                skipped += 1
                _logger.debug(
                    "partner autocomplete: no lookup key for %s (id %s), skipped",
                    partner.display_name,
                    partner.id,
                )
                continue
            model = self.env.get(
                partner.partner_autocomplete_provider, None
            ) or self.env.get(self.env.company.partner_autocomplete_provider, None)
            if model is None:
                raise UserError(
                    f"The provider ({partner.partner_autocomplete_provider}) is not installed."
                )
            try:
                data = model.enrich_company(
                    vat="",
                    partner_gid=key,
                    company_domain="",
                )
                if data:
                    partner.write(self._process_partner_data(data))
                    enriched += 1
                else:
                    empty += 1
            except Exception as e:
                failed += 1
                _logger.warning(
                    f"Error while updating partner info: {partner.name} ({e})"
                )
        if len(self) > 1 or empty or failed or skipped:
            self._notify_update_partner_info(enriched, empty, failed, skipped)
        return True

    def _notify_update_partner_info(self, enriched, empty, failed, skipped=0):
        parts = [_("%s updated", enriched)]
        if skipped:
            parts.append(_("%s skipped", skipped))
        if empty:
            parts.append(_("%s with no data returned", empty))
        if failed:
            parts.append(_("%s failed", failed))
        message = ", ".join(parts)
        # One sentence per outcome, because the three have different causes and
        # a single catch-all explanation sends people looking in the wrong
        # place. "Skipped" in particular used to be reported as "no data
        # returned", which reads as a register problem when nothing was asked.
        if skipped:
            message += _(
                ". Skipped means no company number to search by — a contact "
                "inside a company is looked up through the company itself."
            )
        if empty:
            message += _(
                ". A register that answers nothing is usually a rate limit on a "
                "large selection, or a company it does not hold — the server log "
                "distinguishes them."
            )
        if failed:
            message += _(". Failures are in the server log with their cause.")
        self.env.user._bus_send("simple_notification", {
            "type": "success" if enriched and not failed else "warning",
            "title": _("Partner update"),
            "message": message,
        })

    def _process_partner_data(self, data):
        if "child_ids" in data:
            existing_partners = self.env["res.partner"].search([]).mapped("name")
            for child in data["child_ids"]:
                if isinstance(child[2], dict):
                    if child[0].value == 0 and "country_id" in child[2]:
                        child[2]["country_id"] = child[2]["country_id"].get("id", "")

            data["child_ids"] = [
                i
                for i in data["child_ids"]
                if isinstance(i[2], dict)
                and i[2].get("name", False) not in existing_partners
            ]
        if "bank_ids" in data:
            existing_acc_numbers = (
                self.env["res.partner.bank"].search([]).mapped("sanitized_acc_number")
            )
            bank_ids = []
            for bank in data["bank_ids"]:
                if (
                    isinstance(bank[2], dict)
                    and bank[2]["acc_number"] not in existing_acc_numbers
                ):
                    if "bank_id" in bank[2] and bank[2]["bank_id"]:
                        bank_id = bank[2]["bank_id"].get("id", False)
                        bank[2]["bank_id"] = bank_id
                    bank_ids.append(bank)
            data["bank_ids"] = bank_ids

        if "country_id" in data and data["country_id"] and "id" in data["country_id"]:
            data["country_id"] = data["country_id"].get("id", "")
        if (
            "industry_id" in data
            and data["industry_id"]
            and "id" in data["industry_id"]
        ):
            data["industry_id"] = data["industry_id"].get("id", "")
        if "state_id" in data and data["state_id"] and "id" in data["state_id"]:
            data["state_id"] = data["state_id"].get("id", "")
        return data

    @api.model
    def default_get(self, default_fields):
        new_context = self.prepare_new_context()
        if new_context:
            return super().with_context(**new_context).default_get(default_fields)
        return super().default_get(default_fields)

    def prepare_new_context(self):
        new_context = {}
        fields = ["default_bank_ids", "default_child_ids"]

        def process_context_data(key):
            if (
                key in self.env.context
                and "operation" in self.env.context[key]
                and self.env.context[key]["operation"] == "MULTI"
            ):
                try:
                    new_data = [
                        Command.create(i["data"])
                        for i in self.env.context[key]["commands"]
                        if i["operation"] == "CREATE"
                    ]
                    new_context[key] = new_data
                except Exception as e:
                    pass

        for field in fields:
            process_context_data(field)

        return new_context

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        onchange_methods = self.env["res.partner.bank"]._onchange_methods
        if "acc_number" in onchange_methods:
            for partner in res:
                for account in partner.bank_ids:
                    for method in onchange_methods["acc_number"]:
                        method(account)
        return res

    # New methods after DnB
    @api.model
    def _autocomplete_provider_for(self, country_code=None):
        """The provider to ask about a partner in ``country_code``.

        A provider that declares the country (``_autocomplete_country_codes``)
        wins; otherwise the company's own choice. With two companies in two
        countries sharing contacts, a per-company choice alone meant the Slovak
        company could not autocomplete a Czech partner, and the other way
        round.
        """
        if country_code:
            registry = self.env["partner.autocomplete.provider.registry"]
            for name, _label in registry._get_available_providers():
                model = self.env.get(name)
                if model is not None and country_code in (
                    model._autocomplete_country_codes()
                ):
                    return name
        return self.env.company.partner_autocomplete_provider

    @api.model
    def _autocomplete_country_code(self, query_country_id=None, vat=None):
        if query_country_id:
            country = self.env["res.country"].browse(query_country_id).exists()
            if country:
                return country.code
        prefix = (vat or "").strip()[:2].upper()
        if len(prefix) == 2 and prefix.isalpha():
            # Greece's VAT prefix is EL, not its ISO code.
            return "GR" if prefix == "EL" else prefix
        return None

    @api.model
    def _autocomplete_stamp(self, provider, suggestions):
        """Remember which provider produced each suggestion.

        Core's widget passes the picked suggestion back to ``enrich_by_duns``
        as ``enriched_company_data``, and that is the only way to send the
        enrichment to the register it came from: a Czech and a Slovak IČO are
        both eight digits.
        """
        for suggestion in suggestions or []:
            if isinstance(suggestion, dict):
                suggestion.setdefault("partner_autocomplete_provider", provider)
        return suggestions

    @api.model
    def autocomplete_by_name(self, query, query_country_id, timeout=15):
        provider = self._autocomplete_provider_for(
            self._autocomplete_country_code(query_country_id))
        if provider == "partner.autocomplete.provider":
            return super().autocomplete_by_name(query, query_country_id, timeout)
        return self._autocomplete_stamp(
            provider, self.env[provider].autocomplete(query))

    @api.model
    def autocomplete_by_vat(self, vat, query_country_id, timeout=15):
        provider = self._autocomplete_provider_for(
            self._autocomplete_country_code(query_country_id, vat))
        if provider == "partner.autocomplete.provider":
            return super().autocomplete_by_vat(vat, query_country_id, timeout)
        return self._autocomplete_stamp(
            provider, self.env[provider].read_by_vat(vat))

    @api.model
    def enrich_by_duns(self, duns, timeout=15):
        picked = self.env.context.get("enriched_company_data") or {}
        provider = (
            isinstance(picked, dict) and picked.get("partner_autocomplete_provider")
        )
        if not provider or self.env.get(provider) is None:
            provider = self.env.company.partner_autocomplete_provider
        if provider == "partner.autocomplete.provider":
            return super().enrich_by_duns(duns, timeout)
        return self.env[provider].enrich_company(
            None,
            duns,
            None,
        )
