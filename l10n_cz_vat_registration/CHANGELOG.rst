=========
Changelog
=========

All notable changes to **l10n_cz_vat_registration** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-11-15
-------------------------

Added
~~~~~

- ``res.partner.l10n_cz_vat_registration_category`` — whether the partner's
  DIČ belongs to a plátce (§ 6–6f zákona č. 235/2004 Sb.), a skupina (§ 5a),
  an identifikovaná osoba (§ 6g–6l) or a neplátce — plus
  ``l10n_cz_vat_payer_since`` and a computed ``l10n_cz_is_full_vat_payer``,
  and a non-blocking warning on a customer invoice that applies the domestic
  reverse charge of § 92a to a customer recorded as an identifikovaná osoba
  or a neplátce; the reason is posted to the chatter on posting. A § 92a
  supply is recognised by the tax: the row 25 tag of the Czech VAT return, or
  the § 92a flag of ``l10n_cz_invoice``. The category is entered by hand or
  filled from the Finanční správa register by ``l10n_cz_payment_reliability``
  19.0.1.3.0.
