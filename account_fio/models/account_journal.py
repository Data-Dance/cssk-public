# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""The Fio connection: tokens on the bank journal, and the call throttle.

Fio binds one token to one account (§2 of the API documentation), and Odoo
already has exactly one record per bank account: the journal. A separate
``fio.account`` table was a strict 1:1 extension of it, so everything here now
lives on ``account.journal`` directly — including the chatter and the
token-expiry activities, which ``account.journal`` carries natively and which
belong where an accountant actually looks.
"""

import logging
import time
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.account_fio_base.utils import client as fio_client
from odoo.addons.account_fio_base.utils.statement import parse_movements

_logger = logging.getLogger(__name__)

#: How long before expiry the cron starts nagging.
EXPIRY_WARNING_DAYS = 14

#: Never block an interactive request for longer than this; the cron may.
#:
#: It has to be **below** ``MIN_CALL_INTERVAL``, or the guard is dead code: the
#: wait can never exceed the interval itself, so a threshold of 35 s against a
#: 30 s floor meant the branch was unreachable and a user pressing *Pull* was
#: silently frozen for up to 30 seconds instead of being told to come back. Five
#: seconds is about as long as a button may hang without looking broken.
MAX_INTERACTIVE_WAIT = 5

#: Namespace for the advisory lock, so the key cannot collide with another
#: user of PostgreSQL's single-key advisory locks.
#:
#: ``pg_try_advisory_xact_lock`` has a two-argument form taking (classid,
#: objid), which is what makes the key exact. The single-argument form takes a
#: bigint, and everybody reaches for ``hashtext(...)`` to produce one — but
#: ``hashtext`` is a 32-bit hash into a namespace shared with every other
#: single-key user in the database, so two unrelated subsystems can collide and
#: refuse each other. Here the classid is ours and the objid is the journal id,
#: so the only thing that can contend for this key is another Fio call on the
#: same journal, which is exactly the intent.
#: The value is arbitrary and fixed: b"fio!" read as a big-endian int32.
FIO_LOCK_CLASS = 0x66696F21


class AccountJournal(models.Model):
    _inherit = "account.journal"

    # -- credentials ---------------------------------------------------
    # Fio puts the token in the URL path. Administrators only.
    fio_token_read = fields.Char(
        string="Fio Read Token",
        groups="base.group_system",
        copy=False,
        help="Token with the right 'Sledování účtu'. Used by the statement "
             "pull. Generate it in Fio internet banking under Nastavení → API; "
             "it becomes usable 5 minutes after authorisation.",
    )
    fio_token_write = fields.Char(
        string="Fio Submit Token",
        groups="base.group_system",
        copy=False,
        help="Token with the right 'Sledování účtu a zadávání platebních a "
             "inkasních příkazů'. Used only when a payment order is sent. Keep "
             "it separate from the read token: a token that can only read "
             "cannot pay anyone, and each token has its own 30-second budget.",
    )
    # Recorded by hand: Fio's API never reports a token's expiry, so nothing
    # here can fill these in. An empty one is "unknown", not "never expires" —
    # Fio refuses to issue a token without an expiry — but the expiry cron
    # cannot tell the two apart and skips a blank one, so the warning does not
    # fire. Both help texts say so, because the field is the only place a user
    # finds out.
    fio_token_read_expiry = fields.Date(
        string="Fio Read Token Expires",
        help="Fio caps a token's validity at 180 days and refuses to issue one "
             "without an expiry, so every token has one — but the API does not "
             "report it. Copy it from internet banking when you paste the "
             "token: left empty, the expiry warning cannot fire and the feed "
             "will stop without notice.",
    )
    fio_token_write_expiry = fields.Date(
        string="Fio Submit Token Expires",
        help="Fio caps a token's validity at 180 days and refuses to issue one "
             "without an expiry, so every token has one — but the API does not "
             "report it. Copy it from internet banking when you paste the "
             "token: left empty, the expiry warning cannot fire and payment "
             "orders will start failing without notice.",
    )
    # Stored, so the Fio journal list can be filtered on them and a dead
    # connection is visible without opening every journal. Whether a token is
    # set is not user-dependent — only its *value* is restricted — so this is
    # readable by everyone while the token itself is not.
    fio_has_token_read = fields.Boolean(
        string="Fio Read Token Set",
        compute="_compute_fio_has_tokens",
        store=True,
    )
    fio_has_token_write = fields.Boolean(
        string="Fio Submit Token Set",
        compute="_compute_fio_has_tokens",
        store=True,
    )

    # -- settings ------------------------------------------------------
    fio_download_format = fields.Selection(
        selection=[("xml", "Fio XML"), ("json", "Fio JSON")],
        string="Fio Download Format",
        default="xml",
        required=True,
        help="Fio XML is schema-backed and its dates are unambiguous; the JSON "
             "encoding returns epoch milliseconds where the documentation "
             "promises a date string. Change this only if you have a reason.",
    )

    # -- state ---------------------------------------------------------
    fio_last_read_at = fields.Datetime(
        string="Fio Last Read Call", readonly=True, copy=False,
    )
    fio_last_write_at = fields.Datetime(
        string="Fio Last Submit Call", readonly=True, copy=False,
    )

    # -- what the bank says the account is -----------------------------
    fio_account_number = fields.Char(readonly=True, copy=False)
    fio_bank_code = fields.Char(readonly=True, copy=False)
    fio_iban = fields.Char(string="Fio IBAN", readonly=True, copy=False)
    fio_bic = fields.Char(string="Fio BIC", readonly=True, copy=False)
    fio_currency = fields.Char(readonly=True, copy=False)

    @api.depends("fio_token_read", "fio_token_write")
    def _compute_fio_has_tokens(self):
        """Let a non-administrator see *whether* a token is set, not its value."""
        for journal in self:
            journal_sudo = journal.sudo()
            journal.fio_has_token_read = bool(journal_sudo.fio_token_read)
            journal.fio_has_token_write = bool(journal_sudo.fio_token_write)

    @api.constrains("fio_token_read", "fio_token_write")
    def _check_fio_tokens(self):
        for journal in self.sudo():
            for token in (journal.fio_token_read, journal.fio_token_write):
                if token and len(token.strip()) != 64:
                    raise ValidationError(_(
                        "A Fio token is a 64-character string (§2 of the API "
                        "documentation). Got %(length)s characters — the value "
                        "was probably truncated when it was copied.",
                        length=len(token.strip()),
                    ))

    # ------------------------------------------------------------------
    # calling the bank
    # ------------------------------------------------------------------

    def _fio_token(self, kind):
        self.ensure_one()
        # sudo: the tokens are administrator-only fields, but every accountant
        # allowed to pull a statement has to be able to use them.
        journal = self.sudo()
        token = journal.fio_token_write if kind == "write" else journal.fio_token_read
        if not token and kind == "write":
            raise UserError(_(
                "No Fio submit token on %(name)s. Generate one in Fio internet "
                "banking with the right 'Sledování účtu a zadávání platebních "
                "a inkasních příkazů'.", name=self.display_name,
            ))
        if not token:
            raise UserError(_(
                "No Fio read token on %(name)s. Generate one in Fio internet "
                "banking under Nastavení → API.", name=self.display_name,
            ))
        return token.strip()

    def _fio_lock(self):
        """Serialise everything using this journal's tokens.

        An advisory lock keyed on the journal, not a row lock on the journal
        itself. ``SELECT ... FOR UPDATE`` would pin a core ``account_journal``
        row for up to 30 seconds — the length of Fio's call floor — once an
        hour from the cron, and every unrelated write to that journal would
        block behind it for reasons nothing in the UI could explain. The lock
        is released when the transaction ends, exactly like the row lock was,
        and this is the same mechanism core uses to serialise on a logical key
        (``mail.thread``).

        It is re-entrant within a transaction: a caller that reaches here twice
        acquires the same key twice and does not deadlock against itself.
        """
        self.ensure_one()
        self.env.cr.execute(
            "SELECT pg_try_advisory_xact_lock(%s, %s)",
            (FIO_LOCK_CLASS, self.id),
        )
        if not self.env.cr.fetchone()[0]:
            raise UserError(_(
                "Another Fio operation is running on %(name)s. Fio allows one "
                "call per token every 30 seconds, so this one has to wait — "
                "try again shortly.", name=self.display_name,
            ))
        # The lock made another transaction's commit visible; drop the cached
        # timestamps so the throttle below reads what is actually in the table.
        self.invalidate_recordset(["fio_last_read_at", "fio_last_write_at"])

    def _fio_wait_for_slot(self, kind, interactive):
        """Sleep out the remainder of Fio's 30-second floor (§5.2)."""
        self.ensure_one()
        journal = self.sudo()
        last = journal.fio_last_write_at if kind == "write" else journal.fio_last_read_at
        if not last:
            return
        elapsed = (fields.Datetime.now() - last).total_seconds()
        wait = fio_client.MIN_CALL_INTERVAL - elapsed
        if wait <= 0:
            return
        if interactive and wait > MAX_INTERACTIVE_WAIT:
            raise UserError(_(
                "Fio allows one call per token every %(interval)s seconds; the "
                "next one is possible in %(wait)s s.",
                interval=fio_client.MIN_CALL_INTERVAL, wait=int(wait),
            ))
        _logger.debug(
            "Fio: waiting %.1fs for the rate limit on %s", wait, self.display_name,
        )
        time.sleep(wait)

    def _fio_stamp(self, kind):
        """Record that the token was used.

        Written before the call, not after: if the request fails the
        transaction rolls back and the stamp is lost, and the *next* attempt
        would then be sent too early. Writing first at least stamps every call
        that completes, and a lost stamp surfaces as a ``409`` with an
        explanatory message rather than as silence.
        """
        self.sudo().write({
            "fio_last_write_at" if kind == "write" else "fio_last_read_at":
                fields.Datetime.now(),
        })

    def _fio_call(self, method, *args, **kwargs):
        """Run one ``FioClient`` method under the lock and the throttle.

        :param method: name of a :class:`FioClient` method.
        :param kind: ``'read'`` (default) or ``'write'`` — picks the token.
        :param interactive: refuse to block a user for a full interval.
        """
        self.ensure_one()
        kind = kwargs.pop("kind", "read")
        interactive = kwargs.pop("interactive", not self.env.context.get("scheduled"))
        self._fio_lock()
        self._fio_wait_for_slot(kind, interactive)
        client = fio_client.FioClient(
            self._fio_token(kind),
            timeout=int(self.env["ir.config_parameter"].sudo().get_param(
                "account_fio.request_timeout", fio_client.REQUEST_TIMEOUT,
            )),
        )
        self._fio_stamp(kind)
        return getattr(client, method)(*args, **kwargs)

    # ------------------------------------------------------------------
    # actions
    # ------------------------------------------------------------------

    def action_fio_test_connection(self):
        """One cheap call, and check that Fio agrees about which account this is."""
        self.ensure_one()
        today = fields.Date.context_today(self)
        try:
            raw = self._fio_call(
                "periods", today, today, self.fio_download_format, kind="read",
            )
            info = parse_movements(raw, self.fio_download_format).info
        except fio_client.FioError as exception:
            # Same contract as the upload and pull paths: FioError is a plain
            # Exception, so letting it escape an RPC-facing button surfaces as
            # a bare "Internal server error" with the diagnosis stripped off —
            # which is the whole value of this button.
            #
            # Masked again, though FioClient already masked what it raised.
            # The read endpoints put the token in the URL PATH, and this
            # handler is the one most likely to be holding a bad-token failure
            # built from that URL — so it is the right place not to depend on
            # the client having got it right, nor on this ``except`` clause
            # staying narrower than ``Exception``.
            raise UserError(
                fio_client.mask_token(str(exception), self.sudo().fio_token_read)
            ) from None
        self.sudo().write({
            "fio_account_number": info.account_id,
            "fio_bank_code": info.bank_id,
            "fio_iban": info.iban,
            "fio_bic": info.bic,
            "fio_currency": info.currency,
        })
        self._fio_check_account_matches(info)
        message = _(
            "Connected. Fio reports account %(account)s/%(bank)s (%(iban)s), "
            "currency %(currency)s.",
            account=info.account_id, bank=info.bank_id, iban=info.iban,
            currency=info.currency,
        )
        self.message_post(body=message)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"type": "success", "message": message, "sticky": False},
        }

    def _fio_check_account_matches(self, info):
        """Refuse a token that belongs to a different account than the journal.

        A token is bound to one account (§2). Pointing it at the wrong journal
        files somebody else's movements into these books, and nothing in the
        payload would ever say so.
        """
        self.ensure_one()
        bank_account = self.bank_account_id
        if not bank_account or not info.iban:
            return
        journal_iban = (bank_account.acc_number or "").upper().replace(" ", "")
        if bank_account.acc_type == "iban" and journal_iban != info.iban.upper():
            raise UserError(_(
                "This token belongs to Fio account %(fio)s, but journal "
                "%(journal)s is configured with %(journal_account)s. One token "
                "serves one account — using it here would import another "
                "account's movements.",
                fio=info.iban, journal=self.display_name,
                journal_account=bank_account.acc_number,
            ))
        # A bank journal carries currency_id only when it differs from the
        # company's, so relying on it alone left the check off for every
        # journal in the company currency — which is most of them.
        journal_currency = self.currency_id or self.company_id.currency_id
        if journal_currency and info.currency and journal_currency.name != info.currency:
            raise UserError(_(
                "Fio keeps this account in %(fio)s while the journal is in "
                "%(journal)s.", fio=info.currency, journal=journal_currency.name,
            ))

    # ------------------------------------------------------------------
    # cron
    # ------------------------------------------------------------------

    @api.model
    def _fio_cron_check_token_expiry(self):
        """Warn before a token dies. Fio caps validity at 180 days (§2).

        Without this the integration simply stops, and the first sign is a bank
        feed that has been quietly stale for a week.
        """
        today = fields.Date.context_today(self)
        horizon = today + timedelta(days=EXPIRY_WARNING_DAYS)
        journals = self.sudo().search([
            "|",
            ("fio_has_token_read", "=", True),
            ("fio_has_token_write", "=", True),
        ])
        for journal in journals:
            for field_name, label in (
                ("fio_token_read_expiry", _("read token")),
                ("fio_token_write_expiry", _("submit token")),
            ):
                expiry = journal[field_name]
                if not expiry or expiry > horizon:
                    continue
                if journal.activity_ids.filtered(
                    lambda activity, f=field_name: f in (activity.note or "")
                ):
                    continue
                journal.activity_schedule(
                    "mail.mail_activity_data_todo",
                    date_deadline=expiry,
                    summary=_("Fio %(label)s expires", label=label),
                    note=_(
                        "The Fio %(label)s on %(name)s expires on %(date)s "
                        "(field %(field)s). Generate a new one in internet "
                        "banking; it becomes usable 5 minutes after "
                        "authorisation.",
                        label=label, name=journal.display_name, date=expiry,
                        field=field_name,
                    ),
                    user_id=journal._fio_expiry_activity_user().id,
                )

    def _fio_expiry_activity_user(self):
        """Whoever will actually go and generate a new token.

        The cron user is usually a bot, so an activity assigned to it is an
        activity nobody sees.
        """
        self.ensure_one()
        # ``has_group`` rather than a search on the group m2m: it honours
        # implied groups, and the field name differs between 18.0
        # (``groups_id``) and 19.0 (``group_ids``), which this side-steps.
        candidates = self.env["res.users"].search([
            ("company_ids", "in", self.company_id.id),
            ("share", "=", False),
            ("active", "=", True),
        ])
        managers = candidates.filtered(
            lambda user: user.has_group("account.group_account_manager")
        )
        return managers[:1] or self.env.user
