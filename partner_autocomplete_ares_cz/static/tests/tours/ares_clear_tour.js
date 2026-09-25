/** @odoo-module **/
// Copyright 2026 Data Dance s.r.o.
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import { registry } from "@web/core/registry";

/**
 * Re-pick a register suggestion on an EXISTING company whose answer replaces
 * a one2many with `[Command.clear(), Command.create(...)]`, then save.
 *
 * The CLEAR must reach the server. The provider is mocked by
 * TestAresClearTour, which also asserts what was saved.
 */
registry.category("web_tour.tours").add("partner_autocomplete_ares_clear", {
    steps: () => [
        {
            content: "The company already lists its old contact",
            trigger: '.o_field_widget[name="child_ids"]:contains("Old Contact")',
        },
        {
            content: "Type the company name",
            trigger: '.o_field_widget[name="name"] input',
            run: "edit Durwen",
        },
        {
            content: "Pick the ARES suggestion",
            trigger: '.o-autocomplete--dropdown-item:contains("Durwen CZ s.r.o.")',
            run: "click",
        },
        {
            content: "The register's contacts replaced the old one on screen",
            trigger: '.o_field_widget[name="child_ids"]:contains("New Contact"):not(:contains("Old Contact"))',
        },
        {
            content: "Save",
            trigger: ".o_form_button_save",
            run: "click",
        },
        {
            content: "Saved",
            trigger: ".o_form_saved",
        },
    ],
});
