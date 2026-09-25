from odoo import _, api, fields, models
from odoo.tools.translate import LazyTranslate
from odoo.exceptions import UserError

_lt = LazyTranslate(__name__)


class CSSKEcSummaryStatement(models.Model):
    """EC sales list (Súhrnný výkaz / Souhrnné hlášení).

    One aggregated line per (member-state, customer VAT, transaction code).
    """

    _name = "cssk.ec.summary.statement"
    _description = "EC Sales List"
    # Two mixins, two concerns, both wanted: the statutory one retains the
    # filed copy, the submittable one tracks whether it arrived and holds what
    # came back. Neither substitutes for the other — a daňová kontrola asks for
    # the doručenka, which only the second can produce.
    _inherit = ["mail.thread", "mail.activity.mixin",
                "cssk.statutory.submission.mixin",
                "cssk.submittable.mixin"]
    _order = "date_from desc, id desc"

    name = fields.Char(compute="_compute_name")
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda s: s.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    country_id = fields.Many2one(
        related="company_id.account_fiscal_country_id", store=True
    )

    version_id = fields.Many2one(
        "cssk.ec.summary.statement.version",
        required=True,
        domain="[('country_id', '=', country_id),"
        " ('valid_from', '<=', date_to),"
        " '|', ('valid_to', '=', False), ('valid_to', '>=', date_from)]",
        # The dropdown must offer an ARCHIVED vintage too. The domain
        # above already scopes by period, so a 2026 filing never sees
        # the 2014 vzor anyway — archiving is a way of tidying the
        # configuration list, and it must not quietly make an old
        # period unenterable or a historical filing un-repointable.
        context={'active_test': False},
    )

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    period_type = fields.Selection(
        [("month", "Monthly"), ("quarter", "Quarterly")], required=True
    )
    statement_type_id = fields.Many2one(
        "cssk.ec.summary.statement.type",
        domain="[('version_id', '=', version_id)]",
        required=True,
    )

    line_ids = fields.One2many(
        "cssk.ec.summary.statement.line", "statement_id"
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("preview", "Preview"),
            ("exported", "Exported"),
            ("submitted", "Submitted"),
            ("cancelled", "Cancelled"),
            # Terminal, and off the workflow rather than at the end of it. A
            # historical filing was completed and submitted years ago by
            # whoever ran the previous system; it is a RECORD of a filing, not
            # a filing in progress, so no transition leads into or out of it.
            # Set automatically whenever ``legacy`` is set — see
            # ``cssk.statutory.submission.mixin``, which owns that rule so the
            # importer cannot set one without the other.
            ("legacy", "Historical filing"),
        ],
        default="draft",
        tracking=True,
    )
    xml_attachment_id = fields.Many2one("ir.attachment", readonly=True)
    original_return_id = fields.Many2one(
        "cssk.ec.summary.statement", string="Amends", copy=False, readonly=True,
        index=True,
        help="The originally-filed statement this amended / corrective statement amends.")
    amendment_ids = fields.One2many(
        "cssk.ec.summary.statement", "original_return_id", string="Amendments")

    @api.depends("date_from", "date_to")
    def _compute_name(self):
        for st in self:
            st.name = "SV/SHV %s — %s" % (
                st.date_from or "",
                st.date_to or "",
            )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    def action_compute_lines(self):
        self._cssk_check_not_legacy(_("recomputed"))
        self.ensure_one()
        if self.state not in ("draft", "preview"):
            raise UserError(_("Only draft statements can be recomputed."))
        # Preserve manual overrides across the (destructive) recompute —
        # mirrors the VAT return: snapshot the user-edited rows keyed by
        # (country, VAT, transaction code), re-apply them onto the matching
        # repopulated rows, and report any override whose row no longer
        # exists in the chatter (never lose an edit silently).
        overrides = {
            line._cssk_ec_override_key(): line.manual_value
            for line in self.line_ids
            if line.is_overridden
        }
        self.line_ids.unlink()
        lines = self.env["cssk.ec.summary.statement.line"].create(
            self._compute_line_values()
        )
        self._cssk_reapply_line_overrides(lines, overrides)
        self.state = "preview"

    def _cssk_reapply_line_overrides(self, lines, overrides):
        """Re-apply the snapshotted manual overrides onto the freshly
        repopulated ``lines``; post a chatter warning listing the overrides
        whose (country, VAT, code) combination disappeared."""
        self.ensure_one()
        remaining = dict(overrides)
        for line in lines:
            key = line._cssk_ec_override_key()
            if key in remaining:
                manual = remaining.pop(key)
                line.write({
                    "is_overridden": True,
                    "manual_value": manual,
                    "total_amount": manual,
                })
        if remaining:
            self.message_post(body=_(
                "Recompute dropped %(count)s manual override(s) whose row no "
                "longer exists in the recomputed statement:\n%(rows)s",
                count=len(remaining),
                rows="\n".join(
                    "  • %s / %s / kód %s (manual %.2f)"
                    % (key[0] or "??", key[1] or "—", key[2] or "—", manual)
                    for key, manual in sorted(remaining.items()))))
        return remaining

    def _eligible_move_lines(self):
        self.ensure_one()
        return self.env["account.move.line"].search(
            [
                ("parent_state", "=", "posted"),
                ("company_id", "=", self.company_id.id),
                ("move_id", "in", self._cssk_period_move_ids(
                    self.company_id, self.date_from, self.date_to)),
                ("tax_ids.cssk_ec_summary_code", "!=", False),
            ]
        )

    def _compute_line_values(self):
        """Aggregate eligible lines per (country, VAT, transaction code).
        Country modules can refine ``account.move.line._cssk_ec_*`` hooks."""
        self.ensure_one()
        groups = {}
        for ml in self._eligible_move_lines():
            code = ml._cssk_ec_transaction_code()
            if not code:
                continue
            partner = ml.partner_id.commercial_partner_id
            key = (partner.country_id.code or "", ml._cssk_ec_partner_vat(), code)
            grp = groups.get(key)
            if grp is None:
                grp = groups[key] = {
                    "amount": 0.0, "moves": set(),
                    "lines": self.env["account.move.line"]}
            grp["amount"] += ml._cssk_ec_amount()
            grp["moves"].add(ml.move_id.id)
            grp["lines"] |= ml
        return [
            {
                "statement_id": self.id,
                "partner_country_code": country,
                "partner_vat": vat,
                "transaction_code": code,
                "total_amount": data["amount"],
                "supplies_count": len(data["moves"]),
                "source_move_line_ids": [(6, 0, data["lines"].ids)],
            }
            for (country, vat, code), data in groups.items()
        ]

    # ------------------------------------------------------------------
    # Export — the pipeline lives in cssk.statutory.submission.mixin;
    # only the form-specific hooks are parameterized here. The EC list's
    # kontroly stage additionally runs the VIES gate (this base always ran
    # its content checks BEFORE rendering — that order is now the shared
    # standard).
    # ------------------------------------------------------------------
        #: LAZY, not a plain string. This names the form in error messages and
    #: on the comparison screen, and as a bare literal it was in no .pot at
    #: all — untranslatable in every language, not merely untranslated.
    #: ``_lt`` defers the lookup to render time, which is what lets a
    #: module-level constant be translated at all; render it with
    #: ``self.env._(...)`` so it picks up the READER's language.
    _cssk_form_label = _lt("EC sales list")
    _cssk_xml_name_fallback = "ec_sales_list"

    def _cssk_check_kontroly(self):
        self.ensure_one()
        self._check_vies()
        self._cssk_enforce_kontroly()
        return True

    def _cssk_render_context(self):
        ctx = super()._cssk_render_context()
        ctx["lines"] = self.line_ids
        return ctx

    # ------------------------------------------------------------------
    # kontrolné pravidlá (content checks the XSD cannot perform)
    # ------------------------------------------------------------------
    def _kontroly_valid_codes(self):
        """Country modules return the set of allowed kód plnenia, or None."""
        return None

    def check_kontroly(self):
        """Return ``[{code, severity, desc, detail}]`` — empty = clean.

        Each riadok of the súhrnný výkaz carries a kód plnenia; per the FS SR
        poučenie only the defined codes are accepted (XSD-valid free text would
        be portal-rejected). VAT presence/format/EU membership is enforced
        separately by ``_check_vies`` (a hard block).
        """
        self.ensure_one()
        out = []
        valid = self._kontroly_valid_codes()
        if valid is not None:
            for line in self.line_ids:
                if (line.transaction_code or "") not in valid:
                    out.append({
                        "code": "SV_KOD", "severity": "error",
                        "desc": "kód plnenia musí byť jeden z %s" % sorted(valid),
                        "detail": "%s / %s: neplatný kód %r" % (
                            line.partner_country_code, line.partner_vat,
                            line.transaction_code)})
        return out

    def _check_vies(self):
        """Mandatory preflight — every reported line must carry an EU VAT.

        This is a presence/format gate; wire a real VIES network validation
        here for live filing. A submitted EC list with an invalid VAT is
        penalised, so this is a **hard block**, not a warning.
        """
        self.ensure_one()
        eu = self.env.ref("base.europe", raise_if_not_found=False)
        eu_codes = set(eu.country_ids.mapped("code")) if eu else set()
        invalid = []
        for line in self.line_ids:
            vat = line.partner_vat or ""
            if (
                len(vat) < 3
                or not vat[:2].isalpha()
                or (eu_codes and line.partner_country_code not in eu_codes)
            ):
                invalid.append(
                    "%s / %s"
                    % (line.partner_country_code or "??", vat or "—")
                )
        if invalid:
            raise UserError(
                _(
                    "EC sales list cannot be exported — these lines have a "
                    "missing or non-EU VAT number (hard block; connect a VIES "
                    "validation step for live filing):\n%s"
                )
                % "\n".join(invalid)
            )


    def _cssk_comparable_rows(self):
        """Per-COUNTERPARTY comparison.

        A súhrnný výkaz reports one line per (country, IČ DPH, kód) and the
        figure is that counterparty's total for the period, so "the same row"
        is the counterparty — which is also the key the recompute re-applies
        an override to, and the key VIES checks against. Same key, one notion.

        ``supplies_count`` is deliberately NOT compared: how many documents
        make up a counterparty's total is our bookkeeping, not something a
        filed výkaz states, and a filing staged without it would show every
        row as differing.
        """
        self.ensure_one()
        return {
            (_("Line"), (line.partner_country_code or "",
                         line.partner_vat or "",
                         line.transaction_code or "")): (
                round(line.total_amount, 2),)
            for line in self.line_ids
        }


