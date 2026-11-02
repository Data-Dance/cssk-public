// Copyright 2026 Data Dance s.r.o.
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import {Component, onWillStart, useState} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {DomainSelectorDialog} from "@web/core/domain_selector_dialog/domain_selector_dialog";
import {Layout} from "@web/search/layout";
import {SaveViewDialog} from "./save_view_dialog.esm";
import {formatMonetary} from "@web/views/fields/formatters";
import {registry} from "@web/core/registry";
import {standardActionServiceProps} from "@web/webclient/actions/action_service";
import {useService} from "@web/core/utils/hooks";

const MODEL = "account.financial.report.interactive";
const VIEW_MODEL = "account.financial.report.interactive.view";

/**
 * Trial balance rows per account; unfolding an account loads its journal
 * items a page at a time, with a running balance carried over from the last
 * loaded row. Nothing below an account is computed until it is opened.
 */
export class InteractiveLedger extends Component {
    static template = "account_financial_report_interactive.InteractiveLedger";
    static components = {Layout};
    static props = {...standardActionServiceProps};

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.data = {...this.props.action.params.data};
        this.display = {controlPanel: {}, searchPanel: false};
        this.state = useState({
            accounts: [],
            totals: {},
            currencyId: false,
            statements: false,
            // account id -> {lines, total, offset, loading}
            unfolded: {},
            comparisonMode: "none",
            comparisonCount: 1,
            comparisonLabels: [],
            views: [],
        });
        const comparison = this.props.action.params.comparison;
        if (comparison && comparison.mode) {
            this.state.comparisonMode = comparison.mode;
            this.state.comparisonCount = comparison.count || 1;
        }
        onWillStart(() => Promise.all([this.load(), this.loadViews()]));
    }

    async load() {
        const comparison =
            this.state.comparisonMode === "none"
                ? false
                : {mode: this.state.comparisonMode, count: this.state.comparisonCount};
        const result = await this.orm.call(MODEL, "get_accounts", [this.data, comparison]);
        this.state.accounts = result.accounts;
        this.state.totals = result.totals;
        this.state.currencyId = result.currency_id;
        this.state.comparisonLabels = result.comparison_labels;
        this.state.statements = result.statements;
    }

    async loadViews() {
        this.state.views = await this.orm.call(VIEW_MODEL, "list_views", []);
    }

    saveView() {
        this.dialog.add(SaveViewDialog, {
            defaultName: this.props.action.params.title || "",
            onSave: async (values) => {
                await this.orm.call(VIEW_MODEL, "save_view", [{
                    ...values,
                    title: this.props.action.params.title || values.name,
                    data: this.data,
                    comparison:
                        this.state.comparisonMode === "none"
                            ? false
                            : {mode: this.state.comparisonMode, count: this.state.comparisonCount},
                }]);
                this.notification.add(_t("View saved"), {type: "success"});
                await this.loadViews();
            },
        });
    }

    async openView(ev) {
        const viewId = parseInt(ev.target.value, 10);
        ev.target.value = "";
        if (!viewId) {
            return;
        }
        const action = await this.orm.call(VIEW_MODEL, "action_open", [[viewId]]);
        this.action.doAction(action);
    }

    get filtered() {
        const domain = this.data.extra_domain;
        return Boolean(domain && domain !== "[]");
    }

    editFilter() {
        this.dialog.add(DomainSelectorDialog, {
            resModel: "account.move.line",
            domain: this.data.extra_domain || "[]",
            title: _t("Filter the journal items"),
            confirmButtonText: _t("Apply"),
            isDebugMode: Boolean(this.env.debug),
            onConfirm: async (domain) => {
                this.data = {...this.data, extra_domain: domain};
                this.state.unfolded = {};
                await this.load();
            },
        });
    }

    async clearFilter() {
        this.data = {...this.data, extra_domain: false};
        this.state.unfolded = {};
        await this.load();
    }

    get periodLabel() {
        return `${this.data.date_from} – ${this.data.date_to}`;
    }

    async shiftPeriod(step) {
        this.data = await this.orm.call(MODEL, "shift_period", [this.data, step]);
        this.state.unfolded = {};
        await this.load();
        // The breadcrumb follows the period shown.
        const title = this.props.action.params.title;
        if (title) {
            this.env.config.setDisplayName(`${title} ${this.periodLabel}`);
        }
    }

    async onComparisonChange(ev) {
        this.state.comparisonMode = ev.target.value;
        await this.load();
    }

    async onComparisonCountChange(ev) {
        this.state.comparisonCount = parseInt(ev.target.value, 10) || 1;
        await this.load();
    }

    get comparing() {
        return this.state.comparisonLabels.length > 0;
    }

    growthClass(account) {
        if (account.growth === null || !account.growth_sense) {
            return "";
        }
        const good = account.growth * account.growth_sense > 0;
        return good ? "text-success" : "text-danger";
    }

    formatGrowth(account) {
        return account.growth === null ? "" : `${account.growth > 0 ? "+" : ""}${account.growth} %`;
    }

    format(value) {
        return formatMonetary(value, {currencyId: this.state.currencyId});
    }

    // Unfolded entries are keyed "a<account>" or "a<account>:p<partner>".
    accountKey(account) {
        return `a${account.id}`;
    }

    partnerKey(account, partner) {
        return `a${account.id}:p${partner.id}`;
    }

    isUnfolded(key) {
        return Boolean(this.state.unfolded[key]);
    }

    async toggle(account) {
        const key = this.accountKey(account);
        if (account.type === "group") {
            return;
        }
        if (this.isUnfolded(key)) {
            delete this.state.unfolded[key];
            return;
        }
        if (account.by_partner) {
            this.state.unfolded[key] = {partners: [], loading: true};
            const partners = await this.orm.call(MODEL, "get_partners", [this.data, account.id]);
            Object.assign(this.state.unfolded[key], {partners, loading: false});
            return;
        }
        this.state.unfolded[key] = {lines: [], total: 0, offset: 0, loading: true};
        await this.loadMore(key, account.id, null, account.opening);
    }

    async togglePartner(account, partner) {
        const key = this.partnerKey(account, partner);
        if (this.isUnfolded(key)) {
            delete this.state.unfolded[key];
            return;
        }
        this.state.unfolded[key] = {lines: [], total: 0, offset: 0, loading: true};
        await this.loadMore(key, account.id, partner.id, partner.opening);
    }

    async loadMore(key, accountId, partnerId, startBalance) {
        const entry = this.state.unfolded[key];
        if (!entry) {
            return;
        }
        entry.loading = true;
        const page = await this.orm.call(MODEL, "get_lines", [
            this.data,
            accountId,
            entry.offset,
            startBalance,
            80,
            partnerId,
        ]);
        entry.lines.push(...page.lines);
        entry.total = page.total;
        entry.offset = page.offset;
        entry.loading = false;
    }

    parentAccountId(key) {
        return parseInt(key.split(":")[0].slice(1), 10);
    }

    lastBalance(key, opening) {
        const lines = this.state.unfolded[key].lines;
        return lines.length ? lines[lines.length - 1].balance : opening;
    }

    openMove(line) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "account.move",
            res_id: line.move_id,
            views: [[false, "form"]],
        });
    }

    openRecord(model, id) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: model,
            res_id: id,
            views: [[false, "form"]],
        });
    }

    async sendStatement(line) {
        const action = await this.orm.call(MODEL, "statement_action", [
            this.data,
            line.partner_id,
        ]);
        if (action) {
            this.action.doAction(action);
        }
    }

    async copyLine(line) {
        const text = [line.date, line.move_name, line.journal, line.partner, line.label,
            line.debit, line.credit, line.balance].join("\t");
        try {
            await navigator.clipboard.writeText(text);
            this.notification.add(_t("Line copied"), {type: "success"});
        } catch {
            this.notification.add(_t("The browser refused access to the clipboard."), {
                type: "warning",
            });
        }
    }

    async openAccountItems(account) {
        const domain = await this.orm.call(MODEL, "get_account_domain", [
            this.data,
            account.id,
        ]);
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("%s - Journal Items", account.code),
            res_model: "account.move.line",
            domain,
            views: [
                [false, "list"],
                [false, "form"],
            ],
        });
    }
}

registry.category("actions").add("afr_interactive_ledger", InteractiveLedger);
