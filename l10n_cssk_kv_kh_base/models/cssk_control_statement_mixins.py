import re

from odoo import _, api, fields, models


class CSSKControlDrillMixin(models.AbstractModel):
    """Drill-down: every control-statement row keeps the exact account.move.lines
    behind it, so the statement is auditable down to the journal items. Concrete
    rows fill ``source_move_line_ids`` at populate time and override
    ``_drill_expected_amounts`` to declare the (base, tax) the lines should sum to.
    """

    _name = "cssk.control.drill.mixin"
    _description = "Control Statement Drill-down (mixin)"

    source_move_line_ids = fields.Many2many(
        "account.move.line", string="Source lines")
    source_reconciles = fields.Boolean(compute="_compute_source_reconciles")

    # --- manual override (preserved across recompute; mirrors the VAT return)
    # The statement's recompute is destructive (rows are wiped and
    # repopulated); rows flagged 'Override' have their amount columns
    # (``_KV_OVERRIDE_FIELDS``) snapshotted before the wipe and re-applied to
    # the repopulated row with the same ``_kv_override_key``. Overrides whose
    # row disappeared are reported in the statement chatter, never lost
    # silently (see ``cssk.control.statement._kv_reapply_overrides``).
    is_overridden = fields.Boolean(
        string="Override",
        help="Tick to manually correct this row's amounts. The correction is "
        "preserved across recompute and re-applied to the row with the same "
        "identity (partner VAT / document / rate).",
    )

    _KV_OVERRIDE_FIELDS = ()

    def _kv_override_key(self):
        """What identifies 'the same row' for override re-application across
        recomputes. Concrete mixins refine it."""
        self.ensure_one()
        return self._kv_identity()

    def _kv_override_values(self):
        self.ensure_one()
        return {f: self[f] for f in self._KV_OVERRIDE_FIELDS}

    def _drill_expected_amounts(self):
        self.ensure_one()
        return (0.0, 0.0)

    def _compute_source_reconciles(self):
        for row in self:
            base = tax = 0.0
            for line in row.source_move_line_ids:
                b, t = line._cssk_base_and_tax_amounts()
                base += b
                tax += t
            exp_base, exp_tax = row._drill_expected_amounts()
            row.source_reconciles = (
                abs(abs(base) - abs(exp_base)) < 0.01
                and abs(abs(tax) - abs(exp_tax)) < 0.01)

    def action_view_source_lines(self):
        self.ensure_one()
        view = self.env.ref(
            "l10n_cssk_kv_kh_base.view_move_line_kvkh_audit",
            raise_if_not_found=False)
        return {
            "type": "ir.actions.act_window",
            "name": _("Source documents — %s") % (
                getattr(self, "entry_ref", "") or ""),
            "res_model": "account.move.line",
            "view_mode": "list,form",
            "views": [(view.id if view else False, "list"), (False, "form")],
            "domain": [("id", "in", self.source_move_line_ids.ids)],
            "context": {"create": False, "delete": False,
                        "group_by": ["move_id"]},
        }


