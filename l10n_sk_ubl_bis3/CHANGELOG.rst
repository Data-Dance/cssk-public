=========
Changelog
=========

All notable changes to **l10n_sk_ubl_bis3** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[18.0.1.0.1] — 2026-07-18
-------------------------

Changed
~~~~~~~

- ``cbc:PaymentID`` (BT-83) now prefers the canonical
  ``l10n_cssk_variable_symbol`` when ``l10n_cssk_payment_symbols`` is
  installed, falling back to the previous payment_reference/name digits.

[19.0.1.0.0] - 2026-06-16
-------------------------

Added
~~~~~

- Initial release. Registers the Peppol BIS Billing 3.0 format for Slovakia
  (``ubl_bis3_sk``), since ``SK`` is absent from Odoo core's
  ``PEPPOL_DEFAULT_COUNTRIES`` and is therefore not auto-suggested otherwise.
- ``account.edi.xml.ubl_sk`` builder (thin subclass of ``account.edi.xml.ubl_bis3``)
  as a stable extension point. No CustomizationID deviation — Slovakia has no
  national billing CIUS.
- Slovak *variabilný symbol* (VS) mapped onto ``cac:PaymentMeans/cbc:PaymentID``
  (BT-83).
- Auto-default of ``invoice_edi_format`` for Slovak partners.
- Tests covering format registration, builder mapping, auto-suggestion, and
  export content (CustomizationID, IČ DPH, IBAN, VS).
