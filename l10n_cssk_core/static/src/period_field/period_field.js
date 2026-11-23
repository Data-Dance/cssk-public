import { Component, useState } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { useDropdownState } from "@web/core/dropdown/dropdown_hooks";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

const { DateTime } = luxon;

/**
 * A tax period picked in one control: a month or a quarter of a year.
 *
 * Bound to the DATE the period starts on. Whether months or quarters are
 * offered comes from a sibling selection field (`period_type_field`, value
 * `month` / `quarter`). The core date picker can be limited to months
 * (`min_precision`), but it still shows a day ("1 Oct 2026") and knows no
 * quarters; a statutory period is named "October 2026" or "Q4 2026", and
 * that is what this shows and offers.
 */
export class CsskPeriodField extends Component {
    static template = "l10n_cssk_core.PeriodField";
    static components = { Dropdown };
    static props = {
        ...standardFieldProps,
        periodTypeField: { type: String, optional: true },
    };
    static defaultProps = { periodTypeField: "period_type" };

    setup() {
        this.dropdown = useDropdownState();
        this.state = useState({ year: DateTime.local().year });
    }

    get value() {
        return this.props.record.data[this.props.name] || null;
    }

    get isQuarter() {
        return this.props.record.data[this.props.periodTypeField] === "quarter";
    }

    quarterLabel(quarter, year) {
        return _t("Q%(quarter)s %(year)s", { quarter, year });
    }

    get label() {
        const value = this.value;
        if (!value) {
            return "";
        }
        if (this.isQuarter) {
            return this.quarterLabel(value.quarter, value.year);
        }
        return value.toFormat("LLLL yyyy");
    }

    get items() {
        const value = this.value;
        const year = this.state.year;
        if (this.isQuarter) {
            return [1, 2, 3, 4].map((quarter) => ({
                key: quarter,
                month: 3 * quarter - 2,
                label: _t("Q%(quarter)s", { quarter }),
                title: this.quarterLabel(quarter, year),
                selected: Boolean(value) && value.year === year && value.quarter === quarter,
            }));
        }
        return [...Array(12).keys()].map((index) => {
            const start = DateTime.local(year, index + 1, 1);
            return {
                key: index + 1,
                month: index + 1,
                label: start.toFormat("LLL"),
                title: start.toFormat("LLLL yyyy"),
                selected: Boolean(value) && value.year === year && value.month === index + 1,
            };
        });
    }

    onOpened() {
        this.state.year = (this.value || DateTime.local()).year;
    }

    shiftYear(step) {
        this.state.year += step;
    }

    async select(item) {
        await this.props.record.update({
            [this.props.name]: DateTime.local(this.state.year, item.month, 1),
        });
        this.dropdown.close();
    }
}

export const csskPeriodField = {
    component: CsskPeriodField,
    displayName: _t("Tax period (month or quarter)"),
    supportedTypes: ["date"],
    supportedOptions: [
        {
            label: _t("Period type field"),
            name: "period_type_field",
            type: "field",
            availableTypes: ["selection"],
        },
    ],
    extractProps: ({ options }) => ({
        periodTypeField: options.period_type_field,
    }),
    fieldDependencies: ({ options }) => [
        { name: options.period_type_field || "period_type", type: "selection" },
    ],
};

registry.category("fields").add("cssk_period", csskPeriodField);