class CSSKControlStatementSectionMixin(models.AbstractModel):
    """Common fields for control-statement **detail** rows (one row per
    invoice/move line above the threshold). Concrete country section models
    inherit this and implement ``_populate_for_statement``.
    """

    _name = "cssk.control.statement.section.mixin"
    _inherit = "cssk.control.drill.mixin"
    _description = "Control Statement Detail Row (mixin)"

    def _drill_expected_amounts(self):
        self.ensure_one()
        return (self.tax_base_amount, self.tax_amount)

    statement_id = fields.Many2one(
        "cssk.control.statement", required=True, ondelete="cascade", index=True
    )
    # ``set null`` rather than ``restrict``, and the reasoning matters because
    # ``restrict`` is the intuitive choice here and it is wrong.
    #
    # A section row is a SNAPSHOT: it stores its own partner VAT, entry
    # reference, supply date and amounts, precisely so that what was filed
    # stays readable after the underlying documents move on. It does not need
    # the move line to survive in order to remain a true record of the filing —
    # the link is for drill-down, not for the data.
    #
    # ``restrict`` made every computed statement PIN the documents it reported,
    # so a document could never be deleted or re-imported once any statement
    # had been computed over it — including a ``preview`` statement that was
    # never filed. For an importer whose whole method is reload-and-remeasure
    # that is workflow-ending, and it bit both localisations independently
    # within one session: `l10n_cz_kh_a2` blocked a Money S4 rollback, and
    # `l10n_sk_kv_dph_section_b2` blocked one on the i6 agenda. The workaround
    # both times was to delete section rows by hand and recompute afterwards,
    # which is exactly the data loss ``restrict`` was supposed to prevent, done
    # manually and under time pressure.
    #
    # With ``set null`` a filed statement keeps every figure it reported and
    # merely loses the ability to jump to a line that no longer exists.
    # ``move_id`` is a stored related on this field and is itself a plain
    # many2one, so it nulls out through its own foreign key; nothing is left
    # pointing at a deleted record.
    move_line_id = fields.Many2one("account.move.line", ondelete="set null")
    move_id = fields.Many2one(related="move_line_id.move_id", store=True)

    partner_id = fields.Many2one("res.partner")
    partner_vat = fields.Char()  # snapshot at statement time
    partner_vat_stripped = fields.Char()  # without country prefix
    partner_country_code = fields.Char(size=2)

    entry_ref = fields.Char()
    entry_ref_xml = fields.Char(
        compute="_compute_entry_ref_xml",
        help="The reference as the STATEMENT can carry it: the KV DPH schema "
             "types it '\\S{1,32}', which forbids whitespace outright.",
    )
    entry_ref_original_xml = fields.Char(compute="_compute_entry_ref_xml")

    @api.depends("entry_ref", "entry_ref_original")
    def _compute_entry_ref_xml(self):
        r"""Whitespace removed, because the form cannot carry any.

        `kv_dph_2023.xsd` and `kv_dph_2025.xsd` both type the document
        reference as ``\S{1,32}``. A space is not merely discouraged, it is
        unrepresentable — so the choice is to normalise or to refuse the
        filing, and a real accepted filing settles which: the customer's own
        KV row for `PGGR - 2024/05/110` went to the tax office as
        **`PGGR-2024/05/110`**, spaces removed, and was accepted.

        The STORED `entry_ref` deliberately keeps the source's spelling — it
        is what drill-down and every comparison match on. Only the XML view is
        normalised, because only the XML has the constraint.

        Found the first time a KV export was validated against a real schema
        rather than skipping it: 26 of 175 counterparty references in two years
        carry whitespace, so this blocked a large share of periods and did so
        silently, because until the missing-schema fix the assertion never ran.
        """
        for row in self:
            row.entry_ref_xml = self._cssk_ref_for_xml(row.entry_ref)
            row.entry_ref_original_xml = self._cssk_ref_for_xml(
                row.entry_ref_original)

    @api.model
    def _cssk_ref_for_xml(self, value):
        r"""Strip every whitespace character; leave the rest alone.

        NOT a general sanitiser. The schema's own pattern is the specification
        and it objects to exactly one thing, so this removes exactly that. A
        reference too long for the pattern is a different problem and is
        reported by the kontroly rather than truncated here — silently
        shortening a reference the tax office cross-matches against the
        supplier's own filing would break the match it exists for.
        """
        if not value:
            return value
        return re.sub(r"\s+", "", value)
    entry_ref_original = fields.Char(
        help="Reference of the original document for corrections "
        "(SK C.1/C.2, CZ negative rows)."
    )
    supply_date = fields.Date()

    company_currency_id = fields.Many2one(related="statement_id.currency_id")
    tax_base_amount = fields.Monetary(currency_field="company_currency_id")
    tax_amount = fields.Monetary(currency_field="company_currency_id")
    deducted_amount = fields.Monetary(currency_field="company_currency_id")
    tax_rate = fields.Float()
    kod_opravy = fields.Selection(
        [("1", "Cancellation (original data)"), ("2", "New / corrected data")],
        help="Correction code — filled only in an amended KV DPH "
             "(1 = cancellation of the original data, 2 = new / corrected data).")

    # --- manual override: identity + the editable amount columns ----------
    _KV_OVERRIDE_FIELDS = (
        "tax_base_amount", "tax_amount", "deducted_amount")

    def _kv_override_key(self):
        # (partner_vat, entry_ref) + the rate: one invoice can legitimately
        # yield several detail rows (one per rate band), so the rate is part
        # of what makes an override row-specific.
        self.ensure_one()
        return self._kv_identity() + (round(self.tax_rate or 0.0, 2),)

    # --- dodatočný-KV delta matching (see _apply_dodatocny_delta) ----------
    def _kv_identity(self):
        """What makes two rows the *same* document (invoice) across statements."""
        self.ensure_one()
        return (self.partner_vat or "", self._kv_identity_ref() or "")

    def _kv_identity_ref(self):
        """The document reference as it identifies the row.

        The stored spelling here. A form that cannot carry some characters —
        the Slovak KV DPH types it ``\\S{1,32}`` — identifies its rows by
        what it CAN carry, and overrides this; the Czech KH writes
        ``c_evid_dd`` as stored, so whitespace there may tell two documents
        apart and must not be dropped.
        """
        self.ensure_one()
        return self.entry_ref

    def _kv_values(self):
        """The figures that decide whether the document *changed*."""
        self.ensure_one()
        return (round(self.tax_base_amount, 2), round(self.tax_amount, 2),
                round(self.tax_rate, 2), round(self.deducted_amount, 2),
                self.entry_ref_original or "")

    _KV_SNAPSHOT_FIELDS = [
        "partner_id", "partner_vat", "partner_vat_stripped",
        "partner_country_code", "entry_ref", "entry_ref_original",
        "supply_date", "tax_base_amount", "tax_amount", "tax_rate",
        "deducted_amount"]

    def _kv_snapshot(self):
        """JSON-safe snapshot: identity, comparison values, and create-vals (so a
        storno can be recreated from it without the live record)."""
        self.ensure_one()
        vals = {}
        for f in self._KV_SNAPSHOT_FIELDS:
            v = self[f]
            if isinstance(v, models.BaseModel):
                v = v.id or False
            elif hasattr(v, "isoformat"):
                v = v.isoformat()
            vals[f] = v
        return {"id": list(self._kv_identity()), "v": list(self._kv_values()),
                "vals": vals}

    @api.model
    def _populate_for_statement(self, statement, section_code):
        """Create this section's rows for ``statement``. Country override."""
        raise NotImplementedError(
            "Concrete section %s must implement _populate_for_statement"
            % self._name
        )

    @api.model
    def _eligible_move_lines(self, statement, section_code):
        """Posted move lines in the period tagged with this section code."""
        # Period by tax point, shared with the VAT return -- a control
        # statement reconciles against it, so the two must agree on what the
        # period contains.
        move_ids = statement._cssk_period_move_ids(
            statement.company_id, statement.date_from, statement.date_to
        )
        if not move_ids:
            return self.env["account.move.line"]
        return self.env["account.move.line"].search(
            [
                ("parent_state", "=", "posted"),
                ("company_id", "=", statement.company_id.id),
                ("move_id", "in", move_ids),
                ("cssk_control_section_code", "=", section_code.code),
            ]
        )


