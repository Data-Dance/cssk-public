import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { _t } from "@web/core/l10n/translation";

const viewWidgetRegistry = registry.category("view_widgets");

/**
 * Fill this till's VRP2 login/password from the company default register.
 * Updates the record in memory (no save, no reload) so the quick-config
 * dialog stays open and the fields populate immediately.
 */
export class Vrp2LoadCredentials extends Component {
    static template = "pos_vrp2.Vrp2LoadCredentials";
    static props = { ...standardWidgetProps };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
    }

    async onClick() {
        const record = this.props.record;
        const companyId = record.data.company_id && record.data.company_id.id;
        const creds = await this.orm.call(
            "pos.config",
            "vrp2_company_credentials",
            [companyId || false]
        );
        await record.update({
            vrp2_login: creds.vrp2_login,
            vrp2_password: creds.vrp2_password,
        });
        this.notification.add(
            _t("Loaded credentials from the company. Click Login to connect this till."),
            { type: "success" }
        );
    }
}
viewWidgetRegistry.add("vrp2_load_credentials", { component: Vrp2LoadCredentials });

/**
 * Base for VRP2 session actions (Login / Logout): persist pending edits, run
 * the server method, then reload the record in place so the status badge and
 * button visibility refresh without closing the dialog.
 */
class Vrp2SessionButton extends Component {
    static props = { ...standardWidgetProps };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
    }

    async _run(method, fallbackMessage) {
        const record = this.props.record;
        // Persist credentials so the server method sees them.
        if (await record.isDirty()) {
            const saved = await record.save();
            if (saved === false) {
                return;
            }
        }
        const result = await this.orm.call("pos.config", method, [[record.resId]]);
        // Reload so vrp2_token / vrp2_status / dashboard refresh on the form.
        await record.load();
        const params = (result && result.params) || {};
        this.notification.add(params.message || fallbackMessage, {
            type: params.type || "success",
            title: params.title,
            sticky: !!params.sticky,
        });
    }
}

export class Vrp2LoginButton extends Vrp2SessionButton {
    static template = "pos_vrp2.Vrp2LoginButton";
    onClick() {
        return this._run("action_vrp2_login", _t("Logged in to VRP2."));
    }
}
viewWidgetRegistry.add("vrp2_login", { component: Vrp2LoginButton });

export class Vrp2LogoutButton extends Vrp2SessionButton {
    static template = "pos_vrp2.Vrp2LogoutButton";
    onClick() {
        return this._run("action_vrp2_logout", _t("Logged out from VRP2."));
    }
}
viewWidgetRegistry.add("vrp2_logout", { component: Vrp2LogoutButton });
