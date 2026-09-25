# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The register of wage-garnishment orders (exekuční / exekučný príkaz).

One record is one order served on the employer: who is collecting, under
which case number, from which day it ranks (*pořadí* / *poradie*), how much
is owed and how much has already been remitted. The payroll bridges read
this register when they compute a payslip; the accounting bridge turns the
resulting lines into a payable to the bailiff.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .garnishment_calc import (
    CLASS_FINE,
    CLASS_MAINTENANCE,
    CLASS_ORDINARY,
    CLASS_PRIORITY,
    Claim,
    compute_cz,
    compute_sk,
)

CLAIM_CLASS_SELECTION = [
    (CLASS_MAINTENANCE, "Maintenance (výživné)"),
    (CLASS_PRIORITY, "Priority (přednostní / prednostná)"),
    (CLASS_FINE, "Administrative fine (pokuta za priestupok)"),
    (CLASS_ORDINARY, "Ordinary (nepřednostní / neprednostná)"),
]


class HrWageGarnishment(models.Model):
    _name = "hr.wage.garnishment"
    _description = "Wage Garnishment Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_delivered, sequence, id"
    _rec_name = "case_number"

    _check_amounts = models.Constraint(
        "CHECK (total_amount >= 0 AND monthly_amount >= 0)",
        "Garnishment amounts may not be negative.",
    )
    _check_dates = models.Constraint(
        "CHECK (date_end IS NULL OR date_start IS NULL OR date_start <= date_end)",
        "The end date may not precede the start date.",
    )

    case_number = fields.Char(
        "Case Number",
        required=True,
        tracking=True,
        help="Spisová značka of the execution order, used as the variable "
        "symbol when the deduction is remitted.",
    )
    employee_id = fields.Many2one(
        "hr.employee", required=True, index=True, tracking=True, ondelete="restrict"
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id")
    country_code = fields.Char(
        related="company_id.country_id.code", string="Country Code", store=True
    )
    sequence = fields.Integer(
        default=10,
        help="Tie-break within the same delivery date. Orders delivered on "
        "the same day rank equally and are satisfied pro rata; use this only "
        "when the bailiff has established an explicit order.",
    )

    # --- legal classification --------------------------------------------
    garnishment_type = fields.Selection(
        [
            ("execution", "Court execution (exekuce / exekúcia)"),
            ("insolvency", "Insolvency (insolvence / oddlženie)"),
            ("agreement", "Agreement (dohoda o srážkách ze mzdy)"),
            ("administrative", "Administrative enforcement (správní exekuce)"),
        ],
        required=True,
        default="execution",
        tracking=True,
    )
    claim_class = fields.Selection(
        CLAIM_CLASS_SELECTION,
        required=True,
        default=CLASS_ORDINARY,
        tracking=True,
        help="Drives how deep the claim may reach into the net wage. "
        "Priority claims take two thirds, ordinary claims one.",
    )
    date_delivered = fields.Date(
        "Delivered On",
        required=True,
        tracking=True,
        help="Day the order was served on the employer. This — not the date "
        "of the decision — establishes the rank (pořadí) of the claim.",
    )

    # --- parties ----------------------------------------------------------
    creditor_partner_id = fields.Many2one(
        "res.partner",
        "Creditor",
        tracking=True,
        help="Oprávněný / oprávnený — the party the debt is owed to.",
    )
    bailiff_partner_id = fields.Many2one(
        "res.partner",
        "Bailiff",
        tracking=True,
        help="Soudní exekutor / súdny exekútor administering the case. When "
        "set, the deduction is remitted here rather than to the creditor.",
    )
    payee_partner_id = fields.Many2one(
        "res.partner",
        "Payee",
        compute="_compute_payee_partner_id",
        store=True,
        help="Who the deducted money is actually paid to.",
    )
    partner_bank_id = fields.Many2one(
        "res.partner.bank",
        "Payee Bank Account",
        domain="[('partner_id', '=', payee_partner_id)]",
    )
    variable_symbol = fields.Char(
        compute="_compute_variable_symbol",
        store=True,
        readonly=False,
        help="Defaults to the case number. Stamped on the remittance entry.",
    )
    specific_symbol = fields.Char()
    constant_symbol = fields.Char()

    # --- amounts ----------------------------------------------------------
    total_amount = fields.Monetary(
        "Total Claim",
        tracking=True,
        help="Principal plus costs and interest as stated in the order. Leave "
        "at zero for an open-ended recurring maintenance obligation.",
    )
    monthly_amount = fields.Monetary(
        "Monthly Maintenance",
        tracking=True,
        help="Current monthly maintenance (běžné výživné). Used as the "
        "pro-rata weight when the second third cannot cover every "
        "maintenance claim, per § 280(2) OSŘ.",
    )
    arrears_amount = fields.Monetary(
        "Arrears",
        tracking=True,
        help="Maintenance already in default (dlužné výživné), collected on "
        "top of the current monthly amount.",
    )
    paid_amount = fields.Monetary(
        compute="_compute_paid_amount", store=True, tracking=True
    )
    remaining_amount = fields.Monetary(compute="_compute_paid_amount", store=True)
    is_open_ended = fields.Boolean(
        compute="_compute_is_open_ended",
        store=True,
        help="Recurring obligation with no total — never closes automatically.",
    )

    # --- lifecycle --------------------------------------------------------
    date_start = fields.Date(
        compute="_compute_date_start",
        store=True,
        readonly=False,
        help="First period the deduction applies to. Defaults to the day the "
        "order was served — under § 282(1) o. s. ř. the employer must begin "
        "deducting from the day the order is delivered to it. Editable, and a "
        "manual value survives until the delivery date itself changes.",
    )
    date_end = fields.Date(tracking=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("running", "Running"),
            ("suspended", "Suspended"),
            ("done", "Settled"),
            ("cancel", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )

    line_ids = fields.One2many("hr.wage.garnishment.line", "garnishment_id")
    line_count = fields.Integer(compute="_compute_line_count")
    note = fields.Html()
    document = fields.Binary("Order Document", attachment=True)
    document_name = fields.Char()

    # ------------------------------------------------------------------
    # computes / constraints
    # ------------------------------------------------------------------
    @api.depends("bailiff_partner_id", "creditor_partner_id")
    def _compute_payee_partner_id(self):
        for order in self:
            order.payee_partner_id = (
                order.bailiff_partner_id or order.creditor_partner_id
            )

    @api.depends("date_delivered")
    def _compute_date_start(self):
        for order in self:
            order.date_start = order.date_delivered

    @api.depends("case_number")
    def _compute_variable_symbol(self):
        """Digits of the case number, last 10 — a VS is numeric, case numbers
        are not. Stored and editable, so a manual override survives until the
        case number itself changes (the same convention as
        ``l10n_cssk_payment_symbols``)."""
        for order in self:
            digits = "".join(ch for ch in (order.case_number or "") if ch.isdigit())
            order.variable_symbol = digits[-10:] or False

    @api.depends(
        "line_ids.amount", "line_ids.state", "total_amount", "is_open_ended"
    )
    def _compute_paid_amount(self):
        for order in self:
            paid = sum(
                line.amount
                for line in order.line_ids
                if line.state in ("computed", "done")
            )
            order.paid_amount = paid
            order.remaining_amount = (
                0.0 if order.is_open_ended else max(0.0, order.total_amount - paid)
            )

    @api.depends("total_amount", "monthly_amount")
    def _compute_is_open_ended(self):
        for order in self:
            order.is_open_ended = not order.total_amount and bool(order.monthly_amount)

    @api.depends("line_ids")
    def _compute_line_count(self):
        for order in self:
            order.line_count = len(order.line_ids)

    @api.constrains("claim_class", "company_id")
    def _check_claim_class(self):
        rate_model = self.env["hr.wage.garnishment.rate"]
        for order in self:
            code = order.company_id.country_id.code
            if code not in ("CZ", "SK"):
                continue
            if order.claim_class not in rate_model._supported_classes(code):
                raise ValidationError(
                    _(
                        "Claim class %(cls)s does not exist under %(code)s law.",
                        cls=order.claim_class,
                        code=code,
                    )
                )

    @api.constrains("partner_bank_id", "payee_partner_id",
                    "bailiff_partner_id", "creditor_partner_id")
    def _check_partner_bank_belongs_to_the_payee(self):
        """The account the money goes to must be the payee's.

        ``partner_bank_id`` carries a domain, and a domain is a form widget:
        it does not run on import, on a server action, or on any write that
        did not pass through that form. The account is copied straight onto
        the remittance entry and is what a payment order pays into, so an
        account belonging to somebody else is a wage deduction paid to the
        wrong person — recoverable only by chasing it.

        Compared on the commercial partner so a payee contact whose bank
        account sits on the parent company is accepted.
        """
        for order in self:
            bank = order.partner_bank_id
            if not bank:
                continue
            payee = order.payee_partner_id
            if not payee:
                continue
            if bank.partner_id.commercial_partner_id != payee.commercial_partner_id:
                raise ValidationError(_(
                    "The payee bank account %(account)s belongs to "
                    "%(owner)s, not to the payee %(payee)s. The remittance is "
                    "paid into this account, so it must be the payee's.",
                    account=bank.acc_number,
                    owner=bank.partner_id.display_name,
                    payee=payee.display_name,
                ))

    @api.constrains("total_amount", "monthly_amount", "garnishment_type")
    def _check_has_amount(self):
        for order in self:
            if not order.total_amount and not order.monthly_amount:
                raise ValidationError(
                    _(
                        "Order %s needs either a total claim or a monthly "
                        "maintenance amount — otherwise there is nothing to "
                        "deduct.",
                        order.case_number,
                    )
                )

    # ------------------------------------------------------------------
    # state machine
    # ------------------------------------------------------------------
    def action_start(self):
        self.filtered(lambda o: o.state in ("draft", "suspended")).write(
            {"state": "running"}
        )

    def action_suspend(self):
        self.filtered(lambda o: o.state == "running").write({"state": "suspended"})

    def action_settle(self):
        self.write({"state": "done", "date_end": fields.Date.context_today(self)})

    def action_cancel(self):
        self.write({"state": "cancel"})

    def action_draft(self):
        self.filtered(lambda o: o.state in ("cancel", "suspended")).write(
            {"state": "draft"}
        )

    def action_view_lines(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Deductions"),
            "res_model": "hr.wage.garnishment.line",
            "view_mode": "list,form",
            "domain": [("garnishment_id", "=", self.id)],
            "context": {"default_garnishment_id": self.id},
        }

    # ------------------------------------------------------------------
    # allocation
    # ------------------------------------------------------------------
    def _due_this_period(self, date_to):
        """How much this order may absorb in the period ending *date_to*.

        A closed-ended claim is capped by what is still outstanding. A
        recurring maintenance obligation asks for the current month plus any
        arrears still on file.
        """
        self.ensure_one()
        if self.is_open_ended:
            return self.monthly_amount + max(
                0.0, self.arrears_amount - self._arrears_collected()
            )
        return self.remaining_amount

    def _arrears_collected(self):
        """Whatever has already been paid beyond the recurring monthly part."""
        self.ensure_one()
        months = len(self.line_ids.filtered(lambda line: line.state in ("computed", "done")))
        return max(0.0, self.paid_amount - months * self.monthly_amount)

    @api.model
    def _active_orders(self, employee, date_from, date_to, company=None):
        """Orders in force for *employee* over the period, ranked by pořadí.

        The multi-company record rule does NOT stand in for a company filter:
        ``company_ids`` in a rule resolves to the user's ALLOWED companies,
        not to ``env.company``, so a payroll officer who can see A and B was
        shown B's orders while computing an A payslip. The line's
        ``company_id`` is ``related=garnishment_id.company_id``, so the
        deduction then belonged to B and ``_remit_one`` booked the remittance
        in B's journal against an A payslip — money leaving the wrong
        company's books.

        ``company`` is resolved rather than merely honoured when passed: a
        scoping fix whose filter disappears when an argument is omitted is not
        a scoping fix, it is one every future caller has to remember. The
        fallback chain matches ``_allocate``'s own.
        """
        company = company or employee.company_id or self.env.company
        return self.search(
            [
                ("employee_id", "=", employee.id),
                ("state", "=", "running"),
                ("company_id", "=", company.id),
                "|", ("date_start", "=", False), ("date_start", "<=", date_to),
                "|", ("date_end", "=", False), ("date_end", ">=", date_from),
            ],
            order="date_delivered, sequence, id",
        )

    def _as_claim(self, date_to):
        self.ensure_one()
        return Claim(
            key=self.id,
            claim_class=self.claim_class,
            order_key=(self.date_delivered, self.sequence, self.id),
            due=self._due_this_period(date_to),
            current_maintenance=self.monthly_amount,
        )

    @api.model
    def _allocate(self, employee, net, date_from, date_to, company=None):
        """Run the statutory waterfall for one employee and one period.

        Returns ``(orders, result)`` where *result* is a
        :class:`~.garnishment_calc.Result`. Returns ``(empty, None)`` when the
        employee has no running orders, so callers can skip cheaply.
        """
        company = company or employee.company_id or self.env.company
        code = company.country_id.code
        if code not in ("CZ", "SK"):
            raise UserError(
                _(
                    "Wage garnishment is implemented for Czech and Slovak "
                    "companies only; %s is set to %s.",
                    company.display_name,
                    code or _("no country"),
                )
            )
        orders = self._active_orders(employee, date_from, date_to, company)
        if not orders:
            return orders, None
        rate = self.env["hr.wage.garnishment.rate"]._get_rate(code, date_to)
        rates = rate._rates_dict()
        claims = [order._as_claim(date_to) for order in orders]
        dependents = employee.l10n_cssk_garnishment_dependents
        if code == "CZ":
            result = compute_cz(net, rates, dependents, claims)
        else:
            result = compute_sk(
                net,
                rates,
                dependents,
                claims,
                is_pensioner=employee.l10n_cssk_garnishment_is_pensioner,
            )
        return orders, result

    # ------------------------------------------------------------------
    # entry points for salary rules
    # ------------------------------------------------------------------
    # Salary rules run under ``safe_eval``, which offers no ``hasattr`` and no
    # ``getattr``. They therefore probe for this feature with
    # ``'hr.wage.garnishment' in payslip.env`` and call in here — which means
    # a correct payslip amount needs only THIS module, not a bridge. The
    # bridges add the deduction ledger on top; without them the amount is
    # still right, it just is not recorded per order.
    @api.model
    def _payslip_amount(self, payslip, net):
        """Total to withhold from *net*, as a positive number."""
        payslip.ensure_one()
        orders, result = self._allocate(
            payslip.employee_id,
            net,
            payslip.date_from,
            payslip.date_to,
            payslip.company_id,
        )
        if "l10n_cssk_garnishment_net" in payslip._fields:
            # Remember what the payslip was computed on, so confirming it
            # reproduces exactly the figures the employee was shown.
            if payslip.l10n_cssk_garnishment_net != net:
                payslip.sudo().l10n_cssk_garnishment_net = net
        return result.total if result else 0.0

    @api.model
    def _payslip_has_orders(self, payslip):
        """Cheap guard for a salary rule's condition."""
        payslip.ensure_one()
        if payslip.company_id.country_id.code not in ("CZ", "SK"):
            return False
        return bool(
            self.search_count(
                [
                    ("employee_id", "=", payslip.employee_id.id),
                    ("state", "=", "running"),
                    # Same scoping as ``_active_orders``: the guard and the
                    # allocator must agree on which orders exist, or a salary
                    # rule fires for orders the allocator will not honour.
                    ("company_id", "=", payslip.company_id.id),
                ],
                limit=1,
            )
        )

    @api.model
    def _register_allocation(self, employee, result, orders, payslip_ref, date_from, date_to):
        """Materialise an allocation as garnishment lines (idempotently).

        Any previously computed line for the same payslip reference is
        replaced, so recomputing a payslip does not double-count.
        """
        line_model = self.env["hr.wage.garnishment.line"]
        existing = line_model.search(
            [("payslip_ref", "=", payslip_ref), ("state", "!=", "done")]
        )
        existing.unlink()
        if not result:
            return line_model
        vals_list = []
        for order in orders:
            amount = result.allocations.get(order.id, 0.0)
            if not amount:
                continue
            sources = result.breakdown.get(order.id, {})
            vals_list.append(
                {
                    "garnishment_id": order.id,
                    "employee_id": employee.id,
                    "payslip_ref": payslip_ref,
                    "date_from": date_from,
                    "date_to": date_to,
                    "amount": amount,
                    "amount_first_third": sources.get("first", 0.0),
                    "amount_second_third": sources.get("second", 0.0),
                    "amount_unlimited": sources.get("unlimited", 0.0),
                    "state": "computed",
                }
            )
        lines = line_model.create(vals_list)
        # Close anything that has now been paid in full.
        for order in orders:
            if (
                not order.is_open_ended
                and order.total_amount
                and order.remaining_amount <= 0
                and order.state == "running"
            ):
                order.action_settle()
                order.message_post(
                    body=_("Claim settled in full; no further deductions will be made.")
                )
        return lines