class CSSKControlStatementSummaryMixin(models.AbstractModel):
    """Common fields for **aggregated** rows (below-threshold totals: SK B.3.1,
    CZ A.5/B.3)."""

    _name = "cssk.control.statement.summary.mixin"
    _inherit = "cssk.control.drill.mixin"
    _description = "Control Statement Aggregated Row (mixin)"

    def _drill_expected_amounts(self):
        self.ensure_one()
        return (self.total_tax_base, self.total_tax_amount)

    statement_id = fields.Many2one(
        "cssk.control.statement", required=True, ondelete="cascade", index=True
    )
    partner_id = fields.Many2one("res.partner")  # null if 'single' aggregation
    partner_vat = fields.Char()
    company_currency_id = fields.Many2one(related="statement_id.currency_id")
    total_tax_base = fields.Monetary(currency_field="company_currency_id")
    total_tax_amount = fields.Monetary(currency_field="company_currency_id")
    total_deducted_amount = fields.Monetary(currency_field="company_currency_id")
    row_count = fields.Integer()
    kod_opravy = fields.Selection(
        [("1", "Cancellation (original data)"), ("2", "New / corrected data")],
        help="Correction code — filled only in an amended KV DPH "
             "(1 = cancellation of the original data, 2 = new / corrected data).")

    # --- manual override: identity + the editable amount columns ----------
    _KV_OVERRIDE_FIELDS = (
        "total_tax_base", "total_tax_amount", "total_deducted_amount")

    # --- dodatočný-KV delta matching (see _apply_dodatocny_delta) ----------
    def _kv_identity(self):
        self.ensure_one()
        return (self.partner_vat or "",)

    def _kv_values(self):
        self.ensure_one()
        return (round(self.total_tax_base, 2), round(self.total_tax_amount, 2),
                round(self.total_deducted_amount, 2))

    _KV_SNAPSHOT_FIELDS = [
        "partner_id", "partner_vat", "total_tax_base", "total_tax_amount",
        "total_deducted_amount", "row_count"]

    def _kv_snapshot(self):
        self.ensure_one()
        vals = {}
        for f in self._KV_SNAPSHOT_FIELDS:
            v = self[f]
            if isinstance(v, models.BaseModel):
                v = v.id or False
            elif hasattr(v, "isoformat"):
                v = v.isoformat()
            vals[f] = v
        return {"id": list(self._kv_identity()), "v": list(self._kv_values()),
                "vals": vals}

    @api.model
    def _populate_for_statement(self, statement, section_code):
        raise NotImplementedError(
            "Concrete section %s must implement _populate_for_statement"
            % self._name
        )

    @api.model
    def _eligible_move_lines(self, statement, section_code):
        """Posted base lines in the period tagged with this section code."""
        # Period by tax point, shared with the VAT return -- a control
        # statement reconciles against it, so the two must agree on what the
        # period contains.
        move_ids = statement._cssk_period_move_ids(
            statement.company_id, statement.date_from, statement.date_to
        )
        if not move_ids:
            return self.env["account.move.line"]
        return self.env["account.move.line"].search(
            [
                ("parent_state", "=", "posted"),
                ("company_id", "=", statement.company_id.id),
                ("move_id", "in", move_ids),
                ("cssk_control_section_code", "=", section_code.code),
            ]
        )


class CSSKControlStatementReconciliationMixin(models.AbstractModel):
    """Common fields for **reconciliation** rows (fixed lookup-keyed lines that
    are neither detail nor partner-aggregated, e.g. CZ section C: 8 lines
    reconciled against the VAT return)."""

    _name = "cssk.control.statement.reconciliation.mixin"
    _description = "Control Statement Reconciliation Row (mixin)"

    statement_id = fields.Many2one(
        "cssk.control.statement", required=True, ondelete="cascade", index=True
    )
    company_currency_id = fields.Many2one(related="statement_id.currency_id")
    amount = fields.Monetary(currency_field="company_currency_id")

    @api.model
    def _populate_for_statement(self, statement, section_code):
        raise NotImplementedError(
            "Concrete section %s must implement _populate_for_statement"
            % self._name
        )
