# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""A filing beside what the ledger says, row by row, written down.

The comparison used to go to the chatter, which is a log: it records that a
difference was seen and gives nobody a way to work through it. A difference
found against a historical filing has a life of its own — somebody has to ask
the accountant who filed it whether the filing was right or wrong, and the
answer has to survive the next recompute.

So each row becomes a record with a question and an answer on it. Re-running
the comparison UPDATES the figures and leaves the answer alone; a row that
stops appearing is marked ``stale`` rather than deleted, because a deleted
resolved item is indistinguishable from one nobody ever looked at, and the
next reader raises it a second time.

**The rows that AGREE are recorded too**, which is why this is a comparison
and not a defect list. A migration is judged by how much of it landed, and a
screen that shows only what went wrong cannot answer that — on the agenda this
was built for, 583 of 608 rows agree and the accountant had no way to see it.
Agreeing rows are created in state ``agrees``, so the worklist filter (state
``open`` / ``asked``) never fills with them: they are there when somebody opens
the comparison and invisible when somebody is working through findings.

``basis`` says what the right-hand column IS, and it is not decoration. The
mixin's own comparator recomputes the filing from the ledger; the Slovak
reconciliations put the same filing beside the ledger itself (účet 343), or
beside a different filing for the same period (KV ↔ priznanie, VZS ↔ DPPO).
Three different questions. On one screen without a discriminator, a reader
seeing "computed" has no way to know which one was asked, and correct figures
look wrong.

