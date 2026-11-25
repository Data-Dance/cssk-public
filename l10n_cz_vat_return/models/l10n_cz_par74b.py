# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""§ 74b odst. 3 a 4 ZDPH: the debtor's deduction on an overdue bill.

"Není-li pohledávka ze zdanitelného plnění zcela uspokojena do posledního dne
šestého kalendářního měsíce bezprostředně následujícího po kalendářním
měsíci, v němž se stala splatnou, je dlužník, který je plátcem, povinen
uplatněný odpočet daně snížit ve výši vypočtené z neposkytnuté úplaty, a to
za zdaňovací období, do kterého náleží tento poslední den." (odst. 3)

The correction is a document of its own, not a credit note from the
supplier: the debt stays. It is built as a vendor credit note whose total is
zero, because that is the shape the rest of the localization already reads:

* its taxed line carries the bill's own purchase tax, so the ordinary row of
  the DPHDP3 (ř. 40 / 41) goes down by the base and the tax, which is what
  lowers the deduction (ř. 63 does not read ř. 34);
* it is flagged ``l10n_cz_bad_debt = "P"``, which puts its tax on ř. 34 and
  its row into B.2 of the kontrolní hlášení with ``zdph_44``, whatever the
  amount;
* an untaxed line takes the base back and another books the tax as a cost,
  so nothing moves on the supplier's account.

