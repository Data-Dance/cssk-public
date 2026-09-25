from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class CSSKPartnerNettingAgreement(models.Model):
    """Mutual-offset agreement (zápočet / dohoda o vzájomnom zápočte).

    Nets a partner's open receivables against payables: on posting, a clearing
    journal entry reduces both sides by the agreed (balanced) offset amount and
    reconciles the invoices. PDF is intentionally not included yet.
    """

    _name = "cssk.partner.netting.agreement"
    _description = "Partner Netting Agreement (set-off)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "agreement_date desc, id desc"

    name = fields.Char(default="/", readonly=True, copy=False)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda s: s.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    partner_id = fields.Many2one(
        "res.partner", required=True, tracking=True,
        domain="[('parent_id', '=', False)]",
    )
    agreement_date = fields.Date(
        required=True, default=fields.Date.context_today, tracking=True
    )
    netting_mode = fields.Selection(
        [
            ("bilateral", "Bilateral agreement"),
            ("unilateral", "Unilateral set-off"),
        ],
        default="bilateral",
        required=True,
        tracking=True,
        help="Bilateral: both parties sign the agreement before it is posted.\n"
        "Unilateral: a one-sided declaration of set-off that takes legal effect "
        "on delivery to the counterparty — no countersignature required. "
        "Permitted for mutual, like-kind, due and eligible claims "
        "that are not excluded from set-off; verify these conditions hold "
        "before using it.",
    )
    responsible_user_id = fields.Many2one(
        "res.users", string="Responsible", default=lambda s: s.env.user
    )

    line_ids = fields.One2many(
        "cssk.partner.netting.agreement.line", "agreement_id"
    )
    receivable_line_ids = fields.One2many(
        "cssk.partner.netting.agreement.line", "agreement_id",
        domain=[("side", "=", "receivable")],
    )
    payable_line_ids = fields.One2many(
        "cssk.partner.netting.agreement.line", "agreement_id",
        domain=[("side", "=", "payable")],
    )

    receivable_total = fields.Monetary(
        compute="_compute_totals", store=True, currency_field="currency_id",
        help="Sum of amounts to offset on the receivable side.",
    )
    payable_total = fields.Monetary(
        compute="_compute_totals", store=True, currency_field="currency_id",
        help="Sum of amounts to offset on the payable side.",
    )
    netting_amount = fields.Monetary(
        compute="_compute_totals", store=True, currency_field="currency_id",
        help="The mutually offset amount = min(receivables, payables).",
    )
    is_balanced = fields.Boolean(compute="_compute_totals", store=True)

    clearing_journal_id = fields.Many2one(
        "account.journal", domain="[('type', '=', 'general')]",
        help="Journal for the clearing entry. Defaults to a general journal.",
    )
    move_id = fields.Many2one("account.move", readonly=True, copy=False)

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("sent", "Sent"),
            ("countersigned", "Countersigned"),
            ("posted", "Posted"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        tracking=True,
    )
    note = fields.Text()

    @api.depends(
        "line_ids.amount_to_offset", "line_ids.side",
    )
    def _compute_totals(self):
        for agr in self:
            recv = sum(
                agr.line_ids.filtered(lambda line: line.side == "receivable")
                .mapped("amount_to_offset")
            )
            pay = sum(
                agr.line_ids.filtered(lambda line: line.side == "payable")
                .mapped("amount_to_offset")
            )
            agr.receivable_total = recv
            agr.payable_total = pay
            agr.netting_amount = min(recv, pay)
            agr.is_balanced = (
                agr.currency_id.compare_amounts(recv, pay) == 0 and recv > 0
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "cssk.partner.netting.agreement"
                ) or "/"
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_confirm(self):
        self._check_state("draft")
        self.write({"state": "confirmed"})

    def action_send(self):
        self._check_state("confirmed")
        self.write({"state": "sent"})

    def action_countersigned(self):
        self._check_state("sent")
        for agr in self:
            if agr.netting_mode != "bilateral":
                raise UserError(
                    _("Countersignature applies to a bilateral agreement only; "
                      "a unilateral set-off is posted directly once sent.")
                )
        self.write({"state": "countersigned"})

    def action_reset_draft(self):
        for agr in self:
            if agr.state == "posted":
                raise UserError(
                    _("Cancel the posted agreement (with reversal) instead.")
                )
        self.write({"state": "draft"})

    def action_cancel(self):
        for agr in self:
            if agr.state == "posted":
                raise UserError(
                    _("Use 'Cancel with reversal' on a posted agreement.")
                )
        self.write({"state": "cancelled"})

    def action_post(self):
        self.ensure_one()
        required = "sent" if self.netting_mode == "unilateral" else "countersigned"
        if self.state != required:
            raise UserError(
                _("A unilateral set-off can be posted once it has been sent "
                  "(delivered) to the counterparty.")
                if self.netting_mode == "unilateral"
                else _("Only a countersigned agreement can be posted.")
            )
        if not self.is_balanced:
            raise UserError(
                _("Receivable and payable amounts to offset must be equal and "
                  "non-zero (the netting amount). Receivables=%(r)s, "
                  "payables=%(p)s.")
                % {"r": self.receivable_total, "p": self.payable_total}
            )
        # The open residuals may have shrunk since the lines were selected
        # (e.g. a payment arrived meanwhile): fail loudly rather than post a
        # clearing entry that no longer matches the signed agreement.
        for line in self.line_ids.filtered("amount_to_offset"):
            residual = line.move_line_id.amount_residual
            if self.currency_id.compare_amounts(
                line.amount_to_offset, abs(residual)
            ) > 0:
                raise UserError(
                    _("The open amount of %(move)s (%(residual)s) no longer "
                      "covers the agreed offset of %(amount)s. Update the "
                      "agreement lines.")
                    % {
                        "move": line.move_name,
                        "residual": abs(residual),
                        "amount": line.amount_to_offset,
                    }
                )
        move = self._build_clearing_move()
        move.action_post()
        self._reconcile_clearing(move)
        self.move_id = move.id
        self.state = "posted"

    def action_cancel_with_reversal(self):
        self.ensure_one()
        if self.state != "posted":
            raise UserError(_("Only a posted agreement can be reversed."))
        # Reopen the netted invoices first: drop the partials linking the
        # clearing entry to the offset items so their residuals return to
        # the pre-netting values, THEN reverse the clearing entry (which
        # reconciles clearing vs. reversal only).
        self.move_id.line_ids.remove_move_reconcile()
        self.move_id._reverse_moves(
            [{"ref": _("Reversal of zápočet %s") % self.name}],
            cancel=True,
        )
        self.state = "cancelled"

    def _check_state(self, expected):
        for agr in self:
            if agr.state != expected:
                raise UserError(
                    _("This action requires state '%(exp)s' (current: "
                      "'%(cur)s').") % {"exp": expected, "cur": agr.state}
                )

    def unlink(self):
        if any(agr.state == "posted" for agr in self):
            raise UserError(
                _("A posted netting agreement cannot be deleted. Cancel it "
                  "with reversal instead.")
            )
        return super().unlink()

    # ------------------------------------------------------------------
    # Clearing entry
    # ------------------------------------------------------------------
    def _clearing_journal(self):
        self.ensure_one()
        journal = self.clearing_journal_id or self.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", self.company_id.id)],
            limit=1,
        )
        if not journal:
            raise UserError(_("No general journal found for the clearing entry."))
        return journal

    def _build_clearing_move(self):
        """Direct offset: credit each receivable account, debit each payable
        account, by the line's amount to offset. Balances by construction."""
        self.ensure_one()
        move_lines = []
        for index, line in enumerate(
            self.line_ids.filtered(lambda l: l.amount_to_offset)
        ):
            amount = line.amount_to_offset
            ml = line.move_line_id
            common = {
                "account_id": ml.account_id.id,
                "partner_id": ml.partner_id.id,
                # One clearing line per agreement line; the sequence pins the
                # pairing used by _reconcile_clearing().
                "sequence": index,
                "name": _("Zápočet %(agr)s — %(ref)s")
                % {"agr": self.name, "ref": ml.move_id.name or ""},
            }
            if line.side == "receivable":
                common.update({"credit": amount, "debit": 0.0})
            else:
                common.update({"debit": amount, "credit": 0.0})
            move_lines.append((0, 0, common))
        return self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self._clearing_journal().id,
                "date": self.agreement_date,
                "ref": _("Zápočet %s") % self.name,
                "line_ids": move_lines,
            }
        )

    def _reconcile_clearing(self, move):
        """Reconcile each source open item with its own clearing counter-line,
        pairwise, so the per-line agreed offsets are honoured exactly.

        Pooling all lines of an account into one reconcile() call would let
        Odoo redistribute the amounts greedily (two invoices each offset
        partially would end up as one fully reconciled and one untouched).
        The clearing move is built with exactly one counter-line per
        agreement line; the clearing line's ``sequence`` is the index of its
        agreement line, which pins the pairing.
        """
        self.ensure_one()
        agreement_lines = self.line_ids.filtered("amount_to_offset")
        clearing_lines = move.line_ids.sorted(lambda l: (l.sequence, l.id))
        if len(agreement_lines) != len(clearing_lines):
            raise UserError(
                _("Clearing entry lines do not match the agreement lines.")
            )
        for agr_line, clearing_line in zip(agreement_lines, clearing_lines):
            source_line = agr_line.move_line_id
            if clearing_line.account_id != source_line.account_id:
                raise UserError(
                    _("Clearing entry lines do not match the agreement lines.")
                )
            pair = source_line + clearing_line
            pair.filtered(lambda l: not l.reconciled).reconcile()


