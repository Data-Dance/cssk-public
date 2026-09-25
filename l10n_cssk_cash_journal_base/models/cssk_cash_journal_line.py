# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import SQL

_logger = logging.getLogger(__name__)

#: Document lines whose amount is part of what was bought or sold. ``cogs``
#: (anglo-saxon cost of goods sold) and ``payment_term`` are excluded on
#: purpose: the first is a valuation entry the trader never paid for
#: separately, the second is the receivable/payable leg we are arriving from.
BASE_DISPLAY_TYPES = ("product", "rounding")

#: Account types that hold money itself — a bank account or a till.
#:
#: **Every intermediate leg is invisible to this test**, which is the single
#: most expensive thing to get wrong here. Measured on a freshly installed 19.0
#: company: the outstanding receipts account, the bank suspense account and the
#: inter-bank transfer account are all ``asset_current``. They are collected
#: from configuration instead (``_cssk_transit_accounts``), and followed
#: through, they are exactly the *priebežné položky* of the statutory denník
#: (opatrenie MF/27076/2007-74, § 4): money that left one pocket and has not yet
#: arrived in the other.
LIQUIDITY_TYPES = ("asset_cash", "liability_credit_card")

#: How far a reconciliation chain is followed: bank line → suspense →
#: outstanding → receivable → document is four hops. Deeper than this is a
#: write-off chain or a loop, and guessing further would be worse than saying so.
MAX_CHAIN_DEPTH = 5


