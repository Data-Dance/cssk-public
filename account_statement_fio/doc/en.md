---
title: Fio banka — Bank Statements
summary: Pulls transactions and official numbered statements from the Fio banka API into the bank journal every hour, with VS/KS/SS and counterparty accounts.
verified: 19.0.2.4.1
---

## What it is for {#purpose}

With this module a Fio banka journal fills itself: every hour Odoo asks the
Fio API for new transactions and creates the statement lines, with the
counterparty's account, the payment symbols and the message. There is no file
to download and import. It works the same on Community and Enterprise, and for
Czech and Slovak Fio accounts.

It needs the connection set up in
[module:account_fio](module:account_fio#setup): a **read token** on the
journal.

## Turning it on {#setup}

1. On the bank journal (*Accounting → Configuration → Accounting →
   Journals*), set **Bank Feeds** to **Fio banka API**. A journal set to Fio
   without a read token cannot be saved.
2. In the **Fio banka** section, the right-hand column *Bank statements*
   appears. Choose the **Fio Pull Mode** (below) and, in movements mode, the
   **Fio re-read days**.
3. Press **Pull now** to fetch the first batch. From then on the scheduled
   action *Fio: pull bank statements* runs every hour.

Because *Bank Feeds* holds one value, Fio and Odoo Enterprise's own bank
synchronisation cannot both feed the same journal — which would import every
transaction twice. A journal fed by Fio is also no longer prompted to
"connect your bank" on the Accounting dashboard.

The tokens themselves stay usable when *Bank Feeds* is something else: a
journal can send payments to Fio while its statements arrive another way.

## Pull modes {#modes}

| Fio Pull Mode | What each run does | Good for |
|---|---|---|
| **Movements (re-readable date range)** — default | reads the transactions from *today − re-read days* to today and adds those Odoo does not have yet | day-to-day matching; a missed run or a restart leaves no gap |
| **Official numbered statements** | asks Fio for the number of its latest statement and fetches every statement Odoo does not have yet (up to 12 per run); each becomes a bank statement named `<number>/<year>` with the bank's own opening and closing balance | the accounting close: Odoo's balance check compares against the document the bank issued |
| **Since the bookmark on the token** | fetches everything since a bookmark that Fio keeps on the token, and moves it | only with a token used by nothing else |

Notes:

- **Re-read days** (default 3): the overlap costs nothing, because
  transactions already imported are dropped.
- **Group Fio movements into statements** (movements mode only, off by
  default): one statement per day that has movements, named `<journal
  code>/<date>`, with its opening and closing balance worked out from the
  balance Fio reports for the start of the range plus the movements before
  it. A re-read day lands on the statement it already has, so each statement
  adds up to its balances.
- **Official statements, first run**: only the latest statement is fetched.
  At the turn of the year the module starts again at statement 1 of the new
  year. Older statements, and the rest of the previous year, are fetched with
  *Pull a range…*.
- **The bookmark** lives inside Fio, on the token. Anything else that reads
  movements with the same token — another program, a colleague testing — moves
  it, and those movements never arrive in Odoo.

## Fetching a range by hand {#backfill}

**Pull a range…** on the journal (also in the journal's *Action* menu) opens
*Pull from Fio*:

- *Movements in a date range*: from–to dates (the last 7 days by default);
- *Official numbered statements*: a year and the first and last statement
  number.

The wizard tells you how many calls the request means — at one call every
30 seconds, a year of movements cut into monthly chunks takes about six
minutes.

**Older than 90 days**: Fio serves such data only while the full history is
unlocked for the token in internet banking (*Nastavení → API*, the padlock),
and the unlock lasts **ten minutes**. The wizard asks you to unlock it first
and tick *History unlocked in internet banking*; the **Pull** button appears
only then.

## What lands on a statement line {#mapping}

| Fio | Odoo |
|---|---|
| ID pohybu (movement ID) | the line's import key and *Fio Movement ID* |
| Datum | date (the booking date as Fio states it) |
| Objem | amount |
| Protiúčet + Kód banky | counterparty account `number/bank code`, used to find the partner |
| Název protiúčtu | partner name |
| VS, KS, SS | the symbol fields (with [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#bank-statements)) and `VS:…` tokens in the label |
| Zpráva pro příjemce, else Komentář, else Uživatelská identifikace, else Typ | label (the first that is filled) |
| Typ | transaction type |
| Reference plátce | reference |
| ID pokynu | *Fio Instruction ID* |
| Upřesnění in the form `20.00 EUR` | the original amount and currency of a payment made in another currency |

The whole Fio record is also kept on the line. Duplicates are recognised by
the movement ID only. The instruction ID is shared by a transfer and its fee,
or a payment and its later reversal, so it is deliberately not used.

## When something goes wrong {#errors}

- A scheduled pull that fails posts *The scheduled Fio pull failed: …* in the
  journal's chatter; the other journals are pulled regardless.
- A transaction in another currency than the journal's stops the pull for that
  journal: each Fio currency account needs its own journal in that currency,
  with its own token.
- *Pull now* reports how many new transactions arrived, or that there was
  nothing new. *Fio Last Pull At* is updated by every completed pull, even one
  that found nothing.

## Limitations {#limitations}

- **Switching from GPC files to the API** does not recognise transactions
  already imported from GPC: the two use different import keys. Switch at a
  date boundary — import the last GPC statement, then start the pull the next
  day.
- **Group Fio movements into statements**: the daily statements are Odoo's,
  not the bank's documents; for statements numbered and balanced by Fio itself
  use *Official numbered statements*. Lines imported before grouping was
  switched on are not moved onto a statement, so a day that has some of them
  will not add up. If Fio's own figures for a range do not add up, the
  statements of that run are created without balances.
- The original amount of a foreign-currency payment is read only from
  *Upřesnění* in the exact form `20.00 EUR`; anything else stays in the
  stored record. This still needs confirming against a live multi-currency
  account.
- In official mode a run fetches at most 12 missing statements; a longer gap
  is closed over several runs or with *Pull a range…*.
- On Enterprise the module brings in two OCA base modules
  (`account_statement_base`, `account_statement_import_base`) for the import
  key and the partner matching.
