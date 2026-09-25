from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CSSKPartnerConfirmation(models.Model):
    """Partner balance confirmation (saldokonto / odsúhlasenie zostatkov)."""

    _name = "cssk.partner.confirmation"
    _description = "Partner Balance Confirmation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "as_of_date desc, id desc"

    name = fields.Char(default="/", readonly=True, copy=False)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda s: s.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    partner_id = fields.Many2one(
        "res.partner", required=True, tracking=True,
        domain="[('parent_id', '=', False)]",
    )
    partner_contact_id = fields.Many2one(
        "res.partner", string="Contact",
        domain="['|', ('id', '=', partner_id), ('parent_id', '=', partner_id)]",
        help="Person at the partner to address the confirmation to.",
    )
    responsible_user_id = fields.Many2one(
        "res.users", string="Responsible",
        default=lambda s: s.env.user, tracking=True,
    )

    as_of_date = fields.Date(
        required=True, default=fields.Date.context_today, tracking=True
    )
    confirmation_type = fields.Selection(
        [
            ("receivable", "Receivables only"),
            ("payable", "Payables only"),
            ("both", "Receivables and payables"),
        ],
        default="both",
        required=True,
    )

    line_ids = fields.One2many(
        "cssk.partner.confirmation.line", "confirmation_id"
    )

    total_receivable = fields.Monetary(
        compute="_compute_totals", store=True, currency_field="currency_id"
    )
    total_payable = fields.Monetary(
        compute="_compute_totals", store=True, currency_field="currency_id"
    )
    net_balance = fields.Monetary(
        compute="_compute_totals", store=True, currency_field="currency_id",
        help="Receivables − payables (positive = partner owes us).",
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("sent", "Sent"),
            ("agreed", "Agreed"),
            ("disputed", "Disputed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        tracking=True,
    )
    note = fields.Text()

    @api.depends(
        "line_ids.amount_residual", "line_ids.account_type",
        "line_ids.blocked",
    )
    def _compute_totals(self):
        for conf in self:
            active = conf.line_ids.filtered(lambda line: not line.blocked)
            recv = active.filtered(
                lambda line: line.account_type == "asset_receivable"
            )
            pay = active.filtered(
                lambda line: line.account_type == "liability_payable"
            )
            conf.total_receivable = sum(recv.mapped("amount_residual"))
            conf.total_payable = -sum(pay.mapped("amount_residual"))
            conf.net_balance = conf.total_receivable - conf.total_payable

    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "cssk.partner.confirmation"
                ) or "/"
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------
    def action_compute_lines(self):
        for conf in self:
            if conf.state not in ("draft", "sent"):
                raise UserError(
                    _("Only draft/sent confirmations can be recomputed.")
                )
            conf.line_ids.unlink()
            self.env["cssk.partner.confirmation.line"].create(
                conf._collect_open_lines()
            )

    def _open_line_account_types(self):
        self.ensure_one()
        return {
            "receivable": ["asset_receivable"],
            "payable": ["liability_payable"],
            "both": ["asset_receivable", "liability_payable"],
        }[self.confirmation_type]

    @api.model
    def _open_items_domain(self, company, account_types, as_of_date):
        """Domain for journal items that *may* have been open on
        ``as_of_date``: dated on/before it and either still unreconciled
        today, or (fully/partially) matched only after that date."""
        return [
            ("parent_state", "=", "posted"),
            ("company_id", "=", company.id),
            ("account_id.account_type", "in", account_types),
            ("date", "<=", as_of_date),
            "|", "|",
            ("amount_residual", "!=", 0.0),
            ("matched_debit_ids.max_date", ">", as_of_date),
            ("matched_credit_ids.max_date", ">", as_of_date),
        ]

    def _residual_as_of(self, line):
        """Reconstruct ``line``'s residual as it stood on ``as_of_date``:
        today's residual with every partial reconciliation applied after
        that date added back (the OCA open-items pattern).

        Returns (residual_company_currency, residual_line_currency).
        """
        self.ensure_one()
        residual = line.amount_residual
        residual_currency = line.amount_residual_currency
        # Partials where this line is the debit side reduced its residual.
        for partial in line.matched_credit_ids:
            if partial.max_date > self.as_of_date:
                residual += partial.amount
                residual_currency += partial.debit_amount_currency
        # Partials where this line is the credit side pushed its (negative)
        # residual towards zero.
        for partial in line.matched_debit_ids:
            if partial.max_date > self.as_of_date:
                residual -= partial.amount
                residual_currency -= partial.credit_amount_currency
        return residual, residual_currency

    def _collect_open_lines(self):
        """Snapshot the partner's AR/AP items open *as of* ``as_of_date``.

        An item is open as of D if its residual AT D is non-zero — payments
        or reconciliations booked after D (e.g. a 31.12 confirmation
        generated in February, invoice paid in January) must not hide items
        that were still open on D.
        """
        self.ensure_one()
        commercial = self.partner_id.commercial_partner_id
        lines = self.env["account.move.line"].search(
            [
                ("partner_id.commercial_partner_id", "=", commercial.id),
            ]
            + self._open_items_domain(
                self.company_id,
                self._open_line_account_types(),
                self.as_of_date,
            )
        )
        vals = []
        for line in lines:
            residual, residual_currency = self._residual_as_of(line)
            if line.company_currency_id.is_zero(residual):
                continue
            vals.append(
                {
                    "confirmation_id": self.id,
                    "move_line_id": line.id,
                    "move_name": line.move_id.name,
                    "move_date": line.date,
                    "date_maturity": line.date_maturity,
                    "account_type": line.account_id.account_type,
                    "amount_residual": residual,
                    "amount_residual_currency": residual_currency,
                    "line_currency_id": line.currency_id.id,
                }
            )
        return vals

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def _check_state(self, *allowed):
        for conf in self:
            if conf.state not in allowed:
                raise UserError(
                    _("This action requires state %(exp)s (current: "
                      "'%(cur)s').")
                    % {
                        "exp": " / ".join("'%s'" % s for s in allowed),
                        "cur": conf.state,
                    }
                )

    def action_send(self):
        self._check_state("draft")
        self.write({"state": "sent"})

    def action_agreed(self):
        self._check_state("sent")
        self.write({"state": "agreed"})

    def action_disputed(self):
        self._check_state("sent")
        self.write({"state": "disputed"})

    def action_reset_draft(self):
        self._check_state("sent", "agreed", "disputed")
        self.write({"state": "draft"})

    def action_cancel(self):
        self._check_state("draft", "sent", "agreed", "disputed")
        self.write({"state": "cancelled"})

    def unlink(self):
        if any(conf.state in ("agreed", "disputed") for conf in self):
            raise UserError(
                _("An agreed or disputed confirmation is a statutory record "
                  "and cannot be deleted. Cancel it instead.")
            )
        return super().unlink()

    def action_print(self):
        self.ensure_one()
        return self.env.ref(
            "l10n_cssk_partner_balances.action_report_partner_confirmation"
        ).report_action(self)


