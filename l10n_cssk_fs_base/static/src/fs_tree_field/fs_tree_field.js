/** @odoo-module **/
// Foldable financial-statement tree widget for the cssk.fs.statement line_ids
// one2many. Reconstructs the hierarchy from each line's parent_id, renders
// collapsible aggregate rows, and drills a leaf row to its journal items via
// the model's action_view_source_lines().
import { registry } from "@web/core/registry";
import { Component, useState } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class FsTreeField extends Component {
    static template = "l10n_cssk_fs_base.FsTreeField";
    static props = { ...standardFieldProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        // collapsed[resId] === true  -> that aggregate's children are hidden
        this.state = useState({ collapsed: {} });
        this.titles = {
            tie: _t("Source lines tie to the value"),
            noTie: _t("Does not tie (rounding / clamp / carryover)"),
        };
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

    fmt(v) {
        return (v || 0).toLocaleString("sk-SK", { maximumFractionDigits: 0 });
    }
}

export const fsTreeField = {
    component: FsTreeField,
    supportedTypes: ["one2many"],
};
registry.category("fields").add("cssk_fs_tree", fsTreeField);
