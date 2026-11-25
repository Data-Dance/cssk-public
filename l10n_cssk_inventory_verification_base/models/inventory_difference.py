# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Booking of inventarizačné rozdiely / inventarizační rozdíly.

Three abstract models. A country module inherits each of them into a concrete
model and supplies what the statute and the chart decide:

==========================================  ===================================
``l10n_cssk.inventory.difference.mixin``    the exercise (inventarizácia)
``l10n_cssk.inventory.sheet.mixin``         the count sheet (inventúrny súpis)
``l10n_cssk.inventory.difference.line``     one settlement line of a difference
==========================================  ===================================

The concrete line model declares ``inventory_id`` and ``sheet_id``; the
concrete sheet and exercise declare ``difference_line_ids`` pointing at it.
Everything below reaches the records through those three names only.
"""

from collections import defaultdict

from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

#: Kinds whose amount lowers the actual state below the books (the asset
#: account is credited) and kinds that raise it (the asset account is
#: debited). A claim against the liable person explains no part of the
#: difference: it is a second entry that follows from a shortage.
_SIGN = {"shortage": -1, "natural_loss": -1, "surplus": 1, "claim": 0}

#: Fields of a settlement line that the journal entry was built from.
_BOOKED_FIELDS = frozenset({
    "sheet_id", "inventory_id", "kind", "amount", "account_id",
    "counterpart_account_id", "partner_id",
})


def _has(*names):
    """``@api.depends`` on fields only a concrete model declares.

    The registry sets up abstract models too, and a dependency on a field the
    mixin does not have is an error there.
    """
    def depends(model):
        roots = {name.split(".")[0] for name in names}
        return names if roots <= set(model._fields) else ()
    return depends


class L10nCsskInventoryDifferenceLine(models.AbstractModel):
    _name = "l10n_cssk.inventory.difference.line"
    _description = "Settlement of an inventory difference (abstract)"
    _order = "sheet_id, sequence, id"

    sequence = fields.Integer(default=10)
    company_id = fields.Many2one("res.company")
    currency_id = fields.Many2one("res.currency")
    kind = fields.Selection(
        [
            ("shortage", "Shortage"),
            ("natural_loss", "Loss within the norm"),
            ("surplus", "Surplus"),
            ("claim", "Claim against the liable person"),
        ],
        required=True,
        default="shortage",
        help="Shortage and loss within the norm lower the actual state below "
             "the books; a surplus raises it. The three together must explain "
             "the whole difference of the count sheet. A claim explains none "
             "of it: it books what the liable person is asked to pay.",
    )
    name = fields.Char(
        string="Label",
        compute="_compute_name",
        store=True,
        readonly=False,
        precompute=True,
    )
    amount = fields.Monetary(required=True)
    account_id = fields.Many2one(
        "account.account",
        string="Account",
        compute="_compute_account_id",
        store=True,
        readonly=False,
        precompute=True,
        domain="[('company_ids', 'in', company_id)]",
        help="The account the difference sits on: the asset or liability "
             "counted on the sheet, or, for a claim, the receivable from the "
             "liable person.",
    )
    counterpart_account_id = fields.Many2one(
        "account.account",
        string="Counterpart account",
        compute="_compute_counterpart_account_id",
        store=True,
        readonly=False,
        precompute=True,
        domain="[('company_ids', 'in', company_id)]",
        help="The expense or income account the difference is booked "
             "against. Proposed from the kind and the account; change it "
             "where your chart or your case differs.",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Written on both items of the entry: the liable person of a "
             "claim or of a cash shortage, or the partner of a receivable or "
             "payable.",
    )
    move_id = fields.Many2one(
        "account.move",
        string="Journal entry",
        readonly=True,
        copy=False,
        ondelete="set null",
        index="btree_not_null",
    )
    move_state = fields.Selection(related="move_id.state", string="Entry status")
    warning = fields.Char(compute="_compute_warning")

    # ------------------------------------------------------------------
    # What the country module decides
    # ------------------------------------------------------------------
    def _cssk_counterpart_code(self, kind, account):
        """Code prefix of the counterpart for ``kind`` on ``account``.

        ``account`` comes in the company of the inventory verification, so
        its ``code`` can be read as it is.

        Returns a falsy value where the chart gives no single answer; the
        field then stays empty and the entry is refused until someone picks.
        """
        return False

    def _cssk_claim_account_code(self):
        """Code prefix of the receivable from the liable person."""
        return False

    # ------------------------------------------------------------------
    def _cssk_company(self):
        self.ensure_one()
        return self.company_id or self.sheet_id.company_id

    def _cssk_code(self, account):
        """Code of ``account`` in the company of the inventory verification.

        Account codes are company-dependent: read under the company the user
        happens to be working in, an account of another company has none,
        and every proposal would silently come out empty.
        """
        self.ensure_one()
        company = self._cssk_company()
        if not (account and company):
            return ""
        return account.with_company(company).code or ""

    def _cssk_account_by_code(self, prefix):
        self.ensure_one()
        company = self._cssk_company()
        if not (prefix and company):
            return self.env["account.account"]
        accounts = self.env["account.account"].with_company(company).search([
            ("company_ids", "in", company.id),
            ("code", "=like", prefix + "%"),
        ])
        return accounts.sorted(lambda a: a.code or "")[:1]

    @api.depends(_has("kind", "sheet_id"))
    def _compute_name(self):
        for line in self:
            if line.name:
                continue
            labels = dict(line._fields["kind"]._description_selection(line.env))
            sheet = line.sheet_id.name if "sheet_id" in line._fields else ""
            line.name = " – ".join(
                part for part in (labels.get(line.kind), sheet) if part)

    @api.depends(_has("kind", "sheet_id", "sheet_id.account_id"))
    def _compute_account_id(self):
        for line in self:
            if line._cssk_is_booked():
                # a recomputation is not a write and would pass the guard
                continue
            if line.kind == "claim":
                line.account_id = line._cssk_account_by_code(
                    line._cssk_claim_account_code())
            elif "sheet_id" in line._fields:
                line.account_id = line.sheet_id.account_id
            else:
                line.account_id = False

    @api.depends("kind", "account_id")
    def _compute_counterpart_account_id(self):
        for line in self:
            if line._cssk_is_booked():
                continue
            company = line._cssk_company()
            account = line.account_id
            if company:
                account = account.with_company(company)
            line.counterpart_account_id = line._cssk_account_by_code(
                line._cssk_counterpart_code(line.kind, account))

    @api.depends("kind", "account_id", "counterpart_account_id")
    def _compute_warning(self):
        stock_by_company = {}
        for line in self:
            messages = []
            accounts = line.account_id | line.counterpart_account_id
            if line.kind != "claim" and line._cssk_code(line.account_id)[:1] == "0":
                messages.append(line.env._(
                    "Fixed asset: retire or register it in the asset "
                    "register as well, or the register and the ledger part."
                ))
            company = line.company_id
            if company not in stock_by_company:
                stock_by_company[company] = line._cssk_stock_valuation_accounts(
                    company)
            if accounts & stock_by_company[company]:
                messages.append(line.env._(
                    "Odoo Inventory values stock on this account: adjust the "
                    "quantity there instead, or the difference is booked "
                    "twice."
                ))
            line.warning = " ".join(messages) or False

    @api.model
    def _cssk_stock_valuation_accounts(self, company):
        """Accounts Odoo Inventory keeps its valuation on, when installed."""
        accounts = self.env["account.account"]
        if not company:
            return accounts
        if "account_stock_valuation_id" in company._fields:
            accounts |= company.sudo().account_stock_valuation_id
        Category = self.env.get("product.category")
        field = "property_stock_valuation_account_id"
        if Category is not None and field in Category._fields:
            categories = Category.sudo().with_company(company).search(
                [(field, "!=", False)])
            accounts |= categories.mapped(field)
        return accounts

    @api.constrains("amount")
    def _check_amount(self):
        for line in self:
            if line.currency_id.compare_amounts(line.amount, 0.0) <= 0:
                # the kind carries the direction, never the sign
                raise ValidationError(line.env._(
                    "%s: the amount of a difference must be positive; the "
                    "kind says whether it is a shortage or a surplus.",
                    line.name or line.display_name,
                ))

    def _cssk_check_sheet(self, parent_field):
        """Constraint body for the concrete model, which knows the name of
        the sheet's link to its exercise."""
        for line in self:
            sheet = line.sheet_id
            if sheet[parent_field] != line.inventory_id:
                raise ValidationError(line.env._(
                    "The count sheet %s belongs to another inventory "
                    "verification.", sheet.display_name))
            if sheet.difference_skip:
                raise ValidationError(line.env._(
                    "%s: the difference is marked as not booked here, so it "
                    "takes no settlement lines.", sheet.display_name))

    def _cssk_is_booked(self):
        """True while a live (draft or posted) entry was built from the line.

        An entry cancelled in Accounting, or reversed there by hand, is no
        longer one: the difference is unbooked again and can be booked anew.
        """
        self.ensure_one()
        move = self.move_id
        return bool(move) and move.state != "cancel" and not any(
            reversal.state == "posted" for reversal in move.reversal_move_ids)

    def write(self, vals):
        if _BOOKED_FIELDS & set(vals) and any(
                line._cssk_is_booked() for line in self):
            raise UserError(self.env._(
                "A journal entry was already created from this difference. "
                "Cancel the booking of the differences first."
            ))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_booked(self):
        if any(line._cssk_is_booked() for line in self):
            raise UserError(self.env._(
                "A journal entry was already created from this difference. "
                "Cancel the booking of the differences first."
            ))

    def _cssk_signed_amount(self):
        self.ensure_one()
        return _SIGN[self.kind] * self.amount

    def _cssk_move_line_vals(self):
        """The two journal items of this settlement line.

        A shortage and a loss within the norm credit the Account; a surplus
        and a claim debit it. No ``amount_currency``: these are entries in
        the company currency, and an explicit zero there would zero the
        line.
        """
        self.ensure_one()
        if _SIGN[self.kind] < 0:
            debit, credit = self.counterpart_account_id, self.account_id
        else:
            debit, credit = self.account_id, self.counterpart_account_id
        label = "%s: %s" % (self.inventory_id.name, self.name)
        vals = []
        for account, side in ((debit, "debit"), (credit, "credit")):
            vals.append({
                "name": label,
                "account_id": account.id,
                side: self.amount,
                "partner_id": self.partner_id.id,
            })
        return vals