class CSSKPartnerConfirmationLine(models.Model):
    _name = "cssk.partner.confirmation.line"
    _description = "Partner Balance Confirmation Line"
    _order = "confirmation_id, move_date, id"

    confirmation_id = fields.Many2one(
        "cssk.partner.confirmation", required=True, ondelete="cascade",
        index=True,
    )
    company_currency_id = fields.Many2one(
        related="confirmation_id.currency_id"
    )
    # Source link + snapshot fields. ``set null``, NOT ``restrict``: what makes
    # the snapshot survive is that the fields below are STORED, not that the
    # foreign key refuses the delete. The comment here used to claim otherwise
    # and the claim is self-refuting — ``move_name``, ``move_date``,
    # ``date_maturity`` and the amounts are all copies precisely so the
    # confirmation stays readable once the ledger has moved on.
    #
    # What ``restrict`` actually bought was a confirmation PINNING every line it
    # sampled, so no sampled document could be deleted or re-imported
    # afterwards. Same defect as the control-statement sections, where it cost
    # real time in both localisations; see
    # ``cssk.control.statement.section.mixin`` for the full account.
    move_line_id = fields.Many2one("account.move.line", ondelete="set null")
    move_name = fields.Char()
    move_date = fields.Date()
    date_maturity = fields.Date()
    account_type = fields.Selection(
        [("asset_receivable", "Receivable"), ("liability_payable", "Payable")]
    )
    amount_residual = fields.Monetary(currency_field="company_currency_id")
    amount_residual_currency = fields.Monetary(
        currency_field="line_currency_id"
    )
    line_currency_id = fields.Many2one("res.currency")
    blocked = fields.Boolean(
        help="Disputed item: excluded from totals but still shown on the PDF.",
    )

    def _check_confirmation_mutable(self):
        frozen = self.confirmation_id.filtered(
            lambda c: c.state in ("agreed", "disputed")
        )
        if frozen:
            raise UserError(
                _("The lines of an agreed or disputed confirmation are "
                  "frozen (%s). Reset it to draft first.")
                % ", ".join(frozen.mapped("name"))
            )

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._check_confirmation_mutable()
        return lines

    def write(self, vals):
        self._check_confirmation_mutable()
        return super().write(vals)

    def unlink(self):
        self._check_confirmation_mutable()
        return super().unlink()
