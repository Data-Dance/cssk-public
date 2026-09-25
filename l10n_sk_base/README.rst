============================
Slovakia Base Localization
============================

.. |badge1| image:: https://raster.shields.io/badge/license-AGPL--3-blue.png
    :alt: License: AGPL-3

|badge1|

| The Slovak **DIČ** — the income-tax identifier.

**Table of contents**

.. contents::
   :local:


Why a field of its own
======================

Slovakia issues **three** identifiers where most countries manage with two:

==============  ==========================  ====================================
Identifier      Odoo field                  What it is
==============  ==========================  ====================================
**IČO**         ``company_registry``        Company registry number
**DIČ**         ``l10n_sk_dic``             Income-tax identifier, ten digits
**IČ DPH**      ``vat``                     VAT number, ``SK`` + the DIČ
==============  ==========================  ====================================

A subject can hold a **DIČ and no IČ DPH at all** — anyone registered for
income tax who is not a VAT payer. That is the case ``vat`` cannot express, and
the reason this field exists.

A Slovak invoice consequently carries two identifier lines, and they hold
different numbers::

    IČ DPH:  SK2023318462     ← core, from ``vat``
    DIČ:     2023318462       ← ``l10n_sk_invoice``, from this field


Czech Republic needs no such field
==================================

In Czech usage **DIČ is the VAT number** (``CZ`` + IČO), so ``vat`` already
holds it and Odoo already labels it correctly: ``res.country`` for Czechia
carries ``vat_label = {"cs_CZ": "DIČ", "en_US": "VAT"}``, which
``account.report_invoice_document`` prints.

This is not a hypothetical. The field previously lived in ``l10n_cssk_core``,
the shared CZ/SK base, and ``l10n_cz_invoice`` printed a second DIČ line from
it — the same identifier twice, disguised only by the second copy lacking its
country prefix. That line is gone.


Migrating from ``l10n_cssk_core``
=================================

Installing this module carries existing ``l10n_cssk_dic`` values over
automatically. The carry-over runs in ``post_init_hook`` rather than as a
migration script, because a migration in a brand-new module never fires;
removing a field does not drop its column, so the old values are still there on
arrival. Only rows where the new field is empty are filled, so a value entered
after the upgrade wins. The old column is left untouched.

Consumers repointed at the same time: ``l10n_sk_invoice``, ``l10n_sk_dppo``
(both DPPO XML templates), ``partner_autocomplete_orsf_sk``, and
``l10n_cssk_income_tax_base`` — that last one through ``getattr``, since it is
the shared CZ/SK base and a Czech-only deployment installs it with no Slovak
module.


Filling it from the register
============================

Install ``partner_autocomplete_orsf_sk``: it maps the DIČ from ORSF on every
enrichment, and points its mapping at this field automatically.


Author
======

* Data Dance s.r.o.

Contact
=======
https://www.datadance.eu/
