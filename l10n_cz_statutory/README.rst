============================================
CZ Localization — Statutory Reference Data
============================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Czech statutory reference registries: finanční úřady (seeded from the official l10n_cz.tax_office codelist) and person types.**

Czech-specific seed data for the country-neutral registries defined in
``l10n_cssk_core``:

* ``cssk.tax.authority`` — the regional finanční úřady. Their **c_ufo codes** are
  seeded from the official ``l10n_cz.tax_office`` codelist (single source of
  truth), with curated Czech office names; plus the Specializovaný finanční úřad.
* ``cssk.person.type`` — Czech taxpayer types (FO / PO).

This keeps CZ-specific data out of the shared ``l10n_cssk_core`` so it never
loads on a Slovak database.

.. rubric:: Module facts

- **Technical name:** ``l10n_cz_statutory``
- **Version:** 18.0.1.3.0
- **Licence:** AGPL-3
- **Requires:** ``l10n_cz``, ``l10n_cssk_core``, ``partner_nace``

Authors: Data Dance s.r.o.
