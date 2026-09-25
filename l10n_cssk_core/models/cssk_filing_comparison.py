# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""One comparison of one filing against one right-hand side.

``cssk.filing.discrepancy`` is row-grained, and a row is the wrong unit to
read a migration off. A Slovak agenda produced 608 rows on one DPH priznanie;
the list showed 608 lines with mixed states and no way to say which FILING any
of them belonged to — the filing is ``(res_model, res_id)``, two columns, and
Odoo cannot group by a pair. So the one grouping a reader actually wants was
the one grouping the screen could not offer.

The unit is the row key minus the row: ``(res_model, res_id, basis)``. ``basis``
belongs in it for the same reason it belongs in the row's key — the same VAT
return is put beside a recomputation of ITSELF and beside účet 343, and those
are two comparisons that happen to share a filing, not one comparison.

THE CONSOLIDATED STATE IS DERIVED, NEVER SET. It splits on the same two axes
the row does: what the figures say (``kind``) versus what a person decided
(``state``). A parent state somebody could type would drift from its rows the
first time a row changed, and a drifted summary is worse than no summary —
it is read and believed. The one thing here that is NOT derivable is the
sign-off: that a human looked at the whole comparison and accepted it. That
gets its own field, because nothing about the rows implies it.

``expected`` and ``info`` rows are NOT findings. The row model is explicit that
they are "findings of neither agreement nor error" — a KV is a proper subset of
the priznanie — so a comparison whose only non-agreeing rows are those is
``clean``. Counting them as findings would report every correct KV as needing
review, which is the precise failure this screen exists to avoid.

⚠️ **ONLY THE ``ledger`` BASIS CAN PRODUCE THOSE TWO KINDS**, and knowing which
basis you are looking at is the difference between reading a screen and
misreading it. The mixin's own comparator — ``basis='recomputed'``, the
"Compare with computed" button — emits exactly ``ok``, ``only_filed``,
``only_computed``, ``differs`` and ``unmapped``; there is no branch in it that
can yield ``expected`` or ``info``. Those come from ``l10n_sk_datadance``'s
``_RECON_KIND``, which maps ``subset`` → ``expected`` and ``info`` → ``info``
when it puts a filing beside účet 343 and účtová trieda 60.

