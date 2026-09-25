/** @odoo-module **/
/*
    Copyright 2022 Data Dance s.r.o.
    License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

import { x2ManyCommands } from "@web/core/orm_service";
import { patch } from "@web/core/utils/patch";
import { StaticList } from "@web/model/relational_model/static_list";

/**
 * Teach StaticList the CLEAR command (5).
 *
 * A provider that replaces a partner's bank accounts sends
 * `[Command.clear(), Command.create({...})]`. `Record._preprocessX2manyChanges`
 * hands every command that is not SET to `StaticList._applyCommands`, whose
 * switch has no CLEAR case — so the clear is silently dropped and the new lines
 * are appended to the old ones instead of replacing them.
 *
 * CLEAR is rewritten into commands core does know: UNLINK for every saved row
 * and DELETE for every row not saved yet (an UNLINK of a virtual id would be
 * sent to the server as is). Core records those, so `_getCommands()` sends
 * them on save. The previous version emptied `records`, `_currentIds` and
 * `_commands` directly instead: the rows vanished from the form, but the list
 * only ever sends what `_commands` holds, so nothing reached the server and
 * the old rows were still attached after the save. On a one2many, UNLINK and
 * CLEAR do the same thing server-side — the inverse many2one is emptied, or
 * the row deleted where it cascades — and on a many2many both drop the link.
 *
 * Before that, this was a full copy of core's `_applyCommands` with a CLEAR
 * branch added. That copy went stale: by 19.0 it had lost the LINK
 * de-duplication against `_currentIds` (duplicated rows), still called
 * `_parseServerValues(changes, record.data)` after core moved the second
 * argument to an options object `{ currentValues }` (so current values were
 * silently dropped), and pinned an older `_currentIds.splice` index.
 *
 * Handling only the command core does not know about, and delegating the rest,
 * is what keeps that from happening again.
 */
patch(StaticList.prototype, {
    _applyCommands(commands, options) {
        const { CLEAR, DELETE, UNLINK } = x2ManyCommands;
        const clearIndex = commands.findIndex((command) => command[0] === CLEAR);
        if (clearIndex === -1) {
            // Untouched path: same return value and same sync/async shape as
            // core, which some callers rely on by not awaiting it.
            return super._applyCommands(commands, options);
        }

        // Commands are positional: whatever precedes the CLEAR is applied
        // first, so the rows it adds are cleared too, and the removals are
        // computed only then. Whatever follows goes through this method again,
        // which handles a payload with more than one CLEAR.
        const after = commands.slice(clearIndex + 1);
        const applyClear = () => {
            const removals = this._currentIds.map((id) =>
                typeof id === "number" ? [UNLINK, id] : [DELETE, id]
            );
            return this._applyCommands([...removals, ...after], options);
        };
        const before = commands.slice(0, clearIndex);
        if (before.length) {
            return Promise.resolve(super._applyCommands(before, options)).then(applyClear);
        }
        return applyClear();
    },
});
