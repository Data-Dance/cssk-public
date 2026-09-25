/** @odoo-module **/
/*
    Copyright 2026 Data Dance s.r.o.
    License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { Component, useRef, useState } from "@odoo/owl";

/**
 * The whole VIES control: a *Check now* button, and a green tick / red cross
 * for the answer.
 *
 * It replaces the plain `<button type="object">` because that button could only
 * run the check — a server call has no way to activate a notebook tab, so it
 * could not then show you the answer it just fetched. Doing both from one
 * component is what lets a single click validate the number and put the
 * evidence in front of you.
 *
 * The detail — consultation number, request date, the name and address VIES
 * holds — lives on the VIES page. Only the action and its verdict stay beside
 * the VAT number.
 */
export class ViesStatusBadge extends Component {
    static template = "l10n_cssk_vies.ViesStatusBadge";
    static props = { ...standardFieldProps };

    setup() {
        this.orm = useService("orm");
        this.state = useState({ busy: false });
        // The button is re-rendered when the record reloads after the check, so
        // a click event's target is detached by the time we want to find the
        // notebook. A ref always points at the node currently in the DOM.
        this.rootRef = useRef("root");
    }

    get checked() {
        return Boolean(this.props.record.data.vies_check_date);
    }

    get valid() {
        return Boolean(this.props.record.data[this.props.name]);
    }

    get title() {
        if (!this.checked) {
            return _t("Not checked against VIES yet");
        }
        return this.valid
            ? _t("Valid in VIES — open the VIES tab")
            : _t("Not valid in VIES — open the VIES tab");
    }

    /**
     * Run the check, refresh the record, then show the evidence.
     *
     * The record is saved first because the check is a server call against a
     * stored partner: an unsaved one has no id to check.
     */
    async checkNow() {
        if (this.state.busy) {
            return;
        }
        this.state.busy = true;
        try {
            const record = this.props.record;
            // Save ALWAYS, not only when the partner is new. The check is a
            // server call against the STORED vat, and `record.load()` below
            // reloads from the database — so on an existing partner whose VAT
            // had just been edited, the old guard skipped the save, queried
            // VIES for the previous number, stamped that consultation number,
            // and then silently reverted the typed edit under a green tick.
            // On a clean record `save()` is a no-op.
            if (!(await record.save())) {
                return;
            }
            await this.orm.call("res.partner", "action_vies_check_direct", [
                [record.resId],
            ]);
            await record.load();
            this.openViesPage();
        } finally {
            this.state.busy = false;
        }
    }

    onKeydown(ev) {
        // role="button" without this is a keyboard trap: focusable, announced
        // as a button, and doing nothing when pressed.
        if (ev.key === "Enter" || ev.key === " ") {
            ev.preventDefault();
            this.openViesPage();
        }
    }

    /**
     * Open the VIES page.
     *
     * A notebook page has no public API for being activated from outside, but
     * its tab is a plain `<a class="nav-link" name="...">` — the form compiler
     * copies a `<page name="...">` onto the slot, and Notebook renders it with
     * `t-att-name` — and that anchor's own click handler calls `activatePage`.
     * So clicking it is the route in.
     *
     * The tab is found by walking up the ancestors, which needs no
     * container-class assumption and scopes correctly for free: the first
     * ancestor holding a matching tab is this record's own form, so a record
     * opened in a dialog cannot activate the tab of the form behind it.
     *
     * A no-op when the page is not rendered.
     */
    openViesPage() {
        for (let node = this.rootRef.el; node; node = node.parentElement) {
            const tab = node.querySelector?.(
                '.o_notebook a.nav-link[name="vies_proof"]'
            );
            if (tab) {
                tab.click();
                return;
            }
        }
    }
}

export const viesStatusBadge = {
    component: ViesStatusBadge,
    displayName: _t("VIES Status"),
    supportedTypes: ["boolean"],
};

registry.category("fields").add("vies_status_badge", viesStatusBadge);