class L10nCsskInventorySheetMixin(models.AbstractModel):
    _name = "l10n_cssk.inventory.sheet.mixin"
    _description = "Count sheet whose difference is settled (abstract)"

    currency_id = fields.Many2one("res.currency")
    difference_skip = fields.Boolean(
        string="Difference not booked here",
        help="The difference of this sheet is settled elsewhere — in the "
             "asset register, by an adjustment in Odoo Inventory, by a "
             "document of its own — or needs no entry. State the reason; it "
             "is printed in the closing record.",
    )
    difference_skip_reason = fields.Char(string="Reason")
    difference_settled = fields.Monetary(
        string="Settled", compute="_compute_difference_residual", store=True)
    difference_residual = fields.Monetary(
        string="Still to settle",
        compute="_compute_difference_residual",
        store=True,
        help="The part of the difference no settlement line explains yet.",
    )

    def _cssk_difference_date(self):
        """The day the difference of this sheet is booked on.

        Both acts send the differences to the period being verified, so this
        is the day the state was verified as at.
        """
        self.ensure_one()
        return self.date_as_of

    @api.depends(_has(
        "difference", "difference_skip", "difference_line_ids.amount",
        "difference_line_ids.kind"))
    def _compute_difference_residual(self):
        for sheet in self:
            if "difference_line_ids" not in sheet._fields:
                sheet.difference_settled = sheet.difference_residual = 0.0
                continue
            settled = sum(
                line._cssk_signed_amount() for line in sheet.difference_line_ids)
            sheet.difference_settled = settled
            sheet.difference_residual = (
                0.0 if sheet.difference_skip else sheet.difference - settled)

    @api.constrains("difference_skip", "difference_skip_reason")
    def _check_difference_skip(self):
        for sheet in self:
            if sheet.difference_skip and not (
                    sheet.difference_skip_reason or "").strip():
                raise ValidationError(sheet.env._(
                    "%s: say why the difference is not booked here.",
                    sheet.display_name,
                ))
            if sheet.difference_skip and sheet.difference_line_ids:
                raise ValidationError(sheet.env._(
                    "%s: the difference is marked as not booked here, yet it "
                    "has settlement lines. Remove one or the other.",
                    sheet.display_name,
                ))

    @api.ondelete(at_uninstall=False)
    def _unlink_except_booked(self):
        # the lines go by database cascade, which runs no Python
        self.difference_line_ids._unlink_except_booked()


