=========
Changelog
=========

All notable changes to **l10n_cssk_receipt_capture** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Fixed
~~~~~

- The *Receipt Journal* picker in Settings listed every journal: Odoo drops a
  string domain when it copies a field into a related one.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **The 19.0.1.1.0 capture rework (2026-10-19).** 18.0's
  ``l10n_cssk_receipt_capture`` predates it: no QR decoding from the
  photograph, no attempt log or provider fall-through, receipt times stored as
  local-as-UTC, escaped chatter markup, a ``uid``-named local beside ``_()``, no
  simplified-invoice limit, and a bill with no date for a receipt without one.
  Port with its migration.

[19.0.1.1.0] — 2026-10-19
-------------------------

Added
~~~~~

- **QR codes are read off the photograph.** Until now nothing decoded an image:
  ``qr_raw`` was filled only by hand, so a photographed receipt could never
  reach a code-reading provider. Every code on the image is decoded (zxing-cpp,
  optional here and required by the providers that need it) and offered to the
  providers; the first one a provider recognises is used. A loyalty-app QR
  printed above the fiscal code — the case that defeated "take the first QR" —
  is ignored and said so in *Codes on the photograph*. A code that is present but
  unreadable is reported as such, not as "no code".
- **Scan Receipt** (camera): a client action on Odoo's own scanner (native
  BarcodeDetector with the bundled ZXing fallback) that captures from a scanned
  QR, rejects a code no provider recognises with a hint, and opens the result.
- ``cssk.receipt.attempt``: one row per attempt by each provider — outcome,
  message, model, tokens, cost (failed calls included), duration. The receipt
  shows the count and the total cost; a retry no longer overwrites the history.
- Provider fall-through: ``ProviderUnavailable`` (switched off, not configured,
  quota spent) moves on to the next provider; ``CaptureFailed`` stops with the
  reason. Transient failures are retried on a schedule (15 min, 1 h, 4 h) by a
  cron; permanent ones never are.
- Printed-identifier lookup: when a reading supplies the fiscal identifiers
  printed beside an unreadable QR, a provider that can look them up rebuilds
  the key; the authority's figures replace the reading only if its total matches
  the photograph's, and the receipt is parked for review if nothing matches.
- **Simplified-invoice limit** (verified against the consolidated texts in force
  1. 1.–31. 12. 2026): above 400 EUR incl. VAT for a Slovak receipt
  (§ 74 ods. 3 písm. b) with § 51 ods. 1 písm. a) zákona č. 222/2004 Z. z.) or
  10 000 CZK for a Czech one (§ 30 odst. 1 zákona č. 235/2004 Sb.) the purchase
  is booked in full at its gross amount with the VAT as cost, and no VAT is
  claimed. Not a review stop. *Full invoice held* restores the deduction, and
  posting refuses a document that claims VAT the receipt does not allow.
- ``issue_tz``: the receipt's own time zone.

Changed
~~~~~~~

- The provider is chosen afresh on every capture instead of reusing the last
  one, so a receipt the AI failed on and that was then scanned goes to the code
  reader.
- A capture failure is stored on the receipt with its reason instead of being
  raised; one bad receipt no longer aborts a batch.

Fixed
~~~~~

- Receipt times were the printed local time stored as UTC: shown one or two
  hours off, and the document date right only by accident. Stored in UTC now,
  with the date on the paper used for documents. The 19.0.1.1.0 migration
  converts rows a provider wrote and leaves hand-typed ones alone.
- Review reasons and overrides rendered as escaped ``<ul><li>`` in the chatter.
- A duplicate receipt surfaced as a database error; it is now refused by name.
  The local holding the identifier is no longer called ``uid``, which Odoo 19's
  ``_()`` reads from the caller's frame when the environment has no language.
- A receipt without an issue date produced a vendor bill without a date.
- With no rate map, the tax for a rate was the first purchase tax at that
  percentage by id — on a stock SK chart possibly the EU, reverse-charge or
  customs one. The company's default purchase tax wins at its own rate, and
  taxes that net their VAT out are skipped.
- A fiscal code whose reader is archived was listed as "not a receipt
  verification code", the wording meant for a loyalty link. It now names the
  archived reader.
- **On Community nobody but an administrator could see a receipt.** Access
  and the *Fiscal Receipts* menu were tied to "Show Full Accounting Features"
  and the *Accounting* menu, which Community grants nobody by default. Both
  now follow the Invoicing group, and the menu sits under *Vendors* beside
  the bills it produces.
- The footer's *Amount Total* was an editable monetary input in the big-total
  style, which drew the € over the digits ("181€90"). The footer now only
  shows the totals; the total is edited as *Total* in the Receipt section.

Added
~~~~~

- **Employees read their own receipts.** Every internal user may read — not
  change — the receipts they captured, with their items, VAT recap and
  attempts; Invoicing users see and work on all of them. The buttons that
  change a receipt are shown to Invoicing only.

[19.0.1.0.0] — 2026-10-06
-------------------------

Added
~~~~~

- ``cssk.receipt`` (``mail.thread``), ``cssk.receipt.line`` and
  ``cssk.receipt.tax``: a captured cash-register receipt with its items and the
  seller's own per-rate VAT recap.
- ``cssk.receipt.provider`` registry plus ``cssk.receipt.provider.mixin``, the
  contract a capture provider implements (``_can_capture`` / ``_capture``).
- Reconciliation gates: the items must sum to the total and every VAT bucket must
  match the items at its rate, or the receipt is parked in *Needs Review* with
  the discrepancy named.
- Vendor-receipt sink (``account.move`` of type ``in_receipt``), in two shapes —
  one line per VAT rate (default) or one per item — with the created document
  verified back against the receipt's own totals and VAT.
- Seller resolution on VAT (compared normalized), then IČO, then tax number;
  never on name. A created partner takes only the seller's registered identity,
  never the premises where the receipt was issued.
- Company settings: receipt journal, default expense account, document detail,
  auto-create seller. The VAT-rate → tax map is borrowed from
  ``account_invoice_ai_extract`` when installed.

- Hardening from an adversarial review of the money logic (GPT-5.3-Codex,
  2026-10-06):

  - every VAT bucket's own arithmetic is checked (``base + tax`` grossed up at
    the stated rate must give back that base and tax), so a recap that shifts
    value between base and tax no longer passes merely because it foots against
    the items;
  - the rate a tax is mapped to is verified against the tax's own percentage at
    construction time — two buckets with equal bases and swapped taxes post
    exactly the amounts the receipt reports, so no aggregate check can see it;
  - a receipt carrying an item marked as a return or correction is parked for
    review rather than posted, since the sign convention is undocumented and an
    unsigned negative item reconciles perfectly while pointing the money the
    wrong way;
  - the posted document's VAT is also verified per rate, not only in total;
  - a tax-included purchase tax is refused on the vendor-bill path with the
    reason named, instead of failing the totals check with an unactionable
    number;
  - monetary sums are rounded to the receipt's currency before every comparison,
    so float drift cannot decide a gate;
  - the normalized partner search whitelists the column it interpolates into
    SQL, and matches a tax number only as an exact value or behind a two-letter
    country prefix — the previous suffix match could pick a longer number
    ending the same way.
