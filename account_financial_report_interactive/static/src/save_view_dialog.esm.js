// Copyright 2026 Data Dance s.r.o.
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import {Component, useState} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";

export class SaveViewDialog extends Component {
    static template = "account_financial_report_interactive.SaveViewDialog";
    static components = {Dialog};
    static props = {close: Function, onSave: Function, defaultName: {type: String, optional: true}};

    setup() {
        this.state = useState({
            name: this.props.defaultName || "",
            period: "fixed",
            shared: false,
            is_default: false,
        });
    }

    async save() {
        if (!this.state.name.trim()) {
            return;
        }
        await this.props.onSave({...this.state, name: this.state.name.trim()});
        this.props.close();
    }
}
