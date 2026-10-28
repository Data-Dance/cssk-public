====================================================
ISDOC — Local Reverse Charge (KH commodity codes)
====================================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :alt: License: AGPL-3

|badge1|

Bridge between ``account_edi_isdoc`` and ``l10n_cz_kh``, installed
automatically when both are present.

A Czech customer invoice or credit note line in the domestic reverse charge
(§ 92a ZDPH) — recognised exactly as the control statement recognises an
A.1 supply — is exported to ISDOC 6.0.2 with:

* ``ClassifiedTaxCategory/LocalReverseCharge/LocalReverseChargeCode``: the
  KH commodity code (``l10n_cz_kh``'s ``_cz_kh_commodity_code``: product
  first, then a reverse-charge tax), written in the control statement's code
  list;
* ``VATApplicable`` true on the line and on the document;
* a separate ``TaxSubTotal`` with ``LocalReverseChargeFlag`` true.

Rate and tax stay 0 (§ 29 odst. 3 písm. e) bod 2 ZDPH). A reverse-charge
line without a commodity code is an export constraint error.

User documentation: ``static/description/index.html`` (also in Czech and
Slovak).

Credits
=======

* Data Dance s.r.o. — https://www.datadance.eu
