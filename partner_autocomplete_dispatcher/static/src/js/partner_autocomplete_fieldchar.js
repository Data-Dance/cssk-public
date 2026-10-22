/** @odoo-module **/
/**
    Data Dance Proprietary License v1.0

    This software and associated files (the "Software") may only be used
    (executed, modified, executed after modifications) if you have
    purchased a valid license from Data Dance s.r.o.

    The above permissions are granted for a single database per purchased
    license. Furthermore, with a valid license it is permitted to use the
    software on other databases as long as the usage is limited to a testing
    or development environment.

    You may develop modules based on the Software or that use the Software
    as a library (typically by depending on it, importing it and using its
    resources), but without copying any source code or material from the
    Software. You may distribute those modules under the license of your
    choice, provided that this license is compatible with the terms of the
    Data Dance Proprietary License (For example: LGPL, MIT, or proprietary
    licenses similar to this one).

    It is forbidden to publish, distribute, sublicense, or sell copies of
    the Software or modified copies of the Software.

    The above copyright notice and this permission notice must be included
    in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
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