Paying later gives the deduction back (odst. 4), "ve výši vypočtené z
poskytnuté úplaty dlužníkem": the mirror document, a vendor bill of zero.
"""

from datetime import date as date_cls

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero

#: Zákon č. 461/2024 Sb., čl. II bod 17: "Na nárok na odpočet daně, který
#: vznikl přede dnem nabytí účinnosti tohoto zákona, se § 74b … nepoužije."
#: The act took effect on 1. 1. 2025.
PAR74B_FROM = date_cls(2025, 1, 1)


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_cz_par74b_origin_id = fields.Many2one(
        "account.move", string="Opravovaný doklad (§ 74b)", copy=False,
        index="btree_not_null", check_company=True,
        help="The vendor bill whose deduction this document corrects under "
             "§ 74b odst. 3 or gives back under odst. 4.")
    l10n_cz_par74b_correction_ids = fields.One2many(
        "account.move", "l10n_cz_par74b_origin_id", string="Opravy § 74b")
    l10n_cz_par74b_is_reclaim = fields.Boolean(
        string="§ 74b odst. 4", copy=False,
        help="This document gives a corrected deduction back after payment.")
    l10n_cz_par74b_state = fields.Selection(
        [("none", "—"),
         ("draft", "Oprava odpočtu připravena"),
         ("corrected", "Odpočet snížen (§ 74b odst. 3)"),
         ("reclaimed", "Odpočet zčásti nebo zcela vrácen (§ 74b odst. 4)")],
        string="Stav § 74b", compute="_compute_l10n_cz_par74b_state",
        store=True, default="none")
    l10n_cz_par74b_deadline = fields.Date(
        string="Lhůta § 74b odst. 3",
        compute="_compute_l10n_cz_par74b_deadline",
        help="The last day of the sixth calendar month after the month in "
             "which the bill fell due.")

    @api.depends("l10n_cz_par74b_correction_ids.state",
                 "l10n_cz_par74b_correction_ids.l10n_cz_par74b_is_reclaim")
    def _compute_l10n_cz_par74b_state(self):
        for move in self:
            live = move.l10n_cz_par74b_correction_ids.filtered(
                lambda c: c.state != "cancel")
            posted = live.filtered(lambda c: c.state == "posted")
            if posted.filtered("l10n_cz_par74b_is_reclaim"):
                move.l10n_cz_par74b_state = "reclaimed"
            elif posted:
                move.l10n_cz_par74b_state = "corrected"
            elif live:
                move.l10n_cz_par74b_state = "draft"
            else:
                move.l10n_cz_par74b_state = "none"

    @api.depends("invoice_date_due", "move_type")
    def _compute_l10n_cz_par74b_deadline(self):
        for move in self:
            move.l10n_cz_par74b_deadline = (
                move._l10n_cz_par74b_deadline_of(move.invoice_date_due)
                if move.move_type == "in_invoice" else False)

    @api.model
    def _l10n_cz_par74b_deadline_of(self, due):
        """Last day of the sixth month after the month ``due`` falls in."""
        if not due:
            return False
        return due.replace(day=1) + relativedelta(months=7, days=-1)

    # ------------------------------------------------------------------
    # What was deducted, and how much of the bill is unpaid
    # ------------------------------------------------------------------
    def _l10n_cz_par74b_deducted(self):
        """``{tax: (base, vat)}`` of the deduction this bill claimed.

        Only a tax that left a net deduction on the bill. A reverse-charge
        tax books its input and its output line on the same bill and nets to
        nothing: no VAT is owed to the supplier there, so no part of the
        unpaid consideration is VAT and nothing is corrected.
        """
        self.ensure_one()
        result = {}
        tax_lines = self.line_ids.filtered(
            lambda l: l.tax_line_id
            and l.tax_line_id.type_tax_use == "purchase")
        currency = self.company_id.currency_id
        for tax in tax_lines.tax_line_id:
            lines = tax_lines.filtered(lambda l: l.tax_line_id == tax)
            net = sum(lines.mapped("balance"))
            reported = sum(lines.filtered("tax_tag_ids").mapped("balance"))
            if currency.compare_amounts(net, 0.0) <= 0 \
                    or currency.compare_amounts(reported, 0.0) <= 0:
                continue
            base = sum(self.line_ids.filtered(
                lambda l: tax in l.tax_ids).mapped("balance"))
            result[tax] = (base, reported)
        return result

    def _l10n_cz_par74b_payable_lines(self):
        self.ensure_one()
        return self.line_ids.filtered(
            lambda l: l.account_id.account_type == "liability_payable")

    def _l10n_cz_par74b_has_instalments(self):
        """Whether the bill falls due in parts. Each part is then a debt
        with its own six months, which one deadline per bill cannot state."""
        self.ensure_one()
        return len(set(self._l10n_cz_par74b_payable_lines().filtered(
            "date_maturity").mapped("date_maturity"))) > 1

    def _l10n_cz_par74b_settlements(self, on_date=None):
        """Reconciliations of the bill's payable, up to ``on_date``."""
        self.ensure_one()
        payable = self._l10n_cz_par74b_payable_lines()
        partials = payable.matched_debit_ids | payable.matched_credit_ids
        if on_date:
            partials = partials.filtered(lambda p: p.max_date <= on_date)
        return partials

    def _l10n_cz_par74b_unpaid_fraction(self, on_date=None):
        """Share of the bill still owed on ``on_date`` (today when empty).

        What was settled later than that day does not count: the duty of
        odst. 3 arose on the day the six months ran out, and a payment after
        it is the business of odst. 4. Measured in the currency of the bill,
        so that the share of a foreign bill does not move with the rate. A
        supplier's credit note set against the bill counts as settlement: it
        lowers the consideration, and its own tax lowers the deduction.
        """
        self.ensure_one()
        payable = self._l10n_cz_par74b_payable_lines()
        total = abs(sum(payable.mapped("amount_currency")))
        if self.currency_id.is_zero(total):
            return 0.0
        settled = 0.0
        for partial in self._l10n_cz_par74b_settlements(on_date):
            settled += (partial.credit_amount_currency
                        if partial.credit_move_id in payable
                        else partial.debit_amount_currency)
        unpaid = max(total - settled, 0.0)
        if self.currency_id.is_zero(unpaid):
            return 0.0
        return min(unpaid / total, 1.0)

    def _l10n_cz_par74b_vat(self, reclaim, states=("posted",)):
        """Σ tax of this bill's § 74b documents of one kind, positive."""
        self.ensure_one()
        moves = self.l10n_cz_par74b_correction_ids.filtered(
            lambda c: c.state in states
            and c.l10n_cz_par74b_is_reclaim == reclaim)
        return abs(sum(moves.line_ids.filtered("tax_line_id").mapped(
            "balance")))

    def _l10n_cz_par74b_posted_vat(self, reclaim):
        return self._l10n_cz_par74b_vat(reclaim)

    # ------------------------------------------------------------------
    # The documents
    # ------------------------------------------------------------------
    def _l10n_cz_par74b_make_move(self, on_date, account, share, reclaim=False):
        """The draft correction (or, with ``reclaim``, its reverse).

        ``share`` is the part of the bill's deduction the document moves.
        """
        self.ensure_one()
        currency = self.company_id.currency_id
        label = (_("§ 74b odst. 4: oprava odpočtu po úhradě, doklad %s")
                 if reclaim else
                 _("§ 74b odst. 3: snížení odpočtu, doklad %s")) % (
                     self.ref or self.name or "")
        lines = []
        for tax, (base, vat) in self._l10n_cz_par74b_deducted().items():
            amount = currency.round(
                (base + vat if tax.price_include else base) * share)
            if currency.is_zero(amount):
                continue
            lines.append({"name": label, "account_id": account.id,
                          "quantity": 1, "price_unit": amount,
                          "tax_ids": [(6, 0, tax.ids)]})
            lines.append({"name": label, "account_id": account.id,
                          "quantity": 1,
                          "price_unit": -currency.round(base * share),
                          "tax_ids": [(5, 0, 0)]})
        if not lines:
            raise UserError(_(
                "%s claimed no deduction that § 74b could correct.",
                self.display_name))
        move = self.env["account.move"].with_company(self.company_id).create({
            "move_type": "in_invoice" if reclaim else "in_refund",
            "partner_id": self.partner_id.id,
            "journal_id": self.journal_id.id,
            "currency_id": currency.id,
            # The supplier's number of the bill: what B.2 of the kontrolní
            # hlášení identifies the correction by.
            "ref": self.ref or self.name,
            "invoice_date": on_date,
            "date": on_date,
            "taxable_supply_date": on_date,
            "l10n_cz_bad_debt": "P",
            "l10n_cz_par74b_origin_id": self.id,
            "l10n_cz_par74b_is_reclaim": reclaim,
            "invoice_line_ids": [(0, 0, vals) for vals in lines],
        })
        # The tax as the engine computed it goes to the cost account, so the
        # document owes the supplier nothing.
        if not currency.is_zero(move.amount_tax):
            move.invoice_line_ids = [(0, 0, {
                "name": label, "account_id": account.id, "quantity": 1,
                "price_unit": -move.amount_tax, "tax_ids": [(5, 0, 0)]})]
        if not currency.is_zero(move.amount_total):
            raise UserError(_(
                "The § 74b document for %(bill)s does not come to zero "
                "(%(total)s). Check the taxes of the bill.",
                bill=self.display_name, total=move.amount_total))
        return move

    def _l10n_cz_par74b_cost_account(self):
        """The account the earlier correction booked the tax to."""
        self.ensure_one()
        correction = self.l10n_cz_par74b_correction_ids.filtered(
            lambda c: c.state == "posted"
            and not c.l10n_cz_par74b_is_reclaim)[:1]
        return correction.invoice_line_ids.filtered(
            lambda l: not l.tax_ids)[:1].account_id

    def action_l10n_cz_par74b_reclaim(self):
        """§ 74b odst. 4: the deduction comes back with the payment.

        Up to the tax of the payments made since the correction, counting
        what was already given back (odst. 6).
        """
        moves = self.env["account.move"]
        for bill in self:
            corrected = bill._l10n_cz_par74b_posted_vat(reclaim=False)
            if not corrected:
                raise UserError(_(
                    "%s has no posted correction under § 74b odst. 3.",
                    bill.display_name))
            deducted = sum(
                vat for _base, vat in bill._l10n_cz_par74b_deducted().values())
            still_owed = deducted * bill._l10n_cz_par74b_unpaid_fraction()
            # A draft waiting to be posted counts: two drafts for one
            # payment would give the deduction back twice.
            amount = (corrected - min(still_owed, corrected)
                      - bill._l10n_cz_par74b_vat(
                          reclaim=True, states=("draft", "posted")))
            currency = bill.company_id.currency_id
            if currency.compare_amounts(amount, 0.0) <= 0 or not deducted:
                raise UserError(_(
                    "%s has nothing to give back under § 74b odst. 4: it was "
                    "not paid any further since the correction, or the "
                    "deduction was already given back for what was paid "
                    "(a draft counts).",
                    bill.display_name))
            today = fields.Date.context_today(bill)
            settlements = bill._l10n_cz_par74b_settlements()
            last_paid = max(settlements.mapped("max_date"), default=today)
            limit = date_cls(last_paid.year + 2, 12, 31)
            if today > limit:
                raise UserError(_(
                    "%(bill)s was last paid on %(paid)s; the deduction could "
                    "be given back until %(limit)s (§ 74b odst. 9: the end "
                    "of the second calendar year after the period of the "
                    "payment).",
                    bill=bill.display_name, paid=last_paid, limit=limit))
            moves |= bill._l10n_cz_par74b_make_move(
                fields.Date.context_today(bill),
                bill._l10n_cz_par74b_cost_account(),
                amount / deducted, reclaim=True)
        return moves._l10n_cz_par74b_action()

    def _l10n_cz_par74b_action(self):
        action = {
            "type": "ir.actions.act_window",
            "name": _("Opravy odpočtu (§ 74b)"),
            "res_model": "account.move",
            "context": {"create": False},
        }
        if len(self) == 1:
            action.update(view_mode="form", res_id=self.id)
        else:
            action.update(view_mode="list,form",
                          domain=[("id", "in", self.ids)])
        return action


