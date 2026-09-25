=========
Changelog
=========

All notable changes to **l10n_cssk_vies** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.2] — 2026-09-06
-------------------------

Fixed
~~~~~

- **"Check now" silently discarded an unsaved VAT edit.** The guard read
  ``if (!record.resId && !(await record.save()))``, so on an existing partner
  the save never ran: VIES was queried against the *stored* number, the
  consultation number was stamped for it, and ``record.load()`` then reverted
  the number the user had just typed — under a green tick. It saves
  unconditionally now (a no-op on a clean record).

Added
~~~~~

- A **VIES** notebook page holding the consultation number, the request and
  fault dates, and the name and address VIES has on file. That is evidence to
  read once, not seven rows to scroll past on every contact.
- A green tick / red cross beside the *Check now* button (``vies_status_badge``
  widget) showing the verdict at a glance, and opening the VIES page when
  clicked. Nothing when the partner has never been checked.

  The page is opened by clicking its tab, which is a plain
  ``<a class="nav-link" name="vies_proof">`` whose own handler calls
  ``Notebook.activatePage`` — there is no public API for activating a page from
  outside. The tab is found by walking up the ancestors of the clicked glyph,
  which needs no container-class assumption and scopes correctly for free: the
  first ancestor holding a matching tab is this record's own form, so a record
  opened in a dialog cannot activate the tab of the form behind it.

Fixed
~~~~~

- **The VIES block floated free of the rest of the form.** It was anchored on
  ``vies_valid``, which ``base_vat`` (priority 15) puts inside
  ``<span class="text-nowrap ps-2">`` within the ``vat_vies_container`` div
  that it *moves* ``vat`` into. Everything appended after it therefore landed
  inside that span: no label cell, and the span's own left padding pushed the
  button right of the value column. The rows are now placed after the whole
  container, so "VIES" sits in the label column and the button lines up with
  the values above it.
- **The consultation number and the timestamp overlapped.** Putting them on one
  ``o_row`` cannot work: ``.o_row > span`` is ``flex: 0 1 auto``, so a span
  shrinks below its own content and the text spills out of its box onto the
  next one — and ``text-nowrap``, tried as a fix, guarantees the spill instead
  of preventing it. Only the button and a single glyph share that row now;
  everything with a variable width has its own labelled row on the VIES page.
- **The test suite never ran.** ``setUpClass`` in both test modules set the
  company's VAT to ``SK2022334455``, which fails the SK mod-11 checksum, so
  ``base_vat`` raised before a single test executed. Replaced with a
  checksum-valid number; 14 tests now run where 0 did.

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

- Wave 2 external-call hardening: the direct EU VIES REST call runs with request
  timeouts and surfaces transient member-state faults (system down, rate limit)
  as a fault — never silently flipping a partner to *invalid*.

[2026-06-30] — i18n sweep & baseline
------------------------------------

Added
~~~~~

- **Direct EU VIES** on top of core ``base_vat``: calls the European Commission
  VIES REST service directly (per-company opt-in), no Odoo IAP and no Odoo
  account needed.
- **Proof of check**: stores the VIES consultation number (``requestIdentifier``),
  the check timestamp, the VIES request date, and the registered trader name +
  name-match result on the partner.
- A manual **Check VIES (direct)** action and a daily cron refreshing stale
  checks for companies in direct mode.
- CE-clean (``base_vat`` + ``l10n_cssk_core``). Full cs_CZ + sk_SK translations.