class L10nCsskInventoryDifferenceMixin(models.AbstractModel):
    _name = "l10n_cssk.inventory.difference.mixin"
    _description = "Inventory verification whose differences are booked (abstract)"

    #: Name of the one2many holding the count sheets on the concrete model.
    _cssk_sheets_field = None

    company_id = fields.Many2one("res.company")
    currency_id = fields.Many2one("res.currency")
    difference_journal_id = fields.Many2one(
        "account.journal",
        string="Journal for differences",
        compute="_compute_difference_journal_id",
        store=True,
        readonly=False,
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
    )
    difference_move_ids = fields.Many2many(
        "account.move",
        string="Journal entries of differences",
        copy=False,
        readonly=True,
        help="Every entry created from the differences, including the ones "
             "taken back since and their reversals.",
    )
    difference_move_count = fields.Integer(compute="_compute_difference_move_count")
    difference_state = fields.Selection(
        [
            ("none", "No differences"),
            ("to_settle", "To settle"),
            ("ready", "Ready to book"),
            ("draft", "Entry in draft"),
            ("posted", "Posted"),
        ],
        string="Differences",
        compute="_compute_difference_state",
    )
    difference_stale = fields.Boolean(compute="_compute_difference_state")
    difference_misdated = fields.Boolean(compute="_compute_difference_state")

    def _cssk_sheets(self):
        return self[self._cssk_sheets_field]

    @api.depends("company_id")
    def _compute_difference_journal_id(self):
        for inv in self:
            if inv.difference_journal_id.company_id == inv.company_id:
                continue
            inv.difference_journal_id = self.env["account.journal"].search([
                *self.env["account.journal"]._check_company_domain(inv.company_id),
                ("type", "=", "general"),
            ], limit=1)

    @api.depends("difference_move_ids")
    def _compute_difference_move_count(self):
        for inv in self:
            inv.difference_move_count = len(inv.difference_move_ids)

    @api.depends(lambda self: (
        "difference_line_ids.move_id.state",
        "difference_line_ids.move_id.date",
        "difference_line_ids.move_id.reversal_move_ids.state",
        self._cssk_sheets_field + ".difference_residual",
    ) if self._cssk_sheets_field else ())
    def _compute_difference_state(self):
        for inv in self:
            sheets = inv._cssk_sheets()
            currency = inv.currency_id
            open_sheets = sheets.filtered(
                lambda s: not currency.is_zero(s.difference_residual))
            booked = inv.difference_line_ids.filtered(
                lambda line: line._cssk_is_booked())
            moves = booked.move_id
            inv.difference_stale = bool(moves and open_sheets)
            # Someone changed the date in Accounting, or Odoo moved it past
            # a lock date on posting.
            inv.difference_misdated = any(
                line.move_id.date != line.sheet_id._cssk_difference_date()
                for line in booked
            )
            if moves:
                inv.difference_state = (
                    "posted" if all(m.state == "posted" for m in moves)
                    else "draft")
            elif open_sheets:
                inv.difference_state = "to_settle"
            elif inv.difference_line_ids:
                inv.difference_state = "ready"
            else:
                inv.difference_state = "none"

    # ------------------------------------------------------------------
    # Proposing
    # ------------------------------------------------------------------
    def action_propose_differences(self):
        """One settlement line per sheet for whatever is not explained yet.

        The sign decides between shortage and surplus; splitting a shortage
        into the part within the norm, or adding the claim against the
        liable person, is a decision and stays with the user.
        """
        for inv in self:
            Line = inv.difference_line_ids.browse()
            vals_list = []
            for sheet in inv._cssk_sheets():
                residual = sheet.difference_residual
                if sheet.difference_skip or inv.currency_id.is_zero(residual):
                    continue
                vals_list.append({
                    "inventory_id": inv.id,
                    "sheet_id": sheet.id,
                    "kind": "surplus" if residual > 0 else "shortage",
                    "amount": abs(residual),
                })
            Line.create(vals_list)
        return True

    # ------------------------------------------------------------------
    # Booking
    # ------------------------------------------------------------------
    def _cssk_check_differences_bookable(self):
        self.ensure_one()
        _ = self.env._
        if self.state not in ("in_progress", "done"):
            raise UserError(_(
                "%s: differences are booked once the inventory verification "
                "has started.", self.display_name))
        open_sheets = self._cssk_sheets().filtered(
            lambda s: not self.currency_id.is_zero(s.difference_residual))
        if open_sheets:
            raise UserError(_(
                "%(name)s: these count sheets have a difference that is "
                "neither settled in full nor marked as not booked here:\n"
                "%(sheets)s",
                name=self.display_name,
                sheets="\n".join(
                    "%s (%s)" % (
                        sheet.name,
                        self.currency_id.format(sheet.difference_residual),
                    )
                    for sheet in open_sheets
                ),
            ))
        lines = self.difference_line_ids.filtered(
            lambda line: not line._cssk_is_booked())
        if not lines:
            raise UserError(_(
                "%s: there is no difference left to book.", self.display_name))
        incomplete = lines.filtered(
            lambda line: not (line.account_id and line.counterpart_account_id))
        if incomplete:
            raise UserError(_(
                "%(name)s: choose both accounts on:\n%(lines)s",
                name=self.display_name,
                lines="\n".join(incomplete.mapped("name")),
            ))
        same = lines.filtered(
            lambda line: line.account_id == line.counterpart_account_id)
        if same:
            raise UserError(_(
                "%(name)s: the account and its counterpart are the same on:\n"
                "%(lines)s",
                name=self.display_name,
                lines="\n".join(same.mapped("name")),
            ))
        if not self.difference_journal_id:
            raise UserError(_(
                "%s: choose the journal the differences are booked in.",
                self.display_name))
        return lines

    def _cssk_check_period_open(self, date, journal=None):
        """Refuse a day inside a locked period.

        Odoo does not refuse it by itself: on posting it silently moves an
        entry dated in a locked period to the first open day, which for an
        inventory difference is the next accounting period — the one place
        the acts say it must not go.
        """
        self.ensure_one()
        violated = self.company_id._get_violated_lock_dates(
            date, False, journal or self.difference_journal_id)
        if violated:
            raise UserError(self.env._(
                "%(name)s: the differences belong to %(date)s, which lies in "
                "a locked period (%(locks)s). Unlock the period first: "
                "booked later, they would fall into another accounting "
                "period.",
                name=self.display_name,
                date=fields.Date.to_string(date),
                locks=self.env["res.company"]._format_lock_dates(violated),
            ))

    def _cssk_create_difference_entries(self):
        """Create the draft entries; one per day the sheets were verified at."""
        self.ensure_one()
        lines = self._cssk_check_differences_bookable()
        by_date = defaultdict(lambda: self.difference_line_ids.browse())
        for line in lines:
            date = line.sheet_id._cssk_difference_date()
            if not date:
                raise UserError(self.env._(
                    "%s: the day the state was verified as at is missing.",
                    line.sheet_id.display_name))
            by_date[date] |= line
        for date in by_date:
            self._cssk_check_period_open(date)
        moves = self.env["account.move"]
        for date, group in sorted(by_date.items()):
            move = self.env["account.move"].create({
                "move_type": "entry",
                "company_id": self.company_id.id,
                "journal_id": self.difference_journal_id.id,
                "date": date,
                "ref": self.name,
                "l10n_cssk_inventory_difference": True,
                "line_ids": [
                    fields.Command.create(vals)
                    for line in group
                    for vals in line._cssk_move_line_vals()
                ],
            })
            group.move_id = move
            move.message_post(body=self.env._(
                "Created from the differences of %s.",
                self._get_html_link(),
            ))
            moves |= move
        self.difference_move_ids |= moves
        self.message_post(body=self.env._(
            "Differences booked in draft: %s",
            Markup(", ").join(
                move._get_html_link(title=str(move.date)) for move in moves),
        ))
        return moves

    def action_create_difference_entries(self):
        for inv in self:
            inv._cssk_create_difference_entries()
        return self.action_view_difference_moves()

    def _cssk_cancel_difference_entries(self):
        """Take back the entries the differences were booked with.

        An entry that never left draft is deleted; a posted one is reversed
        on its own date, because the reversal belongs to the period verified
        just as the entry did. A lock date on that period therefore refuses
        the whole operation — rightly: the books of a closed period cannot
        quietly lose an entry.
        """
        for inv in self:
            moves = inv.difference_line_ids.filtered(
                lambda line: line._cssk_is_booked()).move_id
            # also the links to entries cancelled or reversed in Accounting
            inv.difference_line_ids.move_id = False
            if not moves:
                continue
            posted = moves.filtered(lambda m: m.state == "posted")
            draft = moves.filtered(lambda m: m.state == "draft")
            never_posted = draft.filtered(lambda m: not m.posted_before)
            names = ", ".join(m.name or "/" for m in posted)
            for move in posted:
                inv._cssk_check_period_open(move.date, move.journal_id)
            if posted:
                reversals = posted._reverse_moves(
                    [
                        {
                            "date": move.date,
                            "ref": inv.env._(
                                "Reversal of %(entry)s (%(inventory)s reopened)",
                                entry=move.name, inventory=inv.name),
                        }
                        for move in posted
                    ],
                    cancel=True,
                )
                inv.difference_move_ids |= reversals
                inv.message_post(body=inv.env._(
                    "Booking of differences reversed: %s", names))
            (draft - never_posted).button_cancel()
            never_posted.unlink()

    def action_cancel_difference_entries(self):
        self._cssk_cancel_difference_entries()
        return True

    def action_view_difference_moves(self):
        self.ensure_one()
        action = {
            "type": "ir.actions.act_window",
            "name": self.env._("Journal entries of differences"),
            "res_model": "account.move",
            "domain": [("id", "in", self.difference_move_ids.ids)],
            "context": {"default_move_type": "entry", "create": False},
        }
        if len(self.difference_move_ids) == 1:
            action.update(view_mode="form", res_id=self.difference_move_ids.id)
        else:
            action["view_mode"] = "list,form"
        return action

    @api.ondelete(at_uninstall=False)
    def _unlink_except_booked(self):
        # the lines go by database cascade, which runs no Python
        self.difference_line_ids._unlink_except_booked()


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_cssk_inventory_difference = fields.Boolean(
        string="Inventory difference",
        copy=False,
        readonly=True,
        help="Created from the differences of an inventory verification; it "
             "must stay in the accounting period that was verified.",
    )

    def _post(self, soft=True):
        # Odoo moves an entry dated in a locked period to the first open day
        # instead of refusing it. For an inventory difference that day lies
        # in the next accounting period, where SK § 30 ods. 7 and CZ § 30
        # odst. 11 say it must not be booked — so refuse.
        for move in self.filtered("l10n_cssk_inventory_difference"):
            violated = move._get_violated_lock_dates(move.date, False)
            if violated:
                raise UserError(self.env._(
                    "%(entry)s books inventory differences of %(date)s, which "
                    "lies in a locked period (%(locks)s). Posted now it would "
                    "be moved into another accounting period. Unlock the "
                    "period first.",
                    entry=move.ref or move.display_name,
                    date=fields.Date.to_string(move.date),
                    locks=self.env["res.company"]._format_lock_dates(violated),
                ))
        return super()._post(soft=soft)
