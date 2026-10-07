=========
Changelog
=========

All notable changes to **l10n_cssk_receipt_capture** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

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
