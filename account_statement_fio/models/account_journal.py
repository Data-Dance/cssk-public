# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Pulling movements and official statements out of Fio."""

import json
import logging
import re
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.account_fio_base.utils.client import (
    FioHistoryLocked,
    FioTooMuchData,
    mask_token,
)
from odoo.addons.account_fio_base.utils.statement import parse_movements

_logger = logging.getLogger(__name__)

#: ``column_18`` of a movement in another currency: ``20.00 EUR``. Strict on
#: purpose, the column is free text.
_FIO_SPECIFICATION_RE = re.compile(
    r"^\s*(?P<amount>-?\d[\d ]*(?:[.,]\d+)?)\s+(?P<currency>[A-Z]{3})\s*$")

#: §3.1 — beyond this, Fio needs the history unlocked in internet banking.
HISTORY_LIMIT_DAYS = 90

#: A backfill is cut into chunks this wide, to stay under the 50 000-movement
#: cap of §8.6 without asking the user to do the arithmetic.
CHUNK_DAYS = 31

PULL_MODES = [
    ("movements", "Movements (re-readable date range)"),
    ("official", "Official numbered statements"),
    ("bookmark", "Since the bookmark on the token"),
]


class AccountJournal(models.Model):
    # The class name is LOAD-BEARING. ``__get_bank_statements_available_sources``
    # starts with a double underscore, so Python mangles every reference to it
    # into ``_AccountJournal__get_bank_statements_available_sources`` — using
    # the name of the class the reference is *written in*. Core declares the
    # base in a class called ``AccountJournal``
    # (account/models/account_journal.py:52), so an override in a class called
    # anything else would call a mangled name nothing defines: ``super()``
    # would fall through to ``AttributeError``, or worse, a differently-named
    # override would simply never be reached and the base sources would vanish
    # without a word. Core's own Enterprise override spells it out the same way
    # (account_online_synchronization/models/account_journal.py:16-21), naming
    # the class in ``super()`` rather than using a bare ``super()``, so a
    # rename fails loudly instead of silently.
    _inherit = "account.journal"

    def __get_bank_statements_available_sources(self):
        # EXTENDS account
        rslt = super(AccountJournal, self).__get_bank_statements_available_sources()
        rslt.append(("fio", _("Fio banka API")))
        return rslt

    fio_pull_mode = fields.Selection(
        selection=PULL_MODES,
        string="Fio Pull Mode",
        default="movements",
        required=True,
    )
    fio_overlap_days = fields.Integer(
        string="Fio re-read days",
        default=3,
        help="In movements mode, each run re-reads this many days before "
             "today. Movements already imported are dropped, so the overlap "
             "costs nothing and closes the hole a missed run would leave.",
    )
    fio_create_statements = fields.Boolean(
        string="Group Fio movements into statements",
        default=False,
        help="Movements mode only. Official statements always produce an "
             "account.bank.statement, because that is the point of them.",
    )
    fio_last_pull_at = fields.Datetime(readonly=True, copy=False)
    fio_last_movement_id = fields.Char(
        string="Last Fio movement",
        readonly=True,
        copy=False,
        help="Highest Fio movement id imported so far. Informational — "
             "duplicate detection uses the statement line's import key.",
    )
    fio_last_statement_year = fields.Integer(readonly=True, copy=False)
    fio_last_statement_number = fields.Integer(readonly=True, copy=False)

    @api.constrains("bank_statements_source", "fio_token_read")
    def _check_fio_source_has_a_token(self):
        """A journal fed by Fio with no read token is a misconfiguration, and
        the next cron run is a bad place to learn about it — it would post the
        same failure to the chatter every hour for as long as nobody looked.

        Constrained on ``fio_token_read`` itself rather than on the stored
        ``fio_has_token_read`` compute: a constraint that triggers on derived
        state depends on when the recompute is flushed relative to the
        validation, and a write that sets the token and the source together is
        exactly the case where that ordering decides whether the constraint
        sees the truth. The real field has no such question.

        ``self.sudo()`` because the token is administrator-only, and an
        accountant who may set the bank feed must get this refusal rather than
        an access error.
        """
        for journal in self.sudo():
            has_token = bool((journal.fio_token_read or "").strip())
            if journal.bank_statements_source == "fio" and not has_token:
                raise ValidationError(_(
                    "Journal %(name)s is set to be fed by the Fio banka API, "
                    "but it has no Fio read token. Ask an administrator to "
                    "paste one into the journal's Fio banka section — it is "
                    "generated in internet banking under Nastavení → API.",
                    name=journal.display_name,
                ))

    # ------------------------------------------------------------------
    # mapping
    # ------------------------------------------------------------------

    @api.model
    def _fio_has_symbol_fields(self):
        """True when a module supplying VS/KS/SS on statement lines is installed."""
        return "variable_symbol" in self.env["account.bank.statement.line"]._fields

    def _fio_label(self, transaction):
        """The statement-line label, in the order a human would look for it.

        Fio scatters the useful text over four columns and fills whichever the
        movement type happens to use: a transfer carries the message for the
        recipient, a card payment carries the merchant in "Uživatelská
        identifikace", a fee carries nothing but its type.
        """
        for key in ("message_for_recipient", "comment", "user_identification",
                    "transaction_type"):
            value = transaction.get(key)
            if value:
                return value
        return _("Fio movement %s", transaction.get("movement_id") or "")

    def _fio_counter_account(self, transaction):
        """``2222233333/2010`` — the form the partner-matching hook expects."""
        number = transaction.get("counter_account")
        if not number:
            return None
        bank_code = transaction.get("counter_bank_code")
        return "%s/%s" % (number, bank_code) if bank_code else number

    def _fio_symbol_tokens(self, transaction):
        """``VS:… KS:… SS:…`` — kept in the label whether or not the symbol
        fields exist, so ``resolve_symbol`` and manual searching both work."""
        tokens = []
        for label, key in (("VS", "vs"), ("KS", "ks"), ("SS", "ss")):
            value = transaction.get(key)
            if value:
                tokens.append("%s:%s" % (label, value))
        return tokens

    def _fio_line_vals(self, transaction):
        """One Fio movement → ``account.bank.statement.line`` values."""
        self.ensure_one()
        label_parts = [self._fio_label(transaction)] + self._fio_symbol_tokens(transaction)
        vals = {
            "date": transaction["date"],
            "amount": float(transaction["amount"]),
            "payment_ref": " ".join(part for part in label_parts if part),
            "transaction_type": transaction.get("transaction_type"),
            "unique_import_id": "fio-%s" % transaction["movement_id"],
            "raw_data": json.dumps(
                {k: str(v) for k, v in transaction.items()},
                ensure_ascii=False, sort_keys=True,
            ),
            "fio_movement_id": str(transaction["movement_id"]),
        }
        if transaction.get("instruction_id"):
            vals["fio_instruction_id"] = str(transaction["instruction_id"])
        if transaction.get("counter_account_name"):
            vals["partner_name"] = transaction["counter_account_name"]
        if self._fio_counter_account(transaction):
            vals["account_number"] = self._fio_counter_account(transaction)
        if transaction.get("payer_reference"):
            vals["ref"] = transaction["payer_reference"]
        if self._fio_has_symbol_fields():
            for field_name, key in (
                ("variable_symbol", "vs"),
                ("constant_symbol", "ks"),
                ("specific_symbol", "ss"),
            ):
                if transaction.get(key):
                    vals[field_name] = transaction[key]
        self._fio_check_currency(transaction)
        vals.update(self._fio_foreign_amount_vals(transaction))
        return vals

    def _fio_check_currency(self, transaction):
        """Refuse a movement that is not in the journal's currency.

        Fio reports every movement of an account in that account's currency
        (``column_14``), and each currency is a separate Fio account with its
        own token. A mismatch therefore means the journal is configured for
        another currency than the account behind its token, and importing
        would book, say, 100 EUR as 100 CZK. This used to log a warning and
        import anyway; the cron isolates each journal, so refusing stops only
        the misconfigured one.
        """
        currency = transaction.get("currency")
        journal_currency = self.currency_id or self.company_id.currency_id
        if currency and journal_currency and currency != journal_currency.name:
            raise UserError(_(
                "Fio journal %(journal)s is in %(journal_currency)s, but the "
                "account behind its token reports movement %(movement)s in "
                "%(currency)s. Each Fio currency account needs its own journal "
                "in that currency, with that account's own API token.",
                journal=self.display_name,
                journal_currency=journal_currency.name,
                movement=transaction.get("movement_id"),
                currency=currency,
            ))

    def _fio_foreign_amount_vals(self, transaction):
        """The original amount of a movement made in another currency.

        Fio puts it in ``column_18`` (*Upřesnění*) as free text, e.g.
        ``20.00 EUR`` for a card payment abroad. Only that exact shape is read,
        and only for a currency Odoo has active; anything else stays in
        ``raw_data`` and the line is imported in the account currency alone.
        The sign follows the movement, since the text carries none reliably.
        """
        text = (transaction.get("specification") or "").replace("\u00a0", " ")
        match = _FIO_SPECIFICATION_RE.match(text)
        if not match:
            return {}
        code = match.group("currency")
        journal_currency = self.currency_id or self.company_id.currency_id
        if code == journal_currency.name:
            return {}
        currency = self.env["res.currency"].search([("name", "=", code)], limit=1)
        if not currency:
            return {}
        try:
            original = abs(float(match.group("amount").replace(" ", "")
                                 .replace(",", ".")))
        except ValueError:
            return {}
        if not original:
            return {}
        sign = -1 if float(transaction["amount"]) < 0 else 1
        return {
            "foreign_currency_id": currency.id,
            "amount_currency": sign * original,
        }

    # ------------------------------------------------------------------
    # importing
    # ------------------------------------------------------------------

    def _fio_import_lines(self, transactions, statement_vals=None):
        """Create the lines Odoo does not have yet. Returns the new lines."""
        self.ensure_one()
        journal = self
        StatementLine = self.env["account.bank.statement.line"]
        if self.env.context.get("scheduled"):
            StatementLine = StatementLine.with_context(tracking_disable=True)
        speeddict = journal._statement_line_import_speeddict()
        account_number = journal.bank_account_id.sanitized_acc_number

        candidates = []
        for transaction in transactions:
            vals = self._fio_line_vals(transaction)
            journal._statement_line_import_update_unique_import_id(
                vals, account_number,
            )
            candidates.append(vals)

        keys = [vals["unique_import_id"] for vals in candidates]
        known = set(
            StatementLine.sudo()
            .search([("unique_import_id", "in", keys)])
            .mapped("unique_import_id")
        )
        fresh = [vals for vals in candidates if vals["unique_import_id"] not in known]
        if not fresh:
            return StatementLine.browse()

        for vals in fresh:
            vals["journal_id"] = journal.id
            journal._statement_line_import_update_hook(vals, speeddict)

        if statement_vals is not None:
            lines = self._fio_attach_to_statement(statement_vals, fresh)
        else:
            lines = StatementLine.create(fresh)

        highest = max(
            (int(t["movement_id"]) for t in transactions if t.get("movement_id")),
            default=None,
        )
        # ``fio_last_pull_at`` is deliberately NOT written here: this method
        # returns early when nothing is new, which stamped a quiet-but-healthy
        # feed as last pulled weeks ago. It is stamped in ``fio_pull`` instead.
        if highest and (
            not self.fio_last_movement_id or int(self.fio_last_movement_id) < highest
        ):
            self.sudo().fio_last_movement_id = str(highest)
        return lines

    def _fio_attach_to_statement(self, statement_vals, line_vals):
        """Put the new lines on the statement of that name, creating it once.

        A statement can be pulled again — a re-read window that overlaps it, a
        retry after a partial import — and every one of those must land on the
        same ``account.bank.statement``. Creating a second one with the same
        name would split the bank's own document in two and break its balance
        check.
        """
        self.ensure_one()
        Statement = self.env["account.bank.statement"]
        statement = Statement.search([
            ("journal_id", "=", self.id),
            ("name", "=", statement_vals["name"]),
        ], limit=1)
        new_lines = [(0, 0, vals) for vals in line_vals]
        if statement:
            before = statement.line_ids
            statement.write(dict(statement_vals, line_ids=new_lines))
            return statement.line_ids - before
        statement = Statement.create(dict(
            statement_vals, journal_id=self.id, line_ids=new_lines,
        ))
        return statement.line_ids

    def _fio_parse(self, raw):
        return parse_movements(raw, self.fio_download_format)

    # ------------------------------------------------------------------
    # the three modes
    # ------------------------------------------------------------------

    def _fio_pull_movements(self, date_from, date_to):
        """``/rest/periods/`` — idempotent, and therefore the safe default."""
        self.ensure_one()
        lines = self.env["account.bank.statement.line"]
        for chunk_from, chunk_to in self._fio_chunks(date_from, date_to):
            raw = self._fio_call(
                "periods", chunk_from, chunk_to, self.fio_download_format,
            )
            parsed = self._fio_parse(raw)
            statement_vals = None
            if self.fio_create_statements and parsed.transactions:
                statement_vals = {
                    "name": "%s/%s" % (self.code or "FIO", chunk_from),
                }
                self._fio_add_balances(statement_vals, parsed.info)
            lines |= self._fio_import_lines(parsed.transactions, statement_vals)
        return lines

    def _fio_pull_official(self, limit=12):
        """``/rest/lastStatement/`` + ``/rest/by-id/`` — the auditable mode.

        Each statement becomes an ``account.bank.statement`` named with Fio's
        own number and carrying its opening and closing balance, so Odoo's
        balance check compares against the document the bank issued.
        """
        self.ensure_one()
        year, number = self._fio_call("last_statement")
        lines = self.env["account.bank.statement.line"]
        wanted = self._fio_statements_to_fetch(year, number, limit)
        for fetch_year, fetch_number in wanted:
            raw = self._fio_call(
                "by_id", fetch_year, fetch_number, self.fio_download_format,
            )
            parsed = self._fio_parse(raw)
            if not parsed.transactions:
                self.sudo().write({
                    "fio_last_statement_year": fetch_year,
                    "fio_last_statement_number": fetch_number,
                })
                continue
            statement_vals = {"name": "%s/%s" % (fetch_number, fetch_year)}
            self._fio_add_balances(statement_vals, parsed.info)
            lines |= self._fio_import_lines(parsed.transactions, statement_vals)
            self.sudo().write({
                "fio_last_statement_year": fetch_year,
                "fio_last_statement_number": fetch_number,
            })
        return lines

    def _fio_statements_to_fetch(self, year, number, limit):
        """Which official statements are still missing, oldest first.

        Statement numbering restarts every year, so a year change means picking
        up at number 1 rather than continuing to count.
        """
        self.ensure_one()
        if not self.fio_last_statement_year:
            return [(year, number)]
        if self.fio_last_statement_year == year:
            first = self.fio_last_statement_number + 1
            return [(year, n) for n in range(first, number + 1)][:limit]
        # A new year: take what is left of this one. Any tail of the previous
        # year has to be fetched deliberately, from the wizard.
        return [(year, n) for n in range(1, number + 1)][:limit]

    def _fio_pull_bookmark(self):
        """``/rest/last/`` — gapless, but it moves state that lives on the token."""
        self.ensure_one()
        raw = self._fio_call("last", self.fio_download_format)
        parsed = self._fio_parse(raw)
        return self._fio_import_lines(parsed.transactions)

    def _fio_add_balances(self, statement_vals, info):
        if info.opening_balance is not None:
            statement_vals["balance_start"] = float(info.opening_balance)
        if info.closing_balance is not None:
            statement_vals["balance_end_real"] = float(info.closing_balance)

    def _fio_chunks(self, date_from, date_to):
        """Cut a range into pieces small enough for the 50 000-movement cap."""
        chunks = []
        start = date_from
        while start <= date_to:
            end = min(start + timedelta(days=CHUNK_DAYS - 1), date_to)
            chunks.append((start, end))
            start = end + timedelta(days=1)
        return chunks

    # ------------------------------------------------------------------
    # entry points
    # ------------------------------------------------------------------

    def fio_pull(self):
        """Pull according to the journal's configured mode."""
        self.ensure_one()
        if self.fio_pull_mode == "official":
            lines = self._fio_pull_official()
        elif self.fio_pull_mode == "bookmark":
            lines = self._fio_pull_bookmark()
        else:
            today = fields.Date.context_today(self)
            lines = self._fio_pull_movements(
                today - timedelta(days=max(self.fio_overlap_days, 0)), today,
            )
        # Stamped for every completed pull, not only for one that imported
        # something. It used to be written inside ``_fio_import_lines``, which
        # returns early when there is nothing new — so a journal that had
        # simply been quiet showed a "last pull" weeks in the past, and an
        # operator asking "is this feed still alive?" got the wrong answer from
        # the one field that exists to tell them.
        self.sudo().fio_last_pull_at = fields.Datetime.now()
        return lines

    def action_fio_pull(self):
        lines = self.fio_pull()
        message = (
            _("%(count)s new transaction(s) imported.", count=len(lines))
            if lines else _("Nothing new — Fio has no movements Odoo does not "
                            "already have.")
        )
        self.message_post(body=message)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"type": "success", "message": message, "sticky": False},
        }

    @api.model
    def _fio_cron_pull_statements(self):
        """One run per journal. Never lets one bank kill the whole schedule."""
        # One switch, not two. ``bank_statements_source`` is a single-valued
        # radio, so a journal is either fed by Fio or by something else and the
        # two can never disagree — where a separate "scheduled pull" boolean
        # alongside it would eventually be found off while the source said Fio,
        # and the support question writes itself. ``l10n_be_codaclean`` keys its
        # own cron the same way.
        #
        # ``_check_fio_source_has_a_token`` guarantees every journal this
        # returns has a read token, so there is nothing further to filter.
        journals = self.sudo().search([("bank_statements_source", "=", "fio")])
        for account in journals:
            # A SAVEPOINT rather than the whole transaction: a bare
            # cr.rollback() discards every account already pulled in this run,
            # so one bank failing late would silently undo all the earlier
            # ones — and it is forbidden inside a test, which is how that was
            # found.
            #
            # Used as a CONTEXT MANAGER, and with the default flush=True.
            # Both matter, and getting either wrong is silent:
            #
            # * ``Savepoint.close()`` is ``close(self, *, rollback=True)``. So
            #   calling ``savepoint.close()`` bare on the success path — which
            #   reads exactly like "release this savepoint" — ROLLS IT BACK.
            #   Every statement line the pull had just created was thrown away
            #   at the moment the pull succeeded. ``__exit__`` passes
            #   ``rollback=exc_type is not None``, which is the intent.
            # * ``flush=False`` returns the plain ``Savepoint``, whose
            #   ``rollback()`` does NOT ``cr.clear()``. The record's own
            #   ``write()`` calls were still sitting unflushed in the ORM cache
            #   at rollback time, so they SURVIVED it and were written
            #   afterwards. That is what made the failure invisible: the cron
            #   left ``last_read_at``, ``last_pull_at`` and the correct
            #   ``last_movement_id`` behind, and no lines — a run that looked
            #   like a success in every field an operator would check. And a
            #   genuinely failed pull advanced the bookmark past movements it
            #   had discarded, so the next run skipped them for good.
            #   ``_FlushingSavepoint`` clears the cache on rollback.
            #
            # Diagnosed on the 18.0 twin of this code, where a staging run
            # imported 15 lines interactively and zero from the cron.
            try:
                with self.env.cr.savepoint():
                    account.with_context(scheduled=True).fio_pull()
            except Exception as exception:  # noqa: BLE001 — one bad account
                _logger.warning(
                    "Fio: pull failed for %s", account.display_name, exc_info=True,
                )
                # Posting happens AFTER the savepoint has been rolled back, so
                # the explanation survives the rollback of the failure it
                # explains.
                #
                # Masked: this handler catches ``Exception``, not just
                # ``FioError``, so it can be handed a message the client never
                # sanitised — and Fio carries the token in the URL path, which
                # is exactly what a stray ``requests`` message would quote into
                # a chatter every follower of this journal can read.
                account.message_post(body=_(
                    "The scheduled Fio pull failed: %(error)s",
                    error=mask_token(str(exception)),
                ))

    # ------------------------------------------------------------------
    # guard rails
    # ------------------------------------------------------------------

    def _fio_check_history_window(self, date_from, confirmed):
        """Refuse to walk into a ``422`` without telling the user why.

        The internet-banking unlock lasts ten minutes (§3.1), so it has to
        happen immediately before the run — which is exactly the kind of thing
        an error message after the fact cannot fix.
        """
        self.ensure_one()
        limit = fields.Date.context_today(self) - timedelta(days=HISTORY_LIMIT_DAYS)
        if date_from >= limit or confirmed:
            return
        raise UserError(_(
            "Fio serves movements older than %(days)s days only while the full "
            "history is unlocked for this token: open internet banking, go to "
            "Nastavení → API and click the padlock on this token. The unlock "
            "lasts ten minutes, so do it now and then tick the confirmation "
            "box.", days=HISTORY_LIMIT_DAYS,
        ))

    def _fio_explain(self, exception):
        """Turn the bank's terser failures into something actionable."""
        if isinstance(exception, FioHistoryLocked):
            return _(
                "Fio refused the request as reaching further back than 90 days "
                "without an unlocked history. Unlock it in internet banking "
                "(Nastavení → API, the padlock) and retry within ten minutes."
            )
        if isinstance(exception, FioTooMuchData):
            return _(
                "That range holds more than 50 000 movements, which Fio will "
                "not serve at once. Pull it in shorter pieces."
            )
        # The fallback is the only branch that returns the bank's own words, so
        # it is the only one that could ever be carrying a token — the read
        # endpoints put it in the URL PATH — and this string goes straight into
        # a UserError in the manual pull wizard. FioClient masks what it raises,
        # so this is the second layer rather than the only one; the branches
        # above return our own text and need nothing.
        #
        # No ensure_one(): this runs inside an exception handler, where raising
        # would replace a diagnosable failure with an opaque one. mask_token
        # still strips token-shaped path segments without being told the token,
        # so the multi-record case degrades to the generic mask rather than to
        # a crash.
        known = self.sudo().fio_token_read if len(self) == 1 else None
        return mask_token(str(exception), known)