So a ``recomputed`` comparison showing ``finding_count == open_count`` and no
structural rows is CORRECT and not a collapse that failed to fire. That reading
cost a round of live analysis: twelve migrated PREMIER filings came back with
that exact uniformity, it looked like a classification that never assigns those
kinds, and it was simply the wrong basis to expect them on.
"""

from odoo import _, api, fields, models

#: Kinds that are a real disagreement and want an answer. Deliberately NOT
#: ``expected`` / ``info`` — see the module docstring — and not ``ok``.
FINDING_KINDS = ("amount", "classification", "only_filed", "only_computed",
                 "unmapped")

#: Row states that mean somebody has answered. ``asked`` is not among them:
#: a question put to the accountant is engagement, not an answer.
ANSWERED_STATES = ("correct_as_filed", "filing_error", "our_error", "no_action")


class CSSKFilingComparison(models.Model):
    _name = "cssk.filing.comparison"
    _description = "Filed vs Computed Comparison"
    _inherit = ["mail.thread"]
    _order = "date_from desc, res_model, basis"

    # The KEY, and the only thing about the form that is stored. A Selection
    # rather than a Char so the label renders in the reader's language while
    # the stored value stays the model name every domain already compares
    # against — same column, same contents, no migration of values.
    res_model = fields.Selection(
        selection="_cssk_form_selection", string="Form",
        required=True, readonly=True, index=True)
    res_id = fields.Integer(required=True, readonly=True, index=True)

    filing_name = fields.Char(readonly=True, index=True)
    legacy_source = fields.Char(
        readonly=True, help="The system the filing was migrated from.")

    company_id = fields.Many2one("res.company", required=True, readonly=True,
                                 index=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    date_from = fields.Date(readonly=True)
    date_to = fields.Date(readonly=True)

    basis = fields.Selection(
        [
            ("recomputed", "The filing, recomputed"),
            ("ledger", "The ledger"),
            ("filing", "Another filing"),
        ],
        string="Compared against", required=True, readonly=True, index=True,
        default="recomputed",
        help="What the right-hand side of every row holds. The same filing is "
             "compared against more than one, and they are separate "
             "comparisons.")
    basis_label = fields.Char(
        string="Compared against (detail)", readonly=True,
        help="The right-hand side named exactly — which account, which other "
             "filing.")

    line_ids = fields.One2many(
        "cssk.filing.discrepancy", "comparison_id", string="Rows",
        readonly=True)

    # --- the counts, which are the point of the screen ---------------------
    row_count = fields.Integer(
        compute="_compute_cssk_rollup", store=True, string="Rows")
    agree_count = fields.Integer(
        compute="_compute_cssk_rollup", store=True, string="Agree")
    finding_count = fields.Integer(
        compute="_compute_cssk_rollup", store=True, string="Findings",
        help="Rows that really disagree. A structural gap ('Difference is "
             "expected') and an informational row are not counted — they are "
             "neither agreement nor error.")
    open_count = fields.Integer(
        compute="_compute_cssk_rollup", store=True, string="To review",
        help="Findings nobody has answered yet.")
    asked_count = fields.Integer(
        compute="_compute_cssk_rollup", store=True, string="Asked")
    answered_count = fields.Integer(
        compute="_compute_cssk_rollup", store=True, string="Answered")
    stale_count = fields.Integer(
        compute="_compute_cssk_rollup", store=True, string="No longer compared")

    filed_total = fields.Monetary(
        compute="_compute_cssk_rollup", store=True, string="Filed")
    computed_total = fields.Monetary(
        compute="_compute_cssk_rollup", store=True, string="Computed")
    difference_total = fields.Monetary(
        compute="_compute_cssk_rollup", store=True, string="Difference")

    state = fields.Selection(
        [
            ("clean", "Everything agrees"),
            ("open", "To review"),
            ("in_progress", "Being worked through"),
            ("resolved", "Every difference answered"),
        ],
        compute="_compute_cssk_rollup", store=True, index=True,
        help="Derived from the rows and never set by hand: a summary somebody "
             "could type would drift from what it summarises. Whether a human "
             "has ACCEPTED the comparison is the separate sign-off.")

    last_run_uid = fields.Many2one("res.users", readonly=True,
                                   string="Last run by")
    last_run_date = fields.Datetime(readonly=True, string="Last run")

    # Not derivable from anything: that a person looked at the whole
    # comparison and accepted it. Kept off ``state`` so a re-run cannot
    # silently revoke it, and so a clean comparison nobody has read is
    # visibly different from one somebody has signed.
    signed_off_uid = fields.Many2one("res.users", readonly=True,
                                     string="Signed off by", tracking=True)
    signed_off_date = fields.Datetime(readonly=True, string="Signed off",
                                      tracking=True)

    _comparison_uniq = models.Constraint(
        "UNIQUE (res_model, res_id, basis)",
        "One comparison per filing, per basis of comparison.",
    )

    # Bare ``line_ids`` alongside the dotted paths. The dotted form does
    # invalidate on membership change in current Odoo, but it costs nothing to
    # state and this compute is the one thing a reader trusts without checking
    # — a count that silently stopped recomputing when a row moved between
    # comparisons would be believed.
    @api.model
    def _cssk_form_selection(self):
        """Every model that can produce a comparison, labelled for the reader.

        THE KEY IS STORED AND THE LABEL IS COMPUTED, which is the whole point of
        this field being a Selection rather than the Char it was beside. The
        label used to be stored in ``form_label``, written in the language of
        whoever ran the comparison — so a screen read English to everybody else
        until each filing was re-run in Slovak, seven of them by hand on the
        demo box. A Selection stores the model name and renders its label per
        reader, which also keeps the field groupable: a computed label alone
        would have cost the "Form" group-by its column.

        Built from the registry rather than a literal list, so a country module
        adding a submission model appears here without editing this file. The
        labels come from the models' own ``_cssk_form_label``, which is an
        ``_lt`` carrying its own module — ``env._`` resolves it against THAT
        module's catalogue, which is where those terms live.
        """
        out = []
        for name, cls in self.env.registry.items():
            # Filter on the CLASS, not on ``self.env[name]``. This runs on
            # every fields_get and every group-by, and a full install has well
            # over a thousand models — instantiating each one to ask two
            # questions about it is work nobody asked for. The attribute and
            # the abstract flag both live on the class.
            if cls._abstract or not hasattr(cls, "_cssk_form_label"):
                continue
            out.append((name, self.env._(cls._cssk_form_label)))
        return sorted(out, key=lambda pair: pair[1])

    @api.depends("line_ids", "line_ids.kind", "line_ids.state",
                 "line_ids.stale", "line_ids.filed", "line_ids.computed",
                 "line_ids.difference")
    def _compute_cssk_rollup(self):
        for rec in self:
            live = rec.line_ids.filtered(lambda r: not r.stale)
            findings = live.filtered(lambda r: r.kind in FINDING_KINDS)
            answered = findings.filtered(lambda r: r.state in ANSWERED_STATES)
            asked = findings.filtered(lambda r: r.state == "asked")
            rec.row_count = len(live)
            rec.agree_count = len(live.filtered(lambda r: r.kind == "ok"))
            rec.finding_count = len(findings)
            rec.answered_count = len(answered)
            rec.asked_count = len(asked)
            rec.open_count = len(findings) - len(answered) - len(asked)
            rec.stale_count = len(rec.line_ids) - len(live)
            rec.filed_total = sum(live.mapped("filed"))
            rec.computed_total = sum(live.mapped("computed"))
            rec.difference_total = sum(live.mapped("difference"))
            if not findings:
                rec.state = "clean"
            elif len(answered) == len(findings):
                rec.state = "resolved"
            elif answered or asked:
                rec.state = "in_progress"
            else:
                rec.state = "open"

    @api.depends("filing_name", "basis")
    def _compute_display_name(self):
        labels = dict(self._fields["basis"]._description_selection(self.env))
        for rec in self:
            rec.display_name = "%s — %s" % (rec.filing_name or "",
                                            labels.get(rec.basis, rec.basis))

    def action_open_filing(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self.res_model,
            "res_id": self.res_id,
            "view_mode": "form",
            "target": "current",
        }

    def action_open_rows(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Filed vs computed — %s", self.filing_name or ""),
            "res_model": "cssk.filing.discrepancy",
            "view_mode": "list,form",
            "domain": [("comparison_id", "=", self.id)],
            "context": {"search_default_live": 1},
            "target": "current",
        }

    def action_cssk_sign_off(self):
        for rec in self:
            rec.write({"signed_off_uid": self.env.uid,
                       "signed_off_date": fields.Datetime.now()})

    def action_cssk_unsign(self):
        for rec in self:
            rec.write({"signed_off_uid": False, "signed_off_date": False})
