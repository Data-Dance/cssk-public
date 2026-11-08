# account_fio: developer notes

Not user documentation: this file is not rendered into a page.

## Rate limiting and the lock

The lock is advisory rather than `SELECT ... FOR UPDATE` on the journal row on
purpose: a row lock would pin a core `account_journal` row for as long as the
call floor — up to 30 seconds, once an hour from the cron — and every unrelated
write to that journal would queue behind it with nothing in the UI to explain
why. This is the same mechanism core uses to serialise on a logical key.

An interactive caller is never made to wait a full interval — it is told when the
next call is possible instead. The cron waits.

- The "last call" timestamp is written before the call. If the request fails the
  transaction rolls back and the stamp is lost, so the next attempt may hit a
  `409` — which arrives as an explanatory message, not as silence.
* Fio operates no test environment, so the live behaviour can only be confirmed
  against a real account.