The classification pairing is the interesting part. Two engines can agree on
an amount and disagree about which row it belongs on, which arrives here as a
row only the filing has and a row only we compute, offsetting each other
exactly. That is one disagreement, not two, and the question to put to the
accountant is a different question — "which box is right" rather than "which
number is right". The pair is detected and labelled as such.
"""

from odoo import _, api, fields, models


class CSSKFilingDiscrepancy(models.Model):
    _name = "cssk.filing.discrepancy"
    _description = "Filed vs Computed Comparison Row"
    # A chatter, because the answer to a discrepancy is a CONVERSATION with
    # the accountant who filed it — asked on a date, answered on another,
    # sometimes by somebody else. `resolved_uid` records who settled it;
    # the thread records how. It also makes ``tracking`` on the state legal,
    # which it was not before: a tracked field on a model without mail.thread
    # is a warning on every registry load and tracks nothing.
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_from desc, code"

    # The comparison this row belongs to — one filing against one right-hand
    # side. Added because the filing is (res_model, res_id), a PAIR, and Odoo
    # cannot group a list by a pair: "group by the filing" was the one
    # grouping a reader wants and the screen could not express. The parent
    # also carries the consolidated verdict, which has nowhere to live on a
    # row.
    comparison_id = fields.Many2one(
        "cssk.filing.comparison", required=True, readonly=True, index=True,
        ondelete="cascade")

    # The filing is one of six statutory models, so it is held as a loose
    # reference rather than a Many2one to any of them.
    #
    # These stay stored on the row rather than becoming ``related`` to the
    # parent. They are genuinely redundant now, but every domain, search view
    # and the ``_row_uniq`` constraint reads them directly, and converting
    # them buys nothing on screen. Recorded as known duplication, not as an
    # oversight.
    # The KEY, and the only thing about the form that is stored. A Selection
    # rather than a Char so the label renders in the reader's language while
    # the stored value stays the model name every domain already compares
    # against — same column, same contents, no migration of values.
    res_model = fields.Selection(
        selection="_cssk_form_selection", string="Form",
        required=True, readonly=True, index=True)
    res_id = fields.Integer(required=True, readonly=True, index=True)
    filing_name = fields.Char(readonly=True)
    legacy_source = fields.Char(
        readonly=True, help="The system the filing was migrated from.")

    company_id = fields.Many2one("res.company", required=True, readonly=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    date_from = fields.Date(readonly=True)
    date_to = fields.Date(readonly=True)

    code = fields.Char(
        required=True, readonly=True, index=True,
        help="The row: a line code on a coded form, or the section and "
             "identity of a row on a document-based one.")
    # NOT "Name". A bare ``Name`` is already in the templates from core's own
    # generic use, sits there untranslated because what it names varies by
    # context, and so came up English in the middle of an otherwise Slovak
    # screen. A label specific enough to translate is a label specific enough
    # to export.
    row_label = fields.Char(
        string="Row name", readonly=True,
        help="The row in words, where the source of the comparison has one. "
             "A coded form identifies its rows by code alone.")
    filed = fields.Monetary(readonly=True, help="What the filing reports.")
    computed = fields.Monetary(
        readonly=True, help="What the right-hand side says — see Compared "
                            "against.")
    difference = fields.Monetary(readonly=True)

    basis = fields.Selection(
        [
            ("recomputed", "The filing, recomputed"),
            ("ledger", "The ledger"),
            ("filing", "Another filing"),
        ],
        string="Compared against", required=True, readonly=True, index=True,
        default="recomputed",
        help="What the right-hand column holds. Without it a reader cannot "
             "tell which question was asked, and correct figures look wrong.")
    basis_label = fields.Char(
        # Paired with ``basis`` deliberately: this is the concrete instance of
        # the same axis, and two names that do not say so read as two
        # unrelated fields sitting next to each other.
        string="Compared against (detail)", readonly=True,
        help="The right-hand side named exactly — which account, which other "
             "filing.")

    kind = fields.Selection(
        [
            ("ok", "Agrees"),
            ("amount", "Amount differs"),
            ("classification", "Same amount, different row"),
            ("only_filed", "Only the filing has it"),
            ("only_computed", "Only we compute it"),
            ("unmapped", "Vocabularies not mapped"),
            ("expected", "Difference is expected"),
            ("info", "Informational, not a control"),
        ],
        required=True, readonly=True,
        help="'Difference is expected' and 'Informational' are findings of "
             "neither agreement nor error: a KV is a proper subset of the "
             "priznanie, and the VAT base legitimately diverges from účtovná "
             "trieda 60. Reported, never flagged.",
    )
    detail = fields.Text(
        readonly=True,
        help="Set where one record stands for many rows — it says how many "
             "and why they are one fact rather than several.")
    counterpart_id = fields.Many2one(
        "cssk.filing.discrepancy", readonly=True,
        help="The other half of a classification disagreement: the row that "
             "carries the same amount on the other side.")

    state = fields.Selection(
        [
            ("agrees", "Agrees"),
            ("open", "To review"),
            ("asked", "Asked the accountant"),
            ("correct_as_filed", "Filing was right"),
            ("filing_error", "Filing was wrong"),
            ("our_error", "We are wrong"),
            ("no_action", "Understood, no action"),
        ],
        default="open", required=True, tracking=True,
        help="'Agrees' and 'To review' are set by the comparison and follow "
             "the figures. Anything beyond them is somebody's answer and is "
             "never overwritten by a re-run.",
    )
    note = fields.Text(
        help="What the accountant said, and anything else worth keeping. "
             "Survives a recompute.")
    resolved_uid = fields.Many2one("res.users", readonly=True)
    resolved_date = fields.Datetime(readonly=True)

    stale = fields.Boolean(
        readonly=True,
        help="The row no longer appears in the comparison at all — neither "
             "side carries it any more. Kept rather than deleted: a deleted "
             "item that somebody resolved looks exactly like one nobody ever "
             "saw. A row that merely stopped DIFFERING is not stale; it is "
             "recorded as agreeing.")

    # ``basis`` belongs in the key. The same filing is compared against more
    # than one right-hand side — a VAT return is put beside a recomputation of
    # itself AND beside účet 343 — and those two comparisons legitimately
    # carry the same row code with different figures.
    _row_uniq = models.Constraint(
        "UNIQUE (res_model, res_id, basis, code)",
        "One comparison row per row of a filing, per basis of comparison.",
    )

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

    @api.depends("code", "filing_name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s — %s" % (rec.filing_name or "", rec.code)

    def write(self, vals):
        # ``agrees`` joins ``open`` as a machine-set state: stamping the user
        # who happened to press Compare as the one who RESOLVED several
        # hundred agreeing rows is a lie the audit trail would keep.
        if "state" in vals and vals["state"] not in ("open", "agrees"):
            vals.setdefault("resolved_uid", self.env.uid)
            vals.setdefault("resolved_date", fields.Datetime.now())
        return super().write(vals)

    def action_open_filing(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self.res_model,
            "res_id": self.res_id,
            "view_mode": "form",
            "target": "current",
        }
