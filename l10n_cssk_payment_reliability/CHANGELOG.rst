=========
Changelog
=========

All notable changes to **l10n_cssk_payment_reliability** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.0] — 2026-09-27
-------------------------

Added
~~~~~

- **The check runs again at payment.** The §69 ods. 14 SK / §109 CZ liability
  attaches to *paying* an unregistered account, and weeks can pass between a
  bill and its payment. Posting an outbound supplier payment now checks the
  account it actually pays and keeps the same snapshot on the payment, with a
  banner and a chatter note. It warns and never blocks, like the bill check.
- **Daily re-check of unpaid bills** (cron *Supplier reliability: re-check
  unpaid bills*): posted vendor bills not yet paid are checked again once their
  last check is a week old, so a supplier that drops its registered account or
  its rating before payment is noticed.
- A **VAT-deregistration listing** hook (``_cssk_get_vat_deregistration``),
  snapshotted on bills and payments and warned about. ``None`` (unavailable)
  and ``False`` (not listed) are kept apart: a register that did not answer is
  not a clean record.

Fixed
~~~~~

- A register failure inside the bill-post check was swallowed without a
  savepoint, so a database error there left the cursor aborted under a
  "successful" post. The check now runs in its own savepoint, as do the new
  payment and scheduled checks.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **Payment check, daily re-check, deregistration hook and the savepoint fix
  (19.0.1.1.0, 2026-09-27).** 18.0 carries this module and still checks at
  bill posting only; the savepoint fix applies to its ``_post`` hook as well.

[19.0.1.0.4] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Code translations that Odoo was never loading.** An entry whose references
  are ``code:addons/...`` is treated as a Python translation only if it carries
  the extracted comment ``#. odoo-python`` — ``_load_python_translations``
  filters on exactly that and never on the reference. Without it an entry can
  name the right ``.py``, carry a correct msgstr, pass ``msgfmt --check``, and
  be silently ignored for ever. This module's hand-added entries were in that
  state. Repaired by ``tools/fix_po_code_comments.py``, which is also the CI
  check; the offline exporter now emits the comment itself.

[19.0.1.0.3] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Terms the translation catalogue never carried.** Strings that reach the
  user were absent from the template — a field with no ``string=``, a mixin
  field addressed to the abstract model's ``ir.model.fields`` row rather
  than each concrete one, or a whole category the offline exporter never
  emitted. An absent term cannot be translated and shows English in an
  otherwise Slovak or Czech screen. The template and the catalogues now carry them,
  and the Slovak or Czech is written.

[19.0.1.0.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- **The chatter posted its own HTML as visible text.** ``message_post``
  ESCAPES a plain ``str`` and renders only a ``markupsafe.Markup`` —
  ``mail_thread.py`` states it on the parameter and applies it at
  ``'body': escape(body)``. Nothing failed: the post succeeded and the log was
  clean, which is why it survived to a user.
- Built as ``Markup(template) % args`` rather than by wrapping the finished
  string. ``%`` on a ``Markup`` escapes what it substitutes; wrapping the join
  renders it — and the interpolated values here are not ours, so the shorter
  fix would have turned an escaping bug into an injection one.

- One site: the supplier reliability warnings, concatenated with
  ``"<br/>"``. Now ``Markup("<br/>").join(...)``, which escapes each
  warning — they carry supplier names straight from the register.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.1] — 2026-07-04
-------------------------

Changed
~~~~~~~

- Wave 2 external-call hardening on the shared supplier-check spine: register
  lookups performed by the country providers now run with request timeouts and
  surfaced errors, so a register outage degrades gracefully rather than hanging
  the bill.

[2026-06-30] — i18n sweep & baseline
------------------------------------

Added
~~~~~

- Country-neutral base for the CZ/SK **supplier reliability check** (guarantor
  liability — ručenie za daň §69/14 SK, ručení §109 CZ): on a vendor bill it
  checks the supplier's tax reliability and whether the bank account being paid
  is one registered/published with the tax authority.
- Result **snapshotted onto the bill** (status + registered accounts + timestamp)
  as point-in-time proof, with a chatter warning; it **never blocks** the
  payment. Actual register lookups live in the country providers
  (``l10n_sk_payment_reliability`` …).
- CE-clean (Odoo core ``account`` + ``l10n_cssk_core``). Full cs_CZ + sk_SK
  translations.
