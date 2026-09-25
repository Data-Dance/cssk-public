/* Copyright 2026 Data Dance s.r.o.
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */
import { Component, onWillStart, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { formatMonetary } from "@web/views/fields/formatters";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

export class DepreciationSchedule extends Component {
    static template = "account_asset_board.DepreciationSchedule";
    static components = { Layout };
    static props = { ...standardActionServiceProps };

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.state = useState({
            dateFrom: "",
            dateTo: "",
            data: null,
            folded: {},
        });
        onWillStart(async () => {
            if (this.env.config.setDisplayName) {
                this.env.config.setDisplayName(_t("Depreciation Schedule"));
            }
            await this.load();
        });
    }

    async load() {
        const data = await this.orm.call("account.asset", "get_schedule", [], {
            date_from: this.state.dateFrom || false,
            date_to: this.state.dateTo || false,
        });
        this.state.data = data;
        this.state.dateFrom = data.date_from;
        this.state.dateTo = data.date_to;
    }

    onDateChange(field, ev) {
        if (!ev.target.value) {
            return;
        }
        this.state[field] = ev.target.value;
        this.load();
    }

    toggleGroup(profileId) {
        this.state.folded[profileId] = !this.state.folded[profileId];
    }

    fmt(value) {
        return formatMonetary(value, { currencyId: this.state.data.currency_id });
    }

    openAsset(assetId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "account.asset",
            res_id: assetId,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

registry
    .category("actions")
    .add("account_asset_board.depreciation_schedule", DepreciationSchedule);
