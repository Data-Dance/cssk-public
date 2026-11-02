=========
Changelog
=========

All notable changes to **l10n_sk_ubl_bis3** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[18.0.3.2.0] — 2026-10-24
-------------------------

Brought to 19.0's 3.2.0 from 18.0.1.0.1 in one step. 19.0 documented only the
last of it, so what the port carries is written out here.

Fixed
~~~~~

- **A Slovak partner was published under the wrong Peppol identifier.** Core
  maps Slovakia to ``{'9950': 'vat', '0245': 'company_registry'}`` and walks
  it in dict order, so a VAT payer was identified as ``9950:SK2020317068``;
  and the fallback ``0245`` was filled from ``company_registry`` — the
  eight-digit **IČO** — under a code whose own label reads "SK Tax
  identification number (DIČ)". The Slovak participant identifier is
  ``0245:<DIČ>``. An access point answers an unknown participant with a
  *validation* error, so the wrong scheme reads as a malformed payload and
  costs an hour before anyone suspects the identifier.

  Done by overriding ``_compute_peppol_eas`` and ``_get_peppol_endpoint_value``
  rather than by re-ordering ``EAS_MAPPING['SK']``: that dict is a
  module-global imported once per PROCESS, so mutating it would reach every
  database the worker serves, including ones where this module is not
  installed. A scheme somebody chose deliberately is preserved — eligibility
  is taken before ``super()`` with exactly core's own test.

- **A company created with its DIČ in one save landed on 9950** (the company
  form; cssk-public#5, 19.0's 3.2.0). Core builds the company's partner from a
  fixed set of values that never includes the DIČ and flushes it, so
  ``peppol_eas`` is computed before the related ``l10n_sk_dic`` writes
  through: ``9950:<IČ DPH>`` for a VAT payer, ``9950`` with **no endpoint at
  all** for a non-payer — an invoice the export constraint lets through (a DIČ
  *is* recorded) and that Peppol rejects (R020, BR-06, BR-CO-26).
  ``res.company.create`` now runs the adoption on the partners core created,
  using core's own condition for creating one; a ``partner_id`` passed in
  keeps its scheme.

- **The DIČ is never derived from the VAT number.** An earlier version took
  ``vat`` minus its ``SK`` prefix. The ePošťák sandbox firms disprove the
  premise — a synthetic IČ DPH stands in for a DIČ that fails ``base_vat``'s
  checksum, so deriving gives ``4536197523`` where the participant is
  ``4536197514`` — and a wrong participant identifier registers the company as
  somebody else. No stored DIČ, no ``0245`` endpoint.

- **The export refuses a Slovak party with no DIČ**, named, instead of letting
  it go out under the IČ DPH — wrong but perfectly well formed, so nothing
  would have complained. Gated on the missing number, not on the scheme: with
  no DIČ the partner never leaves core's ``9950``, which a scheme-gated check
  sailed past (on one real agenda, 1076 of 1204 DIČ-less Slovak partners).

- The ``ubl_bis3_sk`` sequence is 150, below core's ``ubl_bis3`` (200). SK is
  absent from ``PEPPOL_DEFAULT_COUNTRIES`` on this series too, so SK has only
  one entry today; equal sequences would break the tie on dict order once that
  changes and silently drop the VS → BT-83 mapping.

Added
~~~~~

- *Peppol: use 0245 + DIČ* in the contacts' Action menu (Accounting
  administrators): ``action_l10n_sk_adopt_dic_participant`` is re-runnable by
  design and was reachable only from code. It is how partners already on
  ``9950`` are fixed — the migration runs at upgrade, **before** anyone has
  recorded the DIČs it needs, and nothing re-fires afterwards.
- Migration ``18.0.2.0.0``: the same adoption over every Slovak partner not
  already on ``0245``.

18.0 deltas
~~~~~~~~~~~

- ``_get_peppol_endpoint_value`` takes ``(country_code, field)`` here; 19.0
  added an ``eas`` argument and the override keys on it, because
  ``EAS_MAPPING['SK']['0245']`` reads ``company_registry`` upstream and the
  field name that arrives is the wrong one by definition. The pair
  (country, field) stands in exactly: ``company_registry`` is the field of
  ``0245`` and of no other SK code. Core special-cases BE the same way.
- ``sanitize_peppol_endpoint()`` does not exist on 18.0 — there is no per-EAS
  sanitiser, and ``_build_error_peppol_endpoint`` carries no rule for
  ``0245`` — so the recorded DIČ is returned as stored; ``l10n_sk_base``
  validates it as ten digits.
- ``ir.actions.server`` names its groups field ``groups_id`` here (19.0:
  ``group_ids``).
- The migration directory is ``18.0.2.0.0``, not 19.0's number: a
  19.0-numbered directory is in the future for an 18.0 manifest and
  ``MigrationManager`` skips it without a word.
- Everything else matched: ``EAS_MAPPING['SK']`` is identical on both series
  (``0245`` included), ``0245`` is in core's ``peppol_eas`` selection, and
  ``res.company.create``'s partner-creation condition is the same line.

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
