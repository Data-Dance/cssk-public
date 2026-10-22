=========
Changelog
=========

All notable changes to **l10n_sk_fs** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.2] — 2026-07-04
-------------------------

Added
~~~~~

- Poznámky (Úč PODV 3-01) generated as **PDF v1**: new ``l10n.sk.poznamky`` model + QWeb report, with depreciation figures auto-populated. No structured Poznámky XSD exists, so the PDF is the definitive artefact.
- Cash-flow and statement-of-changes-in-equity datasets alongside Súvaha + VZS.

Changed
~~~~~~~

- Evaluator performance (Wave 3): Súvaha compute uses ``_read_group`` balance helpers (~600 queries → 2); form-load reconcile reduced from N-per-line to ≤3 queries.
- Export pipeline consolidated into the shared ``cssk.statutory.submission.mixin``.

[2026-07-01] — Wave 1 (P0 correctness)
--------------------------------------

Fixed
~~~~~

- Multi-company leak closed with an ``ir.rule [('company_id','in',company_ids)]``.

Changed
~~~~~~~

- Statutory rounding unified on ``statutory_round()`` (HALF-UP).

[2026-06-30] — Initial baseline
-------------------------------

Added
~~~~~

- Slovak Súvaha + Výkaz ziskov a strát (druhové členenie) on ``l10n_cssk_fs_base``, computed CE-clean (no ``account_reports``): full statutory line partition, so SPOLU MAJETOK = SPOLU VLASTNÉ IMANIE A ZÁVÄZKY and VH = výnosy − náklady; current-year result (A.V) computed from triedy 5/6.
- Official **UZPODv14** export (``l10n.sk.uzpod``): combined Súvaha Úč POD 1 (r001–r145, Brutto/Korekcia/Netto) + Výkaz ziskov a strát Úč POD 2 (r01–r61), validated against ``data/uzpod-2014.xsd``.
- sk_SK translations (Odoo 19 jsonb) as part of the localization i18n sweep.
