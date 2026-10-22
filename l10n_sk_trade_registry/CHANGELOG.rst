=========
Changelog
=========

All notable changes to **l10n_sk_trade_registry** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the source are
  deliberately left untranslated — the source IS the translation, per the
  hybrid convention for these modules — so an empty ``msgstr`` there is correct
  rather than missing.

Added
~~~~~

- **Predmety podnikania** (``l10n.sk.register.activity``) from ORSR / ŽRSR,
  with their validity and suspension windows, and a partner-level warning when
  one is under an open-ended suspension — the subject stays active but may not
  do that work. **Not the same thing as SK NACE**: NACE is one statistical code
  classifying what a company *is*, a predmet podnikania is a legal
  authorisation to do specific work, and it lapses independently.
- **Účtovné závierky** (``l10n.sk.register.filing``) filed to RÚZ, plus
  *Posledná závierka* and *Roky bez závierky*. Metadata only — ORSF carries no
  figures — but whether and when a customer filed is a credit fact that needs
  none. Nothing known reports as **0 overdue, not late**: unknown and late are
  different facts and only one is the register's.
- **Previous names and seats** (``l10n.sk.register.history``), which is what
  lets a historic document with an unfamiliar header be reconciled.
- An **"Ask ORSF to re-read the registers"** button. ORSF's own copy is
  sometimes incomplete — register coordinates null while the RPO and FS data is
  all present, which looks exactly like a mapping failure on our side. It calls
  ``POST /companies/{ico}/refresh``, which is **live and anonymous but absent
  from ORSF's OpenAPI document**, and is **asynchronous**: the data appears
  about a minute later, so the button says "come back", it does not re-read.
  Found by diagnosing a partner whose Register tab stayed empty; after the
  refresh the same Update produced the full § 3a sentence.

Added
~~~~~

- **Register status is now stored, not just shown once in a dropdown.**
  ``l10n_sk_register_status`` (aktívna / pozastavená / zrušená / vymazaná /
  neznámy), ``l10n_sk_dissolved_on`` and ``l10n_sk_register_checked_on``, with
  a computed ``l10n_sk_register_inactive`` for domains and decorations.
- A banner on the contact and a muted row in the contact list for a subject the
  register no longer shows as trading, plus a *Zrušené subjekty (SK)* action.
- A non-blocking warning on any invoice or bill whose counterparty is dissolved,
  deleted or suspended. On a **vendor bill** it adds that the deduction itself
  is in question, which is the more expensive direction of the mistake.

Notes
~~~~~

- The warning does not block. Documents are legitimately booked for dissolved
  subjects — a final invoice, a late credit note, a bill arriving after the
  counterparty wound up. The document's own date decides that, not the
  register's state today, and only a person can weigh it.
- An unrecognised status parses to **False**, not to ``unknown``: "we did not
  understand the answer" and "the register says it does not know" are different
  facts, and only the second one is the register's.
- ``l10n_sk_register_checked_on`` is stamped on every enrichment. A status is
  only worth as much as its date.

[19.0.1.0.0] — 2026-09-05
-------------------------

Added
~~~~~

- Register coordinates on ``res.partner`` — **Register**, **Registrový súd**,
  **Číslo zápisu** — mirrored onto ``res.company``.
- A composed **§ 3a Obchodného zákonníka** statement, with the Slovak
  declension the sentence needs: locative for the register, genitive for the
  keeping authority, *Zapísaná* for a company and *Zapísaný* for a živnostník.
- Sync into ``l10n_sk``'s ``res.company.trade_registry``, which is the field
  the external layout prints.

Notes
~~~~~

- ``oddiel`` / ``vložka`` wording is used **only** for the Obchodný register.
  A Živnostenský register number can also contain a slash, and labelling its
  parts with the commercial register's vocabulary would put words on a
  statutory document that the issuing register does not use.
- The module records the sentence it last wrote, so it never overwrites wording
  a person typed — and never leaves its own wording standing after the
  coordinates were cleared. Stale statutory text on an invoice is precisely the
  failure the module exists to prevent, so clearing has to propagate.
- Unrecognised registers and authorities pass through verbatim rather than
  being declined by guesswork.
