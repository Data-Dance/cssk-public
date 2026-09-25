=========
Changelog
=========

All notable changes to **currency_rate_update_cz** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.0] — 2026-09-13
-------------------------

Added
~~~~~

- **The provider list is no longer empty after install.** Nothing in the OCA
  ``currency_rate_update`` family ships a provider record, so installing a
  provider module added service options to a selection and left the list blank
  — which reads as a broken module rather than as a configuration step. A
  ``post_init_hook`` now creates the statutory provider for every company whose
  fiscal country is Czechia: service ``CNB``, daily.

  **The service differs from the Slovak sibling on purpose.** A Czech company
  values against the *kurz devizového trhu* published by Česká národní banka; a
  Slovak one values against the ECB reference rate that NBS republishes. They
  are different numbers, and mirroring one country's default onto the other
  would be wrong in exactly the way the statutory modules in this repo keep
  having to warn about.

  It configures the currencies the database already has ACTIVE, and it does not
  activate any. A company with no active foreign currency gets no provider at
  all, because there would be nothing to fetch.

  Idempotent, and it never touches a provider that already exists — including
  an ARCHIVED one, which is somebody's decision that a live sibling would
  silently reverse. That is also why this is a hook and not ``_load_data``,
  which rewrites what it loads on every upgrade.

  A server action on the provider list re-runs it. "Fill non-publishing days"
  is set when ``currency_rate_update_sk`` is also installed — ČNB does not
  publish on weekends either, but that field belongs to the Slovak module and
  is not worth a dependency.

  ⚠️ The daily cron is active by default in OCA ``currency_rate_update`` and
  ``res.company.currency_rates_autoupdate`` defaults to True, so a provider
  created here starts writing ``res.currency.rate`` on the next cron run.

Robustness (from a GPT-5.3-Codex review)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **The record rule could fool the existence check into creating a duplicate.**
  ``currency_rate_update`` puts a multi-company rule on the provider
  (``company_id in company_ids``). Read as the caller, the "does one already
  exist" search returns nothing for a company the caller is not in — so the
  code concluded there was none and created a SECOND provider, which the same
  rule then hid from them. The check now reads with ``sudo()``; creation stays
  unprivileged and the company list is still whatever the caller can see, so it
  reads more than it may write and escalates nothing. There is a test.

- **The server action needed a rights check, not a groups field.** Odoo 19 has
  no ``groups_id`` on ``ir.actions`` — an XML field of that name fails the
  module's own data load, so the first attempt at restricting the action would
  have broken the install outright. The action is therefore visible to everyone
  who can see the provider list, which by ``currency_rate_update``'s ACL
  includes the Accounting Manager, who has READ and nothing else. It now checks
  ``has_access("create")`` and says who can run it instead of raising
  AccessError at them.

Not changed, and why: the review recommended creating the provider ``active =
False`` as a safeguard against OCA's daily cron being on by default. Shipping
it inactive would only half-fix the reported problem — the list stops being
empty but no rate is ever fetched, and the user has to know to go and switch it
on. It is left active because the exposure is bounded and the behaviour is the
correct one: ``_scheduled_update`` gives a daily provider
``date_from = next_run - 1 day`` and ``date_to = today``, so the first run
writes two days of rates and not a backfill of history; the rate itself is
statutory rather than a preference; and OCA's own posture is already "on" (the
cron ships active and ``res.company.currency_rates_autoupdate`` defaults True).
The off switch is that per-company setting, which is where a user would look
for it.

A residual, accepted: two concurrent runs could both miss the existence check
and create a duplicate, because the base model has no UNIQUE constraint on
(company, service) for an IntegrityError to catch. ``post_init_hook`` runs
inside an exclusive install and the server action is a deliberate click, so the
window is not reachable in practice.

Fixed before the version ever landed (found by a live install)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **The company's own currency was going onto the fetch list.** The currency
  selection read ``available_currency_ids`` off a ``new()`` record and filtered
  with ``currency != company.currency_id``. Reading an x2many off an in-memory
  record returns ids wrapped as ``NewId(...)`` — ``convert_to_cache`` says so
  outright, "x2many field value of new record is new records" — so the
  comparison was ``NewId(126) != 126``, TRUE for every row, and the filter
  removed nothing. ``.ids`` afterwards *does* resolve to origins, so the create
  looked perfectly normal; only the comparison was corrupted. Nothing about the
  code reads wrong and only a live run showed it.

  It now asks ``_get_supported_currencies()`` (plain strings, safe on a
  throwaway record) and does a real search excluding the company currency in
  SQL — which also gets ``active_test`` applied properly rather than by
  assumption.

- **A stale fiscal country made the hook create nothing at all.** The company
  filter read ``account_fiscal_country_id or country_id``, which looks like a
  fallback and is not one: ``compute_account_tax_fiscal_country`` fills the
  fiscal country only WHEN IT IS EMPTY and never re-syncs, so a database built
  from the US-defaulted template and then made Slovak keeps
  ``account_fiscal_country_id = US`` for ever. The ``or`` therefore saw a stale
  value as present and the fallback could never fire — precisely on the
  databases needing it. A live install created ZERO providers on a company whose
  country was SK. It now matches on EITHER field: a false positive is a provider
  archived in one click, a false negative is silence.

- The "no currency to fetch" test deactivated currencies, which Odoo refuses
  outright ("This currency is set on a company and therefore cannot be
  deactivated") on any database with more than the one company the test just
  made. It now patches the resolver instead of mutating global state.

Confirmed live against ECB: the first ``_update`` over a four-day window wrote
exactly four rates, one per date, for USD only — EUR correctly got none, and
there is no backfill of history. ``_scheduled_update()`` wrote nothing at
install time because ``next_run`` is already today and is not due until
tomorrow, so installing the module does not itself reach out to the provider.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Česká národní banka (ČNB) daily fixing registered as a
  ``res.currency.rate.provider`` for the OCA ``currency_rate_update`` framework.
- CE-compatible: no Enterprise ``currency_rate_live`` dependency.
- Parses the ČNB ``Amount|Currency|Code|Rate`` feed; for a CZK-base company the
  stored rate is ``Amount / Rate`` (foreign per CZK), e.g. ``1|EUR|24.170`` → 1/24.170
  and ``100|JPY|13.043`` → 100/13.043.
- Licensed AGPL-3, matching the ``currency_rate_update`` framework it derives from.
