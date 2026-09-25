# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The payslip half of the garnishment feature, kept engine-neutral.

Both payroll engines expose the same handful of payslip concepts —
``employee_id``, ``company_id``, ``date_from``/``date_to``, a
``compute_sheet`` and an ``action_payslip_done``/``_cancel`` lifecycle — so
all of the logic lives here as an ``AbstractModel``. The two bridge modules
do nothing but mix it into their engine's ``hr.payslip`` and hook the
lifecycle methods.

An ``AbstractModel`` is never instantiated on its own, so declaring it here
does not drag ``hr.payslip`` into the base module's dependencies.

Timing
------
Garnishment lines are **not** written while the payslip is being computed —
a draft payslip may be recomputed any number of times and each run would
otherwise shift the outstanding balances under its own feet. Instead the
salary rule stores the net wage it computed on, and the lines are
materialised once, idempotently, when the payslip is confirmed.
"""

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class CSSKGarnishmentPayslipMixin(models.AbstractModel):
    _name = "cssk.garnishment.payslip.mixin"
    _description = "Wage Garnishment Payslip Mixin"

    l10n_cssk_garnishment_net = fields.Float(
        "Garnishment Net Base",
        readonly=True,
        copy=False,
        help="Net wage the garnishment waterfall was computed on. Stored so "
        "confirming the payslip reproduces exactly what the payslip showed.",
    )
    # A plain Many2many, not a One2many: ``payslip_ref`` is a Char rather than
    # a foreign key (the base module must not bind to either engine's payslip
    # table), so there is no inverse field to hang a One2many on.
    l10n_cssk_garnishment_line_ids = fields.Many2many(
        "hr.wage.garnishment.line",
        compute="_compute_l10n_cssk_garnishment_line_ids",
        string="Garnishment Deductions",
    )

    @api.depends_context("uid")
    def _compute_l10n_cssk_garnishment_line_ids(self):
        line_model = self.env["hr.wage.garnishment.line"]
        for slip in self:
            slip.l10n_cssk_garnishment_line_ids = (
                line_model.search(
                    [("payslip_ref", "=", slip._cssk_garnishment_payslip_ref())]
                )
                if slip.id
                else line_model
            )

    def _cssk_garnishment_payslip_ref(self):
        self.ensure_one()
        return "%s,%s" % (self._name, self.id)

    # ------------------------------------------------------------------
    # called from the salary rule
    # ------------------------------------------------------------------
    def _cssk_garnishment_amount(self, net):
        """Total to withhold from *net* this period, as a positive number."""
        self.ensure_one()
        return self.env["hr.wage.garnishment"]._payslip_amount(self, net)

    def _cssk_garnishment_has_orders(self):
        """Cheap guard so the salary rule's condition can short-circuit."""
        self.ensure_one()
        return self.env["hr.wage.garnishment"]._payslip_has_orders(self)

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------
    def _cssk_garnishment_register(self):
        """Materialise the deduction ledger for confirmed payslips."""
        garnishment = self.env["hr.wage.garnishment"]
        for slip in self:
            if not slip.company_id.country_id.code in ("CZ", "SK"):
                continue
            orders, result = garnishment._allocate(
                slip.employee_id,
                slip.l10n_cssk_garnishment_net,
                slip.date_from,
                slip.date_to,
                slip.company_id,
            )
            if not orders:
                continue
            garnishment._register_allocation(
                slip.employee_id,
                result,
                orders,
                slip._cssk_garnishment_payslip_ref(),
                slip.date_from,
                slip.date_to,
            )

    def _cssk_garnishment_check_resettable(self):
        """Refuse to reset a payslip whose deduction has already been remitted.

        ``_cssk_garnishment_unregister`` deliberately keeps ``done`` lines —
        the money has gone to the bailiff and only a reversal undoes that. But
        ``_register_allocation`` filters on the SAME ``state != 'done'`` when
        it clears the old rows, so confirming the payslip again wrote a SECOND
        line for the same ``payslip_ref``: the ``done`` one and a fresh
        ``computed`` one, side by side.

        The employee is still debited once — the payslip only carries one
        deduction — so this is not money lost. What breaks is the ledger the
        bailiff is answered from: ``paid_amount`` inflated, ``remaining_amount``
        understated, and the Garnishments tab showing the deduction twice. On
        an order that is nearly settled that understates what is still owed,
        which is the direction that ends an exekúcia early.

        Blocking the transition is the honest fix: a remitted deduction is a
        payment to a third party, and a payroll correction after it needs a
        reversal, not a silent re-computation.
        """
        line_model = self.env["hr.wage.garnishment.line"].sudo()
        blocked = line_model.search([
            ("payslip_ref", "in", [s._cssk_garnishment_payslip_ref() for s in self]),
            ("state", "=", "done"),
        ])
        if not blocked:
            return
        # The search runs under ``sudo`` so the block cannot be dodged by not
        # holding the ACL, but the MESSAGE must not become a way to read case
        # numbers that way. Name the orders only to a reader entitled to them
        # — an exekúcia against a named employee is exactly the sort of thing
        # not to spill into an error string.
        try:
            orders = ", ".join(sorted(set(
                blocked.garnishment_id.sudo(False).mapped("display_name"))))
        except AccessError:
            orders = ""
        if orders:
            raise UserError(_(
                "This payslip carries a wage deduction that has already been "
                "remitted to the payee (%(orders)s), so it cannot be reset to "
                "draft — resetting it would leave the garnishment ledger "
                "counting the deduction twice while the employee was debited "
                "once. Reverse the remittance first.",
                orders=orders,
            ))
        raise UserError(_(
            "This payslip carries a wage deduction that has already been "
            "remitted to the payee, so it cannot be reset to draft — "
            "resetting it would leave the garnishment ledger counting the "
            "deduction twice while the employee was debited once. Reverse the "
            "remittance first."
        ))

    def _cssk_garnishment_unregister(self):
        """Drop the ledger rows of payslips being reset or cancelled.

        Rows already remitted to the bailiff are left alone — the money has
        gone out and only a reversal can undo that.
        """
        lines = self.env["hr.wage.garnishment.line"].search(
            [
                ("payslip_ref", "in", [s._cssk_garnishment_payslip_ref() for s in self]),
                ("state", "!=", "done"),
            ]
        )
        # Reopen any order that had been auto-settled by these deductions.
        orders = lines.garnishment_id.filtered(lambda o: o.state == "done")
        lines.unlink()
        for order in orders:
            if order.remaining_amount > 0:
                order.write({"state": "running", "date_end": False})
                order.message_post(
                    body=_(
                        "Reopened: a payslip carrying a deduction against this "
                        "order was cancelled or reset to draft."
                    )
                )

    @api.model
    def _cssk_garnishment_is_enabled(self, company):
        return company.country_id.code in ("CZ", "SK")
