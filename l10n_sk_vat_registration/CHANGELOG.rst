=========
Changelog
=========

All notable changes to **l10n_sk_vat_registration** are documented here.
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

[19.0.1.0.0] — 2026-09-05
-------------------------

Added
~~~~~

- ``res.partner.l10n_sk_vat_registration_category`` — the paragraph of the SK
  VAT Act the IČ DPH was issued under (§ 4 / § 4b / § 5 / § 6 / § 7 / § 7a) —
  plus ``l10n_sk_vat_payer_since`` and a computed ``l10n_sk_is_full_vat_payer``.
- A non-blocking warning on a customer invoice that applies a § 69 ods. 12
  domestic reverse charge to a § 7 / § 7a customer, who is not a platiteľ and
  to whom that provision therefore cannot apply. The reason is posted to the
  chatter on posting.

Notes
~~~~~

- § 7 / § 7a registrants hold an IČ DPH that **VIES confirms as valid**. The
  distinction this module records is exactly the one VIES cannot make, which is
  why it is worth storing separately.
- An unrecognised ``druhReg`` value yields **False**, never a guess: reading
  "unknown" as "not a platiteľ" (or the reverse) changes how an invoice is
  taxed. Parsing tolerates the non-breaking spaces and tabs the Finančná správa
  values arrive with.
- The reverse-charge check detects ``l10n_sk_invoice``'s ``account.tax.
  l10n_sk_reverse_charge`` flag at runtime instead of depending on the module,
  so this stays a data module and simply stays quiet where the flag is absent.
