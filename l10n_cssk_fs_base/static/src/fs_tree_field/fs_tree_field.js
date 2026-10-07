/** @odoo-module **/
// Foldable financial-statement tree widget for the cssk.fs.statement line_ids
// one2many. Reconstructs the hierarchy from each line's parent_id, renders
// collapsible aggregate rows, and drills a leaf row to its journal items via
// the model's action_view_source_lines(). Any row that is not a total takes a
// manual figure for either column (is_overridden / is_prior_overridden); the
// totals catch up on the next Compute, which keeps the manual figures.
import { registry } from "@web/core/registry";
import { Component, useEffect, useRef, useState } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { formatFloat } from "@web/views/fields/formatters";
import { parseFloat } from "@web/views/fields/parsers";

// Per column: the flag, the manual figure, and the value it stands in for.
const COLUMNS = {
    current: { flag: "is_overridden", manual: "manual_value", value: "current_value" },
    prior: { flag: "is_prior_overridden", manual: "prior_manual_value", value: "prior_value" },
};

export class FsTreeField extends Component {
    static template = "l10n_cssk_fs_base.FsTreeField";
    static props = { ...standardFieldProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        // collapsed[resId] === true  -> that aggregate's children are hidden
        this.state = useState({ collapsed: {}, invalid: {}, editing: {}, focus: null });
        this.titles = {
            tie: _t("Source lines tie to the value"),
            noTie: _t("Does not tie (rounding / clamp / carryover / manual figure)"),
            edit: _t("Enter this figure by hand"),
            reset: _t("Back to the computed figure (on the next Compute)"),
            manual: _t("Entered by hand"),
        };
        this.root = useRef("root");
        // Focus the input a pencil click just opened.
        useEffect(
            (focus) => {
                if (!focus || !this.root.el) {
                    return;
                }
                const input = this.root.el.querySelector(`input[data-cell="${focus}"]`);
                if (input) {
                    input.focus();
                    input.select();
                }
                this.state.focus = null;
            },
            () => [this.state.focus]
        );
    }

    get list() {
        return this.props.record.data[this.props.name];
    }

    _parentId(rec) {
        const p = rec.data.parent_id;
        if (!p) {
            return false;
        }
        return p.id ?? (Array.isArray(p) ? p[0] : false);
    }

    // Ordered, depth-annotated rows respecting the collapse state.
    get rows() {
        const recs = (this.list && this.list.records) || [];
        const byId = {};
        const childrenOf = {};
        const roots = [];
        for (const r of recs) {
            byId[r.resId] = r;
        }
        for (const r of recs) {
            const pid = this._parentId(r);
            if (pid && byId[pid]) {
                (childrenOf[pid] ||= []).push(r);
            } else {
                roots.push(r);
            }
        }
        const out = [];
        const walk = (r, depth) => {
            const kids = childrenOf[r.resId] || [];
            const collapsed = !!this.state.collapsed[r.resId];
            out.push({
                id: r.resId,
                record: r,
                editable: !this.props.readonly && r.data.kind !== "aggregate",
                manual: !!r.data.is_overridden,
                priorManual: !!r.data.is_prior_overridden,
                depth,
                hasChildren: kids.length > 0,
                collapsed,
                isLeaf: !!r.data.is_leaf,
                hasSource: !!r.data.has_source,
                code: r.data.code || "",
                name: r.data.name || r.data.code || "",
                value: r.data.current_value || 0,
                prior: r.data.prior_value || 0,
                reconciles: !!r.data.source_reconciles,
            });
            if (!collapsed) {
                for (const k of kids) {
                    walk(k, depth + 1);
                }
            }
        };
        for (const r of roots) {
            walk(r, 0);
        }
        return out;
    }

    toggle(id) {
        this.state.collapsed[id] = !this.state.collapsed[id];
    }

    collapseAll() {
        const recs = (this.list && this.list.records) || [];
        const parents = {};
        for (const r of recs) {
            const pid = this._parentId(r);
            if (pid) {
                parents[pid] = true;
            }
        }
        this.state.collapsed = parents;
    }

    expandAll() {
        this.state.collapsed = {};
    }

    async drill(id) {
        const action = await this.orm.call(
            "cssk.fs.statement.line", "action_view_source_lines", [[id]]);
        this.action.doAction(action);
    }

    cellKey(row, column) {
        return `${row.id}-${column}`;
    }

    isEditing(row, column) {
        return !!this.state.editing[this.cellKey(row, column)];
    }

    inputValue(row, column) {
        const col = COLUMNS[column];
        const data = row.record.data;
        // Before the first entry the input starts from the figure on screen,
        // so a slight correction does not mean retyping the whole number.
        const value = data[col.flag] ? data[col.manual] : data[col.value];
        return formatFloat(value || 0, { digits: [16, 2] });
    }

    // Pencil: open the input locally. Nothing is written until a figure is
    // entered — a round-trip here raced the typing that follows it, and a
    // figure entered while it was in flight was lost.
    startOverride(row, column) {
        const key = this.cellKey(row, column);
        this.state.editing[key] = true;
        this.state.focus = key;
    }

    async setManual(row, column, ev) {
        const col = COLUMNS[column];
        const key = this.cellKey(row, column);
        let value;
        try {
            value = parseFloat(ev.target.value);
        } catch {
            this.state.invalid[key] = true;
            return;
        }
        delete this.state.invalid[key];
        // The row's own figure follows at once; the totals over it on the
        // next Compute.
        await row.record.update({ [col.flag]: true, [col.manual]: value, [col.value]: value });
        delete this.state.editing[key];
    }

    // Leaving an opened input without entering anything closes it again.
    // ``change`` fires before ``blur``, so a figure that was entered has its
    // update under way and keeps the input open until it lands.
    onBlur(row, column, ev) {
        const key = this.cellKey(row, column);
        if (ev.target.value === this.inputValue(row, column) && !row.record.data[COLUMNS[column].flag]) {
            delete this.state.editing[key];
        }
    }

    async resetOverride(row, column) {
        const key = this.cellKey(row, column);
        delete this.state.invalid[key];
        delete this.state.editing[key];
        await row.record.update({ [COLUMNS[column].flag]: false });
    }

    fmt(v) {
        return (v || 0).toLocaleString("sk-SK", { maximumFractionDigits: 0 });
    }
}

export const fsTreeField = {
    component: FsTreeField,
    supportedTypes: ["one2many"],
};
registry.category("fields").add("cssk_fs_tree", fsTreeField);
