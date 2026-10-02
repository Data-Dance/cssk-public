=========================
CZ VAT Status — Sales
=========================

.. |badge1| image:: https://raster.shields.io/badge/license-AGPL--3-blue.png
    :alt: License: AGPL-3

|badge1|

Bridge between ``l10n_cz_vat_status`` and ``sale``, installed automatically
when both are.

A sales order line proposes the taxes the company's VAT status allows on the
**order date**: while the company is a neplátce or an identifikovaná osoba, a
domestic sale carries no VAT. An order is not a tax document, so this is only a
proposal — the invoice made from it takes the status on its own DUZP, and
``l10n_cz_vat_status`` refuses to post it with taxes that do not fit.

A company with no VAT-status history is not affected.

Author
======

* Data Dance s.r.o.