class L10nCzPar74bWizard(models.TransientModel):
    _name = "l10n.cz.par74b.wizard"
    _description = "Oprava odpočtu daně u pohledávky po splatnosti (§ 74b)"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company)
    date = fields.Date(
        string="Ke dni", required=True, default=fields.Date.context_today,
        help="Bills whose six months ran out by this day are offered.")
    period_type = fields.Selection(
        [("month", "Měsíc"), ("quarter", "Čtvrtletí")],
        string="Zdaňovací období", required=True,
        default=lambda self: self._default_period_type(),
        help="A quarterly payer owes no correction for a bill paid in full "
             "by the end of the quarter in which the six months ran out "
             "(§ 74b odst. 3, second sentence).")
    book_on = fields.Selection(
        [("deadline", "Poslední den lhůty (§ 74b odst. 3)"),
         ("date", "Den uvedený výše")],
        string="Datum opravy", required=True, default="deadline",
        help="The law puts the correction in the tax period the last day of "
             "the six months belongs to. Use the other choice only where "
             "that period is closed and you decide to report the correction "
             "now instead of in a dodatečné přiznání.")
    correction_account_id = fields.Many2one(
        "account.account", string="Účet nákladu", required=True,
        domain="[('company_ids', 'in', company_id)]",
        default=lambda self: self._default_correction_account(),
        help="Where the tax that is no longer deductible is booked, for "
             "example 538.")
    bill_ids = fields.Many2many(
        "account.move", compute="_compute_bills", string="Faktury")
    bill_count = fields.Integer(
        compute="_compute_bills", string="Počet faktur")
    instalment_bill_ids = fields.Many2many(
        "account.move", compute="_compute_bills",
        string="Faktury se splátkami",
        help="Overdue bills payable in instalments. Each instalment is a "
             "debt with its own six months (§ 74b odst. 3), so these are "
             "left out; correct them by hand.")

    @api.model
    def _default_period_type(self):
        last = self.env["cssk.vat.return"].search([
            ("company_id", "=", self.env.company.id),
            ("country_id.code", "=", "CZ"),
        ], order="date_to desc", limit=1)
        return last.period_type if last.period_type in (
            "month", "quarter") else "month"

    @api.model
    def _default_correction_account(self):
        return self.env["account.account"].with_company(
            self.env.company).search([
                ("company_ids", "in", self.env.company.id),
                ("code", "=like", "538%"),
            ], order="code", limit=1)

    @api.depends("company_id", "date", "period_type")
    def _compute_bills(self):
        for wiz in self:
            found = wiz._qualifying_bills(with_instalments=True)
            bills = found.filtered(
                lambda b: not b._l10n_cz_par74b_has_instalments())
            wiz.bill_ids = bills
            wiz.bill_count = len(bills)
            wiz.instalment_bill_ids = found - bills

    def _decision_day(self, deadline):
        """The day the bill must be paid by to escape the correction."""
        self.ensure_one()
        if self.period_type != "quarter":
            return deadline
        quarter_start = deadline.replace(
            month=3 * ((deadline.month - 1) // 3) + 1, day=1)
        return quarter_start + relativedelta(months=3, days=-1)

    def _qualifying_bills(self, with_instalments=False):
        self.ensure_one()
        Move = self.env["account.move"]
        if not self.date or not self.company_id:
            return Move
        if self.company_id.account_fiscal_country_id.code != "CZ":
            return Move
        candidates = Move.search([
            ("company_id", "=", self.company_id.id),
            ("move_type", "=", "in_invoice"),
            ("state", "=", "posted"),
            ("l10n_cz_par74b_state", "=", "none"),
            ("invoice_date_due", "!=", False),
            # no bill can be six calendar months overdue sooner than this
            ("invoice_date_due", "<=", self.date - relativedelta(months=6)),
        ], order="invoice_date_due, id")

        def qualifies(bill):
            arose = bill.taxable_supply_date or bill.invoice_date or bill.date
            if arose < PAR74B_FROM:
                return False
            decision = self._decision_day(bill.l10n_cz_par74b_deadline)
            if decision > self.date:
                return False
            return bool(bill._l10n_cz_par74b_unpaid_fraction(decision)
                        and bill._l10n_cz_par74b_deducted())
        found = candidates.filtered(qualifies)
        if with_instalments:
            return found
        return found.filtered(
            lambda b: not b._l10n_cz_par74b_has_instalments())

    def _check_period_open(self, bills):
        """Odoo moves a document dated in a locked period past the lock
        instead of refusing it; the correction would then sit in a period
        the law does not put it in, without anybody having decided so."""
        self.ensure_one()
        locked = bills.filtered(
            lambda b: self.company_id._get_violated_lock_dates(
                b.l10n_cz_par74b_deadline, True, b.journal_id))
        if locked:
            raise UserError(_(
                "The correction belongs to a closed period for: %(bills)s. "
                "Reopen the period and file a dodatečné přiznání, or choose "
                "to date the corrections on the day entered above.",
                bills=", ".join("%s (%s)" % (
                    bill.name, bill.l10n_cz_par74b_deadline)
                    for bill in locked[:20])))

    def action_generate(self):
        self.ensure_one()
        bills = self._qualifying_bills()
        if not bills:
            raise UserError(_(
                "No bill meets the conditions of § 74b odst. 3 on %s.",
                self.date))
        if self.book_on == "deadline":
            self._check_period_open(bills)
        moves = self.env["account.move"]
        for bill in bills:
            deadline = bill.l10n_cz_par74b_deadline
            share = bill._l10n_cz_par74b_unpaid_fraction(
                self._decision_day(deadline))
            moves |= bill._l10n_cz_par74b_make_move(
                deadline if self.book_on == "deadline" else self.date,
                self.correction_account_id, share)
        return moves._l10n_cz_par74b_action()