class CSSKPartnerNettingAgreementLine(models.Model):
    _name = "cssk.partner.netting.agreement.line"
    _description = "Partner Netting Agreement Line"
    _order = "agreement_id, side, id"

    agreement_id = fields.Many2one(
        "cssk.partner.netting.agreement", required=True, ondelete="cascade",
        index=True,
    )
    company_currency_id = fields.Many2one(
        related="agreement_id.currency_id"
    )
    # ``restrict`` is DELIBERATE here, and it is the one place in this
    # localisation where it is right — so it is worth saying why, since the
    # identical declaration was wrong on the control-statement sections and on
    # the balance confirmations and was changed to ``set null`` on both.
    #
    # Those two are SNAPSHOTS: they record what was filed or sent and carry
    # their own copies of every figure, so the link is for drill-down only. A
    # netting line is not a snapshot — it is an operation on a LIVE open item,
    # and the field is ``required``, so there is no null state it could
    # meaningfully hold. Deleting a move line that a netting agreement is built
    # on would leave the agreement claiming to offset something that no longer
    # exists, which is a genuine integrity problem rather than a lost hyperlink.
    move_line_id = fields.Many2one(
        "account.move.line", required=True, ondelete="restrict"
    )
    move_name = fields.Char(related="move_line_id.move_id.name", store=True)
    side = fields.Selection(
        [("receivable", "Receivable"), ("payable", "Payable")],
        compute="_compute_side", store=True,
    )
    full_amount = fields.Monetary(
        compute="_compute_full_amount", store=True,
        currency_field="company_currency_id",
        help="Open amount of the source line (absolute).",
    )
    amount_to_offset = fields.Monetary(
        currency_field="company_currency_id",
        help="Amount of this line to offset (≤ open amount; partial allowed).",
    )

    @api.depends("move_line_id")
    def _compute_side(self):
        """Side of the set-off follows the SIGN of the open residual, not the
        account type: what matters is who owes whom.

        An open customer credit note (negative residual on a receivable
        account) is a debt WE owe the partner, so it belongs on the payable
        side of the zápočet — the clearing entry debits its account and
        clears it together with the partner's other claims. Symmetrically, a
        vendor refund/debit note (positive residual on a payable account)
        is the partner's debt to us → receivable side.

        Depends on move_line_id only (not its residual) on purpose: the side
        is fixed when the line is selected and must not flip once posting
        drives the residual to zero.
        """
        for line in self:
            ml = line.move_line_id
            if not ml:
                line.side = False
                continue
            cmp_zero = ml.company_currency_id.compare_amounts(
                ml.amount_residual, 0.0
            )
            if cmp_zero > 0:
                line.side = "receivable"
            elif cmp_zero < 0:
                line.side = "payable"
            else:
                atype = ml.account_id.account_type
                line.side = (
                    "receivable" if atype == "asset_receivable"
                    else "payable" if atype == "liability_payable"
                    else False
                )

    @api.depends("move_line_id.amount_residual")
    def _compute_full_amount(self):
        for line in self:
            line.full_amount = abs(line.move_line_id.amount_residual)

    @api.onchange("move_line_id")
    def _onchange_move_line_id(self):
        for line in self:
            if line.move_line_id and not line.amount_to_offset:
                line.amount_to_offset = abs(
                    line.move_line_id.amount_residual
                )

    @api.constrains("amount_to_offset", "move_line_id")
    def _check_amount_to_offset(self):
        for line in self:
            currency = line.move_line_id.company_currency_id
            if currency.compare_amounts(line.amount_to_offset, 0.0) <= 0:
                raise ValidationError(
                    _("The amount to offset for %s must be positive.")
                    % line.move_name
                )
            residual = abs(line.move_line_id.amount_residual)
            if currency.compare_amounts(line.amount_to_offset, residual) > 0:
                raise ValidationError(
                    _("The amount to offset for %(move)s (%(amount)s) "
                      "exceeds its open amount (%(residual)s).")
                    % {
                        "move": line.move_name,
                        "amount": line.amount_to_offset,
                        "residual": residual,
                    }
                )

    def _check_agreement_mutable(self):
        frozen = self.agreement_id.filtered(lambda a: a.state != "draft")
        if frozen:
            raise UserError(
                _("The lines of a netting agreement can only be changed in "
                  "draft (%s). Reset it to draft first.")
                % ", ".join(frozen.mapped("name"))
            )

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._check_agreement_mutable()
        return lines

    def write(self, vals):
        self._check_agreement_mutable()
        return super().write(vals)

    def unlink(self):
        self._check_agreement_mutable()
        return super().unlink()
