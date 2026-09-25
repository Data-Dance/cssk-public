==================================================
Slovakia - Peppol BIS Billing 3.0 (eFaktúra)
==================================================

Enables Peppol BIS Billing 3.0 (UBL 2.1 / EN 16931) e-invoice export for
Slovak companies, ahead of the mandatory Slovak e-invoicing regime
(domestic B2B from 1 January 2027).

Why this module is thin
=======================

Slovakia has **no national billing CIUS**. The mandated invoice is unmodified
Peppol BIS Billing 3.0, which Odoo's ``account.edi.xml.ubl_bis3`` already
produces correctly for a Slovak company. This module only fills the gaps:

* **Format registration.** ``SK`` is missing from Odoo core's
  ``PEPPOL_DEFAULT_COUNTRIES``, so the generic Peppol format is not offered or
  auto-suggested for Slovak partners. This module registers ``ubl_bis3_sk`` for
  ``SK`` and makes it the default ``invoice_edi_format`` for Slovak partners.
* **Extension point.** ``account.edi.xml.ubl_sk`` subclasses the generic Peppol
  builder, giving a stable place to add Slovak-specific behaviour later.
* **Variabilný symbol (VS).** Mapped onto ``cac:PaymentMeans/cbc:PaymentID``
  (BT-83): the explicit payment reference if set, otherwise the numeric tail of
  the invoice number.

Out of scope
============

The Slovak **Tax Data Document** (TDD, ``urn:peppol:taxdata:sk-1``) and the
5-corner CTC reporting to Finančná správa are the responsibility of a certified
Peppol Access Point, not the ERP.

Configuration
=============

Slovak partners get ``invoice_edi_format = "Slovakia (Peppol BIS 3.0)"``
automatically. Ensure the company has a valid IČ DPH (VAT) and a Slovak IBAN on
the relevant bank account.

Documentation
=============

* ``CHANGELOG.md`` — release history.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
