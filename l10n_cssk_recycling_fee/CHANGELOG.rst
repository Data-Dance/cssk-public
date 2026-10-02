=========
Changelog
=========

All notable changes to **l10n_cssk_recycling_fee** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-09-28
-------------------------

Added
~~~~~

- Dated CZ/SK recycling-fee rates on OCA ``account_ecotax`` classifications,
  with a scheme country and currency; overlapping rates are refused.
- The fee priced per invoice line at the invoice date, per piece in the
  product's unit of measure or per kg of product weight, converted for a
  foreign-currency invoice; frozen once posted.
- The per-line statement required by § 73 odst. 1 zákona č. 542/2020 Sb. (MŽP
  guideline of 26. 10. 2021) and § 34 ods. 1 písm. d) zákona č. 79/2015 Z. z.:
  "z toho recyklační příspěvek …" / "z toho recyklačný poplatok …", and the
  document total "… celkem / spolu bez DPH".
- Portable-battery fees are never printed (CZ § 85 odst. 3, SK § 46 ods. 2,
  § 48 ods. 1 písm. d)) but are priced and reported.
- Included / on-top presentation setting.
- Recycling Fees report (pivot, list, graph) and its XLSX export, per country,
  category and period.
- EEE categories 1–6 and the five battery categories as ecotax categories.
