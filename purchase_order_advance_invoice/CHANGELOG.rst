=========
Changelog
=========

All notable changes to **purchase_order_advance_invoice** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Fixed
~~~~~

- The *advance purchase journal* picker in Settings listed every journal: Odoo
  drops a string domain when it copies a field into a related one.

[19.0.1.2.0] — 2026-10-27
-------------------------

Fixed
~~~~~

- **The deduction covers what was paid but not yet documented.** With a
  posted tax document the deduction copied the document's lines only, so an
  advance paid in full but documented in part was deducted in part. The
  undocumented rest is now deducted gross, without VAT. A second bill no
  longer copies the tax documents again after an earlier deduction.
- **The expected tax-document date is the statutory one**: 15 days in the
  Czech Republic (§ 28 odst. 8 ZDPH), the later of 15 days and the month end in
  Slovakia (§ 73 ods. 1 písm. b) zákona o DPH, payments from 2016). It was the
  earlier of the two for everybody, so suppliers were chased before they were
  late. Existing advances are recomputed on update.
- **The supplier is chased once, in any language.** The cron recognised its
  own activity by an English summary that is translated for a Slovak or Czech
  user, and scheduled a new one every day. The activity now has its own type,
  *Chase Advance Tax Document*.

[19.0.1.1.0] — 2026-09-13
-------------------------

Added
~~~~~

- **Slovak and Czech catalogues — the module had none at all.** 120 of its 122
  messages are translated; on a Slovak or Czech database its menus, actions and
  selections were English sitting in the middle of a localized form
  ("Received Advance Invoices", "Deduct Advance Invoices", "Advance Invoice
  (issued)"). English source with ``.po`` catalogues is right here because this
  is a generic module, not an ``l10n_*`` one — the national-language-in-source
  rule applies to the localization modules.
- Shipped as ``sk.po`` / ``cs.po``, the short form Odoo core uses. The sale-side
  module carries both ``sk.po`` and ``sk_SK.po``; that duplication is not
  copied here.

Notes
~~~~~

- Two messages are deliberately left untranslated: ``advance_purchase_order_id``
  and ``advance_invoice_parent_order_id``. They are field technical names
  reaching the catalogue from ``purchase_order.py``, not user-facing text, and
  translating a technical name would be wrong. They are worth removing at
  source rather than rendering.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.1] — 2026-07-18
-------------------------

Added
~~~~~

- "Received Advance Invoices" menu entry under Accounting → Vendors, just
  before Payments (visible to purchase and accounting users).

[19.0.1.0.0] — 2026-07-15
-------------------------

Added
~~~~~

- Initial release. Purchase-side mirror of ``sale_order_advance_invoice``:
  received proformas as their own ``PADV`` purchase orders (never posted),
  outbound payments to the reconcilable clearing account (wizard or
  link-existing-payment), "Register Received Tax Document" wizard creating
  a draft vendor bill in the dedicated purchase journal (net on the paid
  advances account, payable leg on the clearing account, supplier's number
  mandatory in ``ref``, taxable supply date = payment date, accounting date
  freely editable), automatic clearing reconcile on posting, automatic
  deduction of paid advances on bills created from the parent purchase
  order and a "Deduct Advance Invoices" wizard for standalone advances
  (net + taxes with a posted tax document, gross without), the
  received-advances register (kniha) with overdue-document filters and a
  daily chase-the-supplier activity cron.
