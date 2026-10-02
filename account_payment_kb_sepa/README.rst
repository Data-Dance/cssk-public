============================
KB XML SEPA Credit Transfer
============================

Komerční banka's XML format for foreign payments is ISO 20022
**pain.001.001.03** SEPA Credit Transfer — *Klientský formát XML SEPA CT v KB*.
OCA ``account_banking_sepa_credit_transfer`` (vendored, see ``PORTED-OCA.md``)
already generates it: TRF, service level SEPA, charges SLEV, EUR, validated
against the official XSD. This module only adapts that output to what KB's
specification documents, and only for orders paid **from a KB account**
(bank code ``0100``) in the pain.001.001.03 flavour. Every other bank's
orders are left exactly as OCA writes them.

What changes for KB
===================

* **Structured postal address.** OCA writes pain.001.001.03 addresses as
  ``Ctry`` plus free ``AdrLine`` lines. KB's list of accepted tags for the
  debtor and the creditor is ``StrtNm``, ``BldgNb``, ``PstCd``, ``TwnNm``,
  ``CtrySubDvsn``, ``Ctry`` — no ``AdrLine`` — and "pokud klient zadá
  jakýkoliv prvek adresy, musí zadat minimálně Město a Zemi". The address is
  therefore written structured, and omitted altogether when the partner lacks
  a town or a country (for SEPA the address is optional). With
  ``base_address_extended`` the street name and number go to ``StrtNm`` and
  ``BldgNb``.
* **SWIFT character set.** KB accepts SEPA data "výhradně bez diakritiky";
  OCA converts to ASCII only when the payment method's *Convert to ASCII* is
  ticked. For a KB order it always does.

Scope
=====

KB's XML is **SEPA only** (EUR, into SEPA-reachable or unreachable banks).
Foreign payments in other currencies, or with OUR/BEN charges, go through
KB's BEST format — ``account_payment_kb_best``, method *KB BEST (foreign /
SEPA transfer)*.

Not handled here: KB's rule that identifications and references must not start
or end with ``/`` nor contain ``//`` (EPC slash rule). OCA's EndToEndId is an
internal record number, which satisfies it; a remittance text the user types is
passed through.

Specification
=============

Komerční banka — *Klientský formát XML SEPA CT v KB* (valid from
20 June 2026), fetched 2026-09-28:
https://mojebanka.kb.cz/file/cs/KB-podminky_format_XML.pdf

Credits
=======

Author: Data Dance s.r.o. — https://www.datadance.eu
