==========================================
CZ Supplier Reliability — ADIS provider
==========================================

Implements the Czech country provider for ``l10n_cssk_payment_reliability``.
It queries the Czech Financial Administration ADIS SOAP web service
(``rozhraniCRPDPH``) to determine whether a supplier is an unreliable VAT
payer (nespolehlivý plátce) and to retrieve the supplier's registered
(published) bank accounts (zveřejněné účty). No API key is required — the
service is open.

Features
========

* Calls the published ADIS endpoint
  ``adisrws.mfcr.cz/.../rozhraniCRPDPH.rozhraniCRPDPHSOAP``, operation
  ``getStatusNespolehlivyPlatce``.
* Tax reliability mapping: ``nespolehlivyPlatce`` ANO → unreliable, NE →
  reliable, NENALEZEN → unknown. A NENALEZEN subject is not a VAT payer, so
  its bank account is reported unavailable rather than unregistered.
* Registered bank accounts: ``standardníÚčet`` (předčíslí/číslo/kódBanky) is
  converted to its IBAN so it matches the bank account on the bill;
  ``nestandardníÚčet`` (already an IBAN) is taken as-is. An account entered on
  the bill in the domestic form (``19-2000145399/0800``) is converted the same
  way before comparing.
* Gracefully returns no result on network or parsing errors, leaving the
  supplier status unknown.

Usage
=====

Install alongside ``l10n_cssk_payment_reliability``. For partners with the
country set to Czech Republic (CZ) and a VAT/DIČ filled in, the shared
reliability check automatically routes to this ADIS provider. No
configuration or API key is needed.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