class CSSKEcSummaryStatementLine(models.Model):
    _name = "cssk.ec.summary.statement.line"
    _description = "EC Sales List Line"
    _order = "partner_country_code, partner_vat, transaction_code"

    statement_id = fields.Many2one(
        "cssk.ec.summary.statement", required=True, ondelete="cascade",
        index=True,
    )
    company_currency_id = fields.Many2one(related="statement_id.currency_id")
    partner_country_code = fields.Char(size=2, required=True)
    partner_vat = fields.Char(required=True)
    transaction_code = fields.Char(required=True)
    total_amount = fields.Monetary(
        currency_field="company_currency_id",
        help="Effective reported value: the computed aggregate, or the "
        "manual override.",
    )
    supplies_count = fields.Integer()

    # --- manual override (preserved across recompute; mirrors the VAT return)
    is_overridden = fields.Boolean(
        string="Override",
        help="Tick to enter a manual value for this row — used to correct "
        "the reported hodnota (e.g. an external correction not yet booked). "
        "The value is preserved across recompute and re-applied to the row "
        "with the same country / VAT / transaction code.",
    )
    manual_value = fields.Monetary(
        currency_field="company_currency_id",
        help="Manual value applied when 'Override' is ticked.",
    )

    def _cssk_ec_override_key(self):
        """What identifies 'the same row' across recomputes."""
        self.ensure_one()
        return (self.partner_country_code or "", self.partner_vat or "",
                self.transaction_code or "")

    @api.onchange("is_overridden", "manual_value")
    def _onchange_override(self):
        for line in self:
            if line.is_overridden:
                line.total_amount = line.manual_value

    # --- drill-down: the EU-supply journal items behind this record ---
    source_move_line_ids = fields.Many2many(
        "account.move.line", string="Source lines")
    source_reconciles = fields.Boolean(compute="_compute_source_reconciles")

    @api.depends("source_move_line_ids", "total_amount")
    def _compute_source_reconciles(self):
        for line in self:
            if not line.source_move_line_ids:
                line.source_reconciles = False
            else:
                s = sum(ml._cssk_ec_amount() for ml in line.source_move_line_ids)
                line.source_reconciles = abs(abs(s) - abs(line.total_amount)) < 0.5

    def action_view_source_lines(self):
        self.ensure_one()
        view = self.env.ref(
            "l10n_cssk_ec_summary_base.view_move_line_ec_audit",
            raise_if_not_found=False)
        return {
            "type": "ir.actions.act_window",
            "name": _("Source documents — %s / code %s") % (
                self.partner_vat or "", self.transaction_code or ""),
            "res_model": "account.move.line",
            "view_mode": "list,form",
            "views": [(view.id if view else False, "list"), (False, "form")],
            "domain": [("id", "in", self.source_move_line_ids.ids)],
            "context": {"create": False, "delete": False,
                        "group_by": ["move_id"]},
        }
