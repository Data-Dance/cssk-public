/** @odoo-module **/
/*
    Copyright 2022 Data Dance s.r.o.
    License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

import { PartnerAutoCompleteCharField } from '@partner_autocomplete/js/partner_autocomplete_fieldchar';
import { deserializeDate, deserializeDateTime } from "@web/core/l10n/dates";
import { patch } from "@web/core/utils/patch";

/**
 * Core's own handler passes the provider's payload straight to
 * `record.update()`, which is fine for the IAP provider because it only ever
 * returns strings, numbers and many2ones. Our providers also map date fields
 * and can create one2many lines (bank accounts, child contacts), and those two
 * cases need opposite treatment — which is the entire reason this patch exists.
 *
 * **Top-level values are client-side values.** `record.update()` ->
 * `Record._update()` -> `Record._applyChanges()` writes each entry into
 * `record.data` verbatim; nothing calls `_parseServerValues` on the way. So a
 * date has to arrive as the luxon object the record holds, not as the
 * "YYYY-MM-DD" string the server sent, and that is what the loop below does.
 *
 * **x2many command payloads are server-side values.** `_update()` routes them
 * through `Record._preprocessX2manyChanges()` -> `StaticList._applyCommands()`
 * -> `_createRecordDatapoint(command[2])`, which builds a `Record` from that
 * dict and *does* run `_parseServerValues` on it. Server-format strings are
 * exactly what it wants — which is exactly what the provider already returns.
 * So the command payloads are deliberately left untouched.
 *
 * Many2one values are likewise passed through as the `{id, display_name}`
 * object the provider returns: `Record._completeMany2OneValue` reads `.id` and
 * `.display_name` off the value, and anything else resolves to `false`.
 */
patch(PartnerAutoCompleteCharField.prototype, {
    async onSelectPartnerAutocompleteOption(option) {
        let data = await this.partnerAutocomplete.getCreateData(option);
        if (!data?.company) {
            return;
        }

        if (data.logo) {
            const logoField = this.props.record.resModel === 'res.partner' ? 'image_1920' : 'logo';
            data.company[logoField] = data.logo;
        }

        // Deserialize date and datetime fields. Iterated with for..of rather
        // than forEach so that this stays ordered with respect to the update
        // below; the previous version used an async forEach callback, which is
        // never awaited, so its work could land after the record was updated.
        for (const [fieldName, value] of Object.entries(data.company)) {
            const field = this.props.record.fields[fieldName];
            // Skip unknown fields, and skip empty values: deserializeDate()
            // throws on false/null rather than returning it.
            if (!field || !value) {
                continue;
            }
            if (field.type === "date") {
                data.company[fieldName] = deserializeDate(value);
            } else if (field.type === "datetime") {
                data.company[fieldName] = deserializeDateTime(value);
            }
        }

        // Save UNSPSC codes (tags)
        const unspsc_codes = data.company.unspsc_codes

        // Delete useless fields before updating record
        data.company = this.partnerAutocomplete.removeUselessFields(data.company, Object.keys(this.props.record.fields));

        // Update record with retrieved values
        if (data.company.name) {
            await this.props.record.update({ name: data.company.name });  // Needed otherwise name it is not saved
        }
        await this.props.record.update(data.company);

        // Add UNSPSC codes (tags)
        if (this.props.record.resModel === 'res.partner' && unspsc_codes) {
            // We must first save the record so that we can then create the tags (many2many)
            const saved = await this.props.record.save();
            if (saved) {
                await this.props.record.load();
                await this.orm.call("res.partner", "iap_partner_autocomplete_add_tags", [this.props.record.resId, unspsc_codes]);
                await this.props.record.load();
            }
        }
        if (this.props.setDirty) {
            this.props.setDirty(false);
        }
    },

});
