============================================
SK Localization — Statutory Reference Data
============================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Slovak statutory reference registries: daňové úrady and person types.**

Slovak-specific seed data for the country-neutral registries defined in
``l10n_cssk_core``:

* ``cssk.tax.authority`` — the eight regional daňové úrady plus the Daňový úrad
  pre vybrané daňové subjekty. Unlike CZ (c_ufo numbers), the SK statutory XSDs
  (``dph2025.xsd``, ``svdph20.xsd``) declare ``danovyUrad`` as a free-text
  ``xsd:string`` with no codelist, so ``submission_code`` carries the office name.
* ``cssk.person.type`` — Slovak taxpayer types (FO / PO).

There is no official ``l10n_sk`` tax-office model to seed from, so this list is
curated. The exact ``danovyUrad`` string convention is not constrained by the
schema; verify against a real FS SR submission if your DÚ is strict.

.. rubric:: Module facts

- **Technical name:** ``l10n_sk_statutory``
- **Version:** 18.0.1.0.0
- **Licence:** AGPL-3
- **Requires:** ``l10n_sk``, ``l10n_cssk_core``

Authors: Data Dance s.r.o.
