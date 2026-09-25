============================================
CZ EC Sales List (Souhrnné hlášení / DPHSHV)
============================================

The Czech country layer for the shared EC-summary framework
(``l10n_cssk_ec_summary_base``). It aggregates intra-EU supplies per member
state, customer VAT number and transaction code — with the mandatory VIES
preflight inherited from the base — and exports the Czech EPO
**Pisemnost / DPHSHV** XML.

Features
========

* Aggregates intra-EU supplies per (member state, customer VAT, transaction
  code), reusing the shared EC-summary statement, lines and the mandatory VIES
  VAT-number validation from ``l10n_cssk_ec_summary_base``.
* Reads transaction codes from ``account.tax.cssk_ec_summary_code``
  (``0`` = goods, ``1`` = triangular trade, ``2`` = services …).
* Exports the EPO Pisemnost / DPHSHV XML: one ``VetaD`` header, one ``VetaP``
  declarant block and one ``VetaR`` per reported partner line.
* Ships the statutory statement version (2025) with the regular / corrective /
  subsequent statement types (Řádné / Opravné / Následné).
* The export is validated against the official EPO **DPHSHV** XSD
  (``data/dphshv_epo2.xsd``), loaded onto the statement version record.

Usage
=====

Install the module on a Czech company, then open the shared EC summary
statement provided by ``l10n_cssk_ec_summary_base``, pick the Czech version and
period, compute the lines and export the EPO Pisemnost / DPHSHV XML. The export
relies on ``account.tax.cssk_ec_summary_code`` to classify each supply, so make
sure the intra-EU sales taxes carry the correct transaction code and that the
company has a competent tax office set.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
</content>
</invoke>
