/** @odoo-module **/
// Copyright 2026 Data Dance s.r.o.
// Data Dance Proprietary License v1.0 — see the LICENSE file.

import { registry } from "@web/core/registry";

/**
 * Pick an ARES suggestion on a new company contact, the way a user does.
 *
 * This is the path that crashed with "Cannot read properties of undefined
 * (reading 'type')" when the dispatcher's own handler passed suggestion keys
 * that are not form fields to record.update(). The provider is mocked by
 * TestAresPickTour; the tour only drives the browser.
 */
registry.category("web_tour.tours").add("partner_autocomplete_ares_pick", {
    url: "/odoo/action-base.action_partner_form/new",
    steps: () => [
        {
            content: "The name field only autocompletes for companies",
            trigger: '.o_field_widget[name="company_type"] input[data-value="company"]',
            run: "click",
        },
        {
            content: "Type the company name",
            trigger: '.o_field_widget[name="name"] input',
            run: "edit Vzorová",
        },
        {
            content: "Pick the ARES suggestion",
            trigger: '.o-autocomplete--dropdown-item:contains("Vzorová CZ s.r.o.")',
            run: "click",
        },
        {
            content: "The register's answer filled the form",
            trigger: '.o_field_widget[name="vat"] input:value("CZ12345678")',
        },
        {
            content: "Many2one filled too",
            trigger: '.o_field_widget[name="country_id"] input:value("Czech Republic")',
        },
        {
            content: "Core saves the record after the pick",
            trigger: ".o_form_saved",
        },
    ],
});