class CsskCashJournalLine(models.Model):
    """One row of the peňažný denník / peněžní deník.

    **Stored, not computed on the fly.** A report that derives the cash basis at
    read time — as Odoo Enterprise's ``account_reports_cash_basis`` does — is
    fine for a management figure and wrong for a statutory book: reconciling an
    old payment next March would silently restate a year already filed, and
    nothing would carry the sequential numbering both statutes ask for ("v
    časovom slede", § 6 ods. 11 ZDP; "v členění potřebném", § 7b ZDP).

    So rows are generated, numbered and kept. Regeneration replaces a window,
    except for rows an accountant typed by hand (``manual``) and rows already
    locked by the company's accounting lock date.

    **One rule decides direction everywhere: a line's own sign.** A credit line
    behind money coming in is income; a debit line is an expense. This replaces
    an earlier draft that prorated ``abs(balance)`` over the money, which was
    wrong twice over — a receipt of 120 net of a 20 bank charge came out as
    85.71 / 14.29 instead of 120 income and 20 expense, and a document carrying
    a negative line inflated both categories. Because every entry balances, the
    signed parts of one movement always add up to the money that moved.

    The direction lives in ``kind`` and the amounts stay positive, because that
    is how the book is read: a príjem column and a výdaj column, never a signed
    one. ``amount_signed`` exists for totals and pivots.
    """

    _name = "cssk.cash.journal.line"
    _description = "Cash Journal Row (peňažný denník)"
    _order = "date, number, id"
    _check_company_auto = True

    company_id = fields.Many2one(
        "res.company", required=True, index=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", readonly=True,
    )
    date = fields.Date(required=True, index=True)
    number = fields.Char(
        index=True, copy=False,
        help="Sequence within the year, assigned in date order when the "
             "denník is generated.",
    )
    ref = fields.Char(
        string="Document No.",
        help="The doklad this row came from — the payment or the statement "
             "line, as the book's 'Doklad' column.",
    )
    label = fields.Char(string="Text")
    partner_id = fields.Many2one("res.partner", index=True)

    kind = fields.Selection(
        [
            ("income", "Income"),
            ("expense", "Expense"),
            ("transit", "Transit (priebežná položka)"),
        ],
        required=True, index=True,
    )
    category_id = fields.Many2one(
        "cssk.cash.category", string="Category", index=True,
    )
    taxable = fields.Boolean(
        string="Affects the tax base",
        help="Copied from the category when the row is generated, so that "
             "recategorising later cannot silently restate a filed year.",
    )
    non_cash = fields.Boolean(
        help="A row that moved no money — depreciation, a tax-base adjustment.",
    )
    payment_kind = fields.Selection(
        [("cash", "Cash (pokladnica)"), ("bank", "Bank (banka)"), ("none", "None")],
        default="none", required=True,
        help="Which of the book's two money columns this row belongs to.",
    )

    amount = fields.Monetary(
        currency_field="currency_id",
        help="Net of VAT for a VAT payer, gross otherwise — whatever reaches "
             "the tax base. Always positive; ``kind`` carries the direction.",
    )
    amount_tax = fields.Monetary(
        string="VAT", currency_field="currency_id",
        help="The VAT part of the same payment. It never reaches the "
             "income-tax base for a VAT payer (SK § 21 ods. 1 písm. i), and is "
             "reported separately.",
    )
    amount_signed = fields.Monetary(
        compute="_compute_amount_signed", store=True,
        currency_field="currency_id",
        help="Positive for income, negative for an expense. For totals.",
    )

    journal_id = fields.Many2one(
        "account.journal", string="Money Journal", check_company=True,
    )
    # ``set null`` rather than ``cascade`` on all four: a book that is read for
    # a filed year must not lose a row because someone deleted the entry behind
    # it. The row keeps its amount and says the source is gone; regeneration
    # will drop it anyway if it is no longer real.
    move_id = fields.Many2one(
        "account.move", string="Money Entry", index=True, ondelete="set null",
        check_company=True,
    )
    move_line_id = fields.Many2one(
        "account.move.line", string="Money Line", index=True,
        ondelete="set null", check_company=True,
    )
    source_move_id = fields.Many2one(
        "account.move", string="Document", index=True, ondelete="set null",
        check_company=True,
        help="The invoice, bill or entry whose category this row carries.",
    )
    source_move_line_id = fields.Many2one(
        "account.move.line", string="Document Line", ondelete="set null",
        check_company=True,
    )

    manual = fields.Boolean(
        copy=False,
        help="Typed by hand. Regeneration leaves these alone.",
    )
    needs_review = fields.Boolean(
        index=True, copy=False,
        help="The row is in the book but something about it could not be "
             "resolved. Never silently dropped.",
    )
    review_reason = fields.Char(copy=False)

    @api.depends("amount", "kind")
    def _compute_amount_signed(self):
        for row in self:
            row.amount_signed = -row.amount if row.kind == "expense" else row.amount

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    @api.model
    def _cssk_regenerate(self, company, date_from, date_to):
        """Rebuild the denník for ``company`` between the two dates.

        Idempotent by construction: generated rows in the window are dropped and
        rebuilt, so running it twice gives the same book. Two kinds of row
        survive — ``manual`` ones, and anything on or before the company's
        accounting lock date, which is the closest thing Odoo has to a filed
        period.

        Returns the rows it created.
        """
        company.ensure_one()
        if date_from > date_to:
            raise UserError(_("The start date must not be after the end date."))

        start = company.cssk_cash_journal_start
        if start and date_from < start:
            date_from = start

        lock = max(
            [date for date in (company.fiscalyear_lock_date,
                               company.hard_lock_date) if date],
            default=None,
        )
        if lock and date_from <= lock:
            date_from = lock + relativedelta(days=1)
        if date_from > date_to:
            raise UserError(_(
                "There is nothing to regenerate: the period ends before the "
                "denník starts, or it is entirely closed by the accounting "
                "lock date (%s).", lock or "",
            ))

        stale = self.search([
            ("company_id", "=", company.id),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
            ("manual", "=", False),
        ])
        stale.unlink()

        vals = self._cssk_collect(company, date_from, date_to)
        rows = self.create(vals)
        self._cssk_assign_numbers(company, date_from)
        return rows

    @api.model
    def _cssk_collect(self, company, date_from, date_to):
        """Build the row values for the window, money rows then non-cash ones."""
        vals = []
        money_lines = self._cssk_money_lines(company, date_from, date_to)
        money_lines.move_id.line_ids.account_id  # one prefetch, not N+1
        for money_line in money_lines:
            vals += self._cssk_money_row_vals(money_line)
        vals += self._cssk_non_cash_row_vals(company, date_from, date_to)
        return vals

    # -- the money -----------------------------------------------------

    @api.model
    def _cssk_money_accounts(self, company):
        """``(bank_accounts, transit_accounts, all_money_accounts)``."""
        journals = self.env["account.journal"].search([
            ("company_id", "=", company.id),
            ("type", "in", ("bank", "cash")),
        ])
        bank_accounts = journals.default_account_id
        transit_accounts = self._cssk_transit_accounts(company)
        liquidity = self.env["account.account"].search([
            ("account_type", "in", LIQUIDITY_TYPES),
            ("company_ids", "in", company.id),
        ])
        return bank_accounts, transit_accounts, \
            bank_accounts | transit_accounts | liquidity

    @api.model
    def _cssk_money_lines(self, company, date_from, date_to):
        """The lines that ARE the money — each movement exactly once.

        Odoo can record one receipt twice over: the payment posts to an
        *outstanding receipts/payments* account and the bank statement line
        posts to the bank account, the two reconciled through the suspense
        account. Taking every liquidity line would double the money; taking only
        the journal's own account would **miss the payment entirely** until a
        statement arrives, which is how a sole trader who never imports
        statements works.

        So a line counts unless the same money is already represented by a line
        on a journal's own account — within its own entry, or anywhere along its
        reconciliation chain.

        **The journal is not part of the test.** An accountant's correction
        posted in the Miscellaneous journal moves real money just as a payment
        does, and filtering on bank/cash journals would leave it out of a book
        that must reconcile to the bank.
        """
        bank_accounts, transit_accounts, money_accounts = \
            self._cssk_money_accounts(company)
        if not money_accounts:
            return self.env["account.move.line"]

        candidates = self.env["account.move.line"].search(
            [
                ("company_id", "=", company.id),
                ("parent_state", "=", "posted"),
                ("date", ">=", date_from),
                ("date", "<=", date_to),
                ("account_id", "in", money_accounts.ids),
            ],
            order="date, id",
        )
        if not candidates:
            return candidates

        matched = self._cssk_matched_bulk(candidates)
        keep = self.env["account.move.line"]
        for line in candidates:
            if line.account_id in bank_accounts:
                keep |= line
                continue
            # Within one entry the bank or till line IS the money and every
            # other money-ish line is its counterpart: a statement entry is
            # *bank* against *suspense*. A transfer, whose two legs are both on
            # real accounts, is unaffected — both are kept.
            if line.move_id.line_ids.account_id & bank_accounts:
                continue
            if not self._cssk_reaches_bank(line, bank_accounts,
                                           transit_accounts, matched):
                keep |= line
        return keep

    @api.model
    def _cssk_reaches_bank(self, line, bank_accounts, transit_accounts, matched,
                           depth=0, seen=None):
        """Has this intermediate leg already been taken over by a bank line?

        Walks the reconciliation chain rather than one hop of it: a payment's
        outstanding line is reconciled to the *suspense* line, and it is the
        suspense line's entry that carries the bank line. A single-hop test
        (the first version of this) left the outstanding line in the book beside
        the statement line and doubled the receipt whenever a customer's
        statement arrived through more than one step.
        """
        if depth >= MAX_CHAIN_DEPTH:
            return False
        seen = seen or set()
        for other_id in matched.get(line.id, ()):
            if other_id in seen:
                continue
            seen.add(other_id)
            other = self.env["account.move.line"].browse(other_id)
            if other.move_id.line_ids.account_id & bank_accounts:
                return True
            if other.account_id in transit_accounts \
                    or other.account_id.account_type in LIQUIDITY_TYPES:
                if self._cssk_reaches_bank(other, bank_accounts,
                                           transit_accounts, matched,
                                           depth + 1, seen):
                    return True
        return False

    @api.model
    def _cssk_transit_accounts(self, company):
        """Accounts that hold money in transit rather than money itself.

        **None of these can be recognised by account type.** Measured on a
        freshly installed 19.0 company: the outstanding receipts account, the
        bank suspense account and the inter-bank transfer account are all
        ``asset_current``; only the bank and till accounts are ``asset_cash``. A
        type-based rule misses every intermediate leg, which is how a first
        draft of this engine generated nothing at all for a payment registered
        through the payment wizard.

        So they are collected from the configuration that created them: the
        chart template's two outstanding accounts (the refs
        ``account_journal_payment_debit_account_id`` /
        ``..._credit_account_id`` that ``account.payment._get_outstanding_account``
        reads), anything a payment method line overrides them with, each
        journal's suspense account, and the company's transfer account.
        """
        chart = self.env["account.chart.template"].with_company(company)
        accounts = self.env["account.account"]
        for ref in ("account_journal_payment_debit_account_id",
                    "account_journal_payment_credit_account_id"):
            accounts |= chart.ref(ref, raise_if_not_found=False) \
                or self.env["account.account"]
        journals = self.env["account.journal"].search([
            ("company_id", "=", company.id),
        ])
        method_lines = self.env["account.payment.method.line"].search([
            ("company_id", "=", company.id),
        ])
        return (
            accounts
            | journals.suspense_account_id
            | method_lines.payment_account_id
            | company.transfer_account_id
        )

    # -- allocation ----------------------------------------------------

    @api.model
    def _cssk_kind(self, line):
        """A line's own sign decides which column it belongs in.

        Credit (negative balance) is money coming in, debit is money going out —
        seen from the counterpart side of a movement, which is where every
        category comes from.
        """
        return "income" if line.balance < 0 else "expense"

    @api.model
    def _cssk_allocate(self, lines, amount, currency):
        """Share ``amount`` out over ``lines`` by their balances.

        Returns ``[(line, share)]`` with positive shares; each line's ``kind``
        comes from its own sign, so what the book must add up to is the
        **signed** total, not the sum of magnitudes.

        That distinction is the whole method. ``amount`` is scaled by
        ``amount / abs(sum(balances))``, so a receipt of 120 with 20 deducted
        allocates 120 and 20 — not 85.71 and 14.29, which is what dividing by
        the sum of magnitudes produced and what made a bank charge eat a third
        of the sale. When the lines exactly balance the money, the scale is 1 and
        every line keeps its own amount.

        Zero-balance lines are dropped first: otherwise one of them absorbs the
        rounding remainder and files real money under nothing. The remainder goes
        to the largest line on the majority side, so the signed parts add up to
        ``amount`` to the cent.
        """
        lines = lines.filtered("balance")
        signed_total = sum(line.balance for line in lines)
        if not signed_total or not amount:
            return []
        scale = amount / abs(signed_total)
        parts = [[line, currency.round(abs(line.balance) * scale)]
                 for line in lines]

        def direction(line):
            return 1 if (line.balance > 0) == (signed_total > 0) else -1

        allocated = sum(share * direction(line) for line, share in parts)
        difference = currency.round(amount - allocated)
        if difference:
            majority = [part for part in parts if direction(part[0]) == 1]
            largest = max(majority or parts, key=lambda part: abs(part[1]))
            largest[1] = currency.round(largest[1] + difference)
        return [(line, share) for line, share in parts if share > 0]

    def _cssk_money_row_vals(self, money_line):
        """Rows for one movement of money.

        The money line says *how much* and *when*; its counterparts say *what
        for*, each in its own direction and for its own amount. Because the
        entry balances, the counterparts' own balances already add up to the
        money — they are scaled only when a part of the movement is followed
        separately.
        """
        move = money_line.move_id
        if not money_line.balance:
            return []
        currency = money_line.company_currency_id
        default_kind = "income" if money_line.balance > 0 else "expense"
        base = {
            "company_id": money_line.company_id.id,
            "date": money_line.date,
            "ref": move.name or money_line.name,
            "label": money_line.name or move.ref or "",
            "partner_id": money_line.partner_id.id,
            "journal_id": money_line.journal_id.id,
            "payment_kind": self._cssk_payment_kind(money_line),
            "move_id": move.id,
            "move_line_id": money_line.id,
        }

        counterparts = move.line_ids - money_line
        parts = self._cssk_allocate(
            counterparts, abs(money_line.balance), currency)
        if not parts:
            return [self._cssk_review_row(
                base, default_kind, abs(money_line.balance),
                _("The entry has no counterpart amount to attribute the money to."),
            )]

        rows = []
        for line, share in parts:
            rows += self._cssk_expand(
                line, share, self._cssk_kind(line), base,
                visited={money_line.id}, depth=0)
        return rows

    @api.model
    def _cssk_payment_kind(self, money_line):
        """Pokladnica or banka, read off the account rather than the journal.

        A correction posted in the Miscellaneous journal can still move the
        till, so the account is what decides which money column it lands in.
        """
        journals = self.env["account.journal"].search([
            ("company_id", "=", money_line.company_id.id),
            ("type", "in", ("bank", "cash")),
        ])
        for journal in journals:
            if journal.default_account_id == money_line.account_id:
                return "cash" if journal.type == "cash" else "bank"
        return "cash" if money_line.journal_id.type == "cash" else "bank"

    # -- following the money to what it paid for -----------------------

    def _cssk_expand(self, line, amount, kind, base, visited, depth):
        """Attribute ``amount`` of money to what ``line`` stands for.

        Three cases, in the order they are tested:

        1. **A receivable or payable** — follow the reconciliation to the
           documents behind it and split each matched part across that
           document's own lines (``_cssk_split_document``).
        2. **Another liquidity or transit account** — an outstanding account, a
           suspense account, a second bank. Follow it one hop further; whatever
           stays unresolved is a genuine priebežná položka.
        3. **Anything else** — a direct income or expense: bank charges, an
           owner's withdrawal, interest. The category comes from the line or its
           account.
        """
        if depth >= MAX_CHAIN_DEPTH:
            return [self._cssk_review_row(base, kind, amount, _(
                "The reconciliation chain is longer than %s hops; resolve it "
                "by hand.", MAX_CHAIN_DEPTH,
            ))]

        account_type = line.account_id.account_type
        if account_type in ("asset_receivable", "liability_payable"):
            return self._cssk_through_reconciliation(
                line, amount, kind, base, visited, depth, documents=True)
        if account_type in LIQUIDITY_TYPES \
                or line.account_id in self._cssk_transit_accounts(line.company_id):
            return self._cssk_expand_transit(
                line, amount, kind, base, visited, depth)
        return [self._cssk_category_row(base, kind, amount, line)]

    def _cssk_expand_transit(self, line, amount, kind, base, visited, depth):
        """Walk one hop of a money-in-transit leg.

        Two hops exist and both are needed, which took a corrected draft to see:

        * **Within the entry.** A payment is *outstanding account* against
          *receivable*; those two are counterparts of one entry and are never
          reconciled to each other. Following only reconciliations stops here
          and reports a transfer where an invoice was paid.
        * **Across entries.** A statement line is *bank* against *suspense*, and
          the suspense line is reconciled to the payment's outstanding line.
          Following only same-entry counterparts stops at the suspense account.

        Same-entry counterparts are tried first, because they are the more
        specific answer; the reconciliation walk is the fallback.
        """
        siblings = line.move_id.line_ids.filtered(
            lambda other: other.id not in visited and other != line)
        parts = self._cssk_allocate(siblings, amount, line.company_currency_id)
        if parts:
            rows = []
            for other, share in parts:
                rows += self._cssk_expand(
                    other, share, self._cssk_kind(other), base,
                    visited | {line.id, other.id}, depth + 1)
            return rows
        return self._cssk_through_reconciliation(
            line, amount, kind, base, visited, depth, documents=False)

    def _cssk_through_reconciliation(self, line, amount, kind, base, visited,
                                     depth, documents):
        """Follow ``line``'s reconciliation and attribute ``amount`` along it.

        ``documents=True`` means the matched lines belong to invoices and bills
        and are expanded into their own categories. ``documents=False`` means we
        are walking a transit account and each matched line is expanded again —
        the payment-then-statement chain.

        What is left unmatched is reported honestly rather than forced:

        * on a **transit** leg it is a *priebežná položka* — money that left one
          pocket and has not yet arrived in the other;
        * on a **receivable or payable** it is money with no document behind it
          yet, which in a cash-basis book is usually a **received or paid
          advance** (a zálohová faktúra is not a taxable event of its own). That
          is a decision for the accountant, so the row carries the account's
          category if it has one and is flagged for review if it does not.
        """
        matched = self._cssk_matched_amounts(line, exclude=visited)
        rows = []
        allocated = 0.0
        currency = line.company_currency_id
        for counterpart, share in matched:
            share = currency.round(min(share, amount - allocated))
            if share <= 0:
                continue
            allocated += share
            if documents:
                rows += self._cssk_split_document(
                    counterpart, share, kind, base)
            else:
                rows += self._cssk_expand(
                    counterpart, share, self._cssk_kind(counterpart), base,
                    visited | {line.id, counterpart.id}, depth + 1)
            if allocated >= amount:
                break

        unmatched = currency.round(amount - allocated)
        if unmatched > 0:
            if documents:
                rows.append(self._cssk_unmatched_row(
                    base, kind, unmatched, line))
            else:
                rows.append(self._cssk_transit_row(base, unmatched, line))
        return rows

    @api.model
    def _cssk_matched_amounts(self, line, exclude):
        """``[(counterpart_line, amount)]`` reconciled against ``line``.

        Read straight off ``account.partial.reconcile`` so both directions are
        covered in one pass, **ordered**, because the caller caps each share at
        what is left of the money: an unordered walk would split the same
        payment differently from one regeneration to the next.
        ``account.partial.reconcile.amount`` is in company currency, which is
        the currency this book is kept in.
        """
        self.env.cr.execute(SQL(
            """
            SELECT CASE WHEN p.debit_move_id = %(line)s
                        THEN p.credit_move_id ELSE p.debit_move_id END AS other,
                   SUM(p.amount) AS amount
              FROM account_partial_reconcile p
             WHERE %(line)s IN (p.debit_move_id, p.credit_move_id)
             GROUP BY other
             ORDER BY other
            """,
            line=line.id,
        ))
        matched = []
        for other_id, amount in self.env.cr.fetchall():
            if other_id in exclude:
                continue
            matched.append(
                (self.env["account.move.line"].browse(other_id), amount))
        return matched

    @api.model
    def _cssk_matched_bulk(self, lines):
        """``{line_id: [counterpart_id, …]}`` for many lines in one query.

        The deduplication pass asks "is this leg already on the bank?" for every
        candidate line in the period; one query per line made that the slowest
        part of a year's regeneration.
        """
        if not lines:
            return {}
        self.env.cr.execute(SQL(
            """
            SELECT p.debit_move_id, p.credit_move_id
              FROM account_partial_reconcile p
             WHERE p.debit_move_id IN %(ids)s OR p.credit_move_id IN %(ids)s
            """,
            ids=tuple(lines.ids),
        ))
        matched = {}
        for debit_id, credit_id in self.env.cr.fetchall():
            matched.setdefault(debit_id, []).append(credit_id)
            matched.setdefault(credit_id, []).append(debit_id)
        return matched

    def _cssk_split_document(self, term_line, amount, kind, base):
        """Split ``amount`` paid on one document across that document's lines.

        **Pro rata across every line and every VAT rate**, which is Odoo's own
        cash-basis convention (``account_reports_cash_basis`` scales each line
        by the matched fraction of the receivable). POHODA instead settles the
        VAT in full out of the first partial payment. Neither is dictated by any
        statute we could establish — the SK JÚ opatrenie (§ 19 ods. 5) leaves
        the allocation to an internal rule, and the CZ answer cites § 37 odst. 2
        ZDPH but is not public — so the choice is ours and this is **one
        overridable method** on purpose.

        Each line keeps **its own direction**: a negative line on an invoice (a
        deduction, a returned deposit) becomes a row in the opposite column
        rather than inflating both categories, which is what prorating absolute
        values did.
        """
        document = term_line.move_id
        currency = term_line.company_currency_id
        base_lines = document.line_ids.filtered(
            lambda line: line.display_type in BASE_DISPLAY_TYPES)
        tax_lines = document.line_ids.filtered(
            lambda line: line.display_type == "tax")
        # Signed sums, for the same reason ``_cssk_allocate`` uses them: a
        # document carrying a deduction is worth the net, and its base and VAT
        # shares of the payment have to be measured against that net.
        total_base = abs(sum(line.balance for line in base_lines))
        total_tax = abs(sum(line.balance for line in tax_lines))
        gross = total_base + total_tax

        if not gross or not total_base:
            # Nothing to attribute the money to: a document of pure VAT, or one
            # whose lines net to zero. Say so rather than dropping the payment,
            # which would leave the book off the bank balance.
            return [self._cssk_review_row(
                dict(base, source_move_id=document.id), kind, amount,
                _("Document %s has no amount to split the payment across.",
                  document.display_name),
            )]

        base_amount = currency.round(amount * total_base / gross)
        tax_amount = currency.round(amount - base_amount)
        base_parts = dict(self._cssk_allocate(base_lines, base_amount, currency))
        tax_parts = dict(self._cssk_allocate(base_lines, tax_amount, currency))

        rows = []
        for line in base_lines:
            line_base = base_parts.get(line, 0.0)
            line_tax = tax_parts.get(line, 0.0)
            if not line_base and not line_tax:
                continue
            row = self._cssk_category_row(
                base, self._cssk_kind(line), line_base, line)
            row.update({
                "amount_tax": line_tax,
                "source_move_id": document.id,
                "source_move_line_id": line.id,
                "label": line.name or row.get("label") or "",
            })
            rows.append(row)
        return rows

    # -- row builders --------------------------------------------------

    def _cssk_category_row(self, base, kind, amount, line):
        """A row whose category comes from a document line or a direct account."""
        category = line._cssk_cash_category()
        vals = dict(
            base,
            kind=kind,
            amount=amount,
            category_id=category.id,
            taxable=category.taxable,
            non_cash=False,
        )
        if not category:
            vals.update({
                "needs_review": True,
                "review_reason": _(
                    "No cash journal category on account %s.",
                    line.account_id.display_name,
                ),
                "taxable": False,
            })
        return vals

    def _cssk_transit_row(self, base, amount, line):
        """Money that moved with nothing yet matched behind it."""
        category = line._cssk_cash_category()
        transit = category if category.kind == "transit" else \
            self.env["cssk.cash.category"]
        vals = dict(
            base,
            kind="transit",
            amount=amount,
            category_id=transit.id,
            taxable=False,
            non_cash=False,
            source_move_id=line.move_id.id,
            source_move_line_id=line.id,
        )
        if not transit:
            # A transit row with no category is not a finished book row: the
            # accountant has to say which priebežná položka it is.
            vals.update({
                "needs_review": True,
                "review_reason": _(
                    "Money in transit through %s with no transit category.",
                    line.account_id.display_name,
                ),
            })
        return vals

    def _cssk_unmatched_row(self, base, kind, amount, line):
        """Money on a receivable or payable with no document behind it yet.

        In a cash-basis book this is normally an advance received or paid, which
        is income or expense when the money moves even though the zálohová
        faktúra itself is not a taxable event. Whether it is taxable here is the
        accountant's call, so it is flagged unless the account itself says.
        """
        category = line._cssk_cash_category()
        vals = dict(
            base,
            kind=kind,
            amount=amount,
            category_id=category.id,
            taxable=category.taxable if category else False,
            non_cash=False,
            source_move_id=line.move_id.id,
            source_move_line_id=line.id,
        )
        if not category:
            vals.update({
                "needs_review": True,
                "review_reason": _(
                    "Payment on %s is not matched to a document — an advance? "
                    "Choose the category.", line.account_id.display_name,
                ),
            })
        return vals

    def _cssk_review_row(self, base, kind, amount, reason):
        return dict(
            base,
            kind=kind,
            amount=amount,
            taxable=False,
            non_cash=False,
            needs_review=True,
            review_reason=reason,
        )

    # -- rows that moved no money --------------------------------------

    @api.model
    def _cssk_non_cash_row_vals(self, company, date_from, date_to):
        """Rows for entries that moved no money.

        Depreciation is the reason this exists: the payment for an asset is not
        an expense (it buys a thing), and the odpis that *is* the expense never
        touches the bank. POHODA keeps these in a separate *nepeněžní deník*;
        here a category flagged ``non_cash`` marks the accounts that belong
        there, and every posted line on such an account becomes a row.
        """
        categories = self.env["cssk.cash.category"].search([("non_cash", "=", True)])
        if not categories:
            return []
        accounts = self.env["account.account"].search([
            ("cssk_cash_category_id", "in", categories.ids),
        ])
        if not accounts:
            return []
        lines = self.env["account.move.line"].search(
            [
                ("company_id", "=", company.id),
                ("parent_state", "=", "posted"),
                ("date", ">=", date_from),
                ("date", "<=", date_to),
                ("account_id", "in", accounts.ids),
                ("journal_id.type", "not in", ("bank", "cash")),
            ],
            order="date, id",
        )
        vals = []
        for line in lines:
            category = line._cssk_cash_category()
            if not category.non_cash or not line.balance:
                continue
            vals.append({
                "company_id": company.id,
                "date": line.date,
                "ref": line.move_id.name,
                "label": line.name or "",
                "partner_id": line.partner_id.id,
                "kind": category.kind,
                "category_id": category.id,
                "taxable": category.taxable,
                "non_cash": True,
                "payment_kind": "none",
                "amount": abs(line.balance),
                "move_id": line.move_id.id,
                "move_line_id": line.id,
                "source_move_id": line.move_id.id,
                "source_move_line_id": line.id,
            })
        return vals

    # -- numbering -----------------------------------------------------

    @api.model
    def _cssk_assign_numbers(self, company, date_from):
        """Number the rows of every year the window touched, in date order.

        The statutes want the records kept in time sequence, and a book whose
        numbering restarts mid-year reads as two books. So numbering is
        recomputed for whole years from ``date_from``'s year onward.

        **The order must not depend on the database id**, because regeneration
        creates new rows for the same facts and the same day's rows would then
        swap numbers between two runs of the same book. Rows are ordered by the
        accounting line behind them, which survives regeneration.
        """
        rows = self.search([
            ("company_id", "=", company.id),
            ("date", ">=", fields.Date.to_date("%s-01-01" % date_from.year)),
        ])
        rows = rows.sorted(key=lambda row: (
            row.date,
            row.move_line_id.id or 0,
            row.source_move_line_id.id or 0,
            row.category_id.id or 0,
            row.id,
        ))
        counters = {}
        for row in rows:
            year = row.date.year
            counters[year] = counters.get(year, 0) + 1
            number = "%s/%05d" % (year, counters[year])
            if row.number != number:
                row.number = number
