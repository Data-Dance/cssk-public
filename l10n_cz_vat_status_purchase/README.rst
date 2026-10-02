=========================
CZ VAT Status — Purchases
=========================

.. |badge1| image:: https://raster.shields.io/badge/license-AGPL--3-blue.png
    :alt: License: AGPL-3

|badge1|

Bridge between ``l10n_cz_vat_status`` and ``purchase``, installed automatically
when both are.

A purchase order line — including one created by procurement — proposes the taxes the company's VAT status allows on the
**order date**: while the company is a neplátce or an identifikovaná osoba,
domestic input VAT is not deductible and goes to the cost. An order is not a tax document, so this is only a
proposal — the vendor bill made from it takes the status on its own DUZP, and
``l10n_cz_vat_status`` refuses to post it with taxes that do not fit.

A company with no VAT-status history is not affected.

Author
======

* Data Dance s.r.o.
