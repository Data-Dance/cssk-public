/** @odoo-module **/
/*
    Copyright 2022 Data Dance s.r.o.
    License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

import { PartnerAutoCompleteCharField } from '@partner_autocomplete/js/partner_autocomplete_fieldchar';
import { deserializeDate, deserializeDateTime } from "@web/core/l10n/dates";
import { patch } from "@web/core/utils/patch";

/**
 * Core 18.0's `onSelect` already does everything a register answer needs:
 * enriches through `enrich_by_duns` (which the dispatcher routes to the
 * company's provider), turns the many2ones into `[id, display_name]` pairs,
 * drops every key that is not a field of the form, and updates the record.
 * So this patch leaves `onSelect` alone and only wraps `getCreateData`, the
 * one step whose output needs more than core gives it. Copying the handler
 * instead is what this module used to do, and the copy patched
 * `onSelectPartnerAutocompleteOption` — 19.0's name for it, which 18.0 never
 * calls.
 *
 * Two additions, both about what core cannot know:
 *
 * **Top-level dates become luxon objects.** `record.update()` ->
 * `Record._update()` -> `Record._applyChanges()` writes each value into
 * `record.data` verbatim; nothing parses it on the way. The IAP provider never
 * returns a date, our providers map some. x2many command payloads are left as
 * they are: `StaticList._applyCommands()` builds a `Record` from each CREATE
 * payload, and that constructor *does* run `_parseServerValues`, so the
 * server-format strings the provider sends are exactly what it wants.
 *
 * **No Dun & Bradstreet chatter card for a register answer.** Core posts one
 * after saving whenever the enrichment did not error. Its template renders
 * D&B's fields (entity type, UNSPSC codes, ...), which no register returns.
 */
patch(PartnerAutoCompleteCharField.prototype, {
    setup() {
        super.setup(...arguments);
        const partnerAutocomplete = this.partnerAutocomplete;
        this.partnerAutocomplete = {
            ...partnerAutocomplete,
            getCreateData: async (company) => {
                const data = await partnerAutocomplete.getCreateData(company);
                if (!data?.company) {
                    return data;
                }
                const provider = data.company.partner_autocomplete_provider;
                if (provider && provider !== "partner.autocomplete.provider") {
                    data.isEnrichAccessible = false;
                }
                for (const [fieldName, value] of Object.entries(data.company)) {
                    const field = this.props.record.fields[fieldName];
                    // Unknown fields are core's to drop. Empty values stay as
                    // they are: deserializeDate() throws on false/null.
                    if (!field || !value) {
                        continue;
                    }
                    if (field.type === "date") {
                        data.company[fieldName] = deserializeDate(value);
                    } else if (field.type === "datetime") {
                        data.company[fieldName] = deserializeDateTime(value);
                    }
                }
                return data;
            },
        };
    },
});
