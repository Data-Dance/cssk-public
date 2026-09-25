=========
Changelog
=========

All notable changes to **l10n_cssk_partner_balances** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.3] — 2026-09-17
-------------------------

Fixed
~~~~~

- **An Administrator could not open it.** An accounting **Administrator**
  could reach balance confirmations and netting agreements but not their lines
  or wizards and hit *not allowed to access*. On Community,
  ``account.group_account_manager`` does not imply
  ``account.group_account_user`` (and on Enterprise ``account_accountant``
  only adds ``group_account_basic``), so a model granted to
  ``group_account_user`` alone is closed to an Administrator who lacks "Show
  Full Accounting Features". The confirmation and the netting agreement
  already granted it. ``group_account_manager`` now has the same access as
  ``group_account_user`` on their lines and on the confirmation and netting
  wizards. Takes effect on module update.

[19.0.1.1.2] — 2026-09-13
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

[19.0.1.1.1] — 2026-09-13
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

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.2] — 2026-07-04
-------------------------

Fixed
~~~~~

- Wave 2 partner-balance correctness: the open-AR/AP snapshot and the netting
  auto-allocation / reconciliation were tightened for accuracy.
- Form-load performance: open-balance reconciliation resolved via ``_read_group``
  instead of an N-per-line query fan-out (down to ≤3 queries).

[2026-06-30] — i18n sweep & baseline
------------------------------------

Added
~~~~~

- Slovak/Czech **saldokonto** — ``cssk.partner.confirmation`` (mail.thread) +
  ``cssk.partner.confirmation.line``: a stored, reproducible snapshot of a
  partner's open receivables and payables as of a date, a state machine
  (draft → sent → agreed / disputed), a bilingual SK/EN countersign PDF, a bulk
  issue wizard, and disputed lines that can be blocked (excluded from totals,
  still shown on the PDF).
- **Mutual offsetting (zápočet)** — ``cssk.partner.netting.agreement`` with picker
  wizard: auto-allocates the offset up to ``min(receivables, payables)``, on
  posting builds a clearing entry (credit AR / debit AP) and reconciles the
  offset invoices (partial offsetting supported), undo via cancel-with-reversal,
  ``ZAP/YYYY/NNNN`` sequence. Two legal modes: bilateral (countersigned before
  effect) and unilateral (effective on delivery, no countersignature), the PDF
  switching wording between them.
- CE-clean (Odoo core ``account`` + ``mail``); complements OCA ``partner_statement``.
  Full cs_CZ + sk_SK translations.
