---
title: Partner NACE Code
summary: The partner's main economic activity as its NACE code — filled from the business register and filed on the Czech and Slovak statutory forms.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

Several statutory forms ask for the company's main economic activity as a code
of the NACE classification, and the business registers publish the same code
for every company. This module gives contacts one field for it, **NACE (main
activity)**, in every country.

The national classifications are the EU's NACE with national digits added, and a
partner has one country, so the country tells which variant the code is in:

| Country | Classification | Code |
|---|---|---|
| Czech Republic | CZ-NACE 2025 — NACE Rev. 2.1 with a fifth, national digit | up to 5 digits |
| Slovakia | NACE Rev. 2.1 (4 digits) as published by the register, or the five-digit SK NACE | 4 or 5 digits |

Only the code is kept, as digits: `62100`, not `62.10.0`. For a readable,
hierarchical industry, see [below](#industries).

## Entering the code {#usage}

The field sits under **Industry** on the contact form, on companies only.

- Type it with or without dots and spaces — `62.10`, `62 10 0` — it is stored as
  digits. Two to six digits are accepted; anything else is refused on save.
- Contacts inside a company share the company's code, like its VAT number, and
  cannot change it there.
- Your own company's code is set on the contact behind the company (open the
  company's contact in *Contacts*).

The partner-autocomplete providers fill it from the register:

- [module:partner_autocomplete_ares_cz](module:partner_autocomplete_ares_cz) —
  the **prevailing** activity in CZ-NACE 2025 from ARES's copy of the
  statistical register;
- [module:partner_autocomplete_orsf_sk](module:partner_autocomplete_orsf_sk) —
  the NACE the Slovak register publishes for the subject.

Both point their mapping at this field automatically when it exists.

## Where it is used {#output}

Your company's code is filed on:

- the Czech VAT return DPHDP3 (field `c_okec`) by
  [module:l10n_cz_vat_return](module:l10n_cz_vat_return);
- the Czech corporate income tax return DPPO (field `c_nace`) by
  [module:l10n_cz_dppo](module:l10n_cz_dppo);
- the Slovak financial statements (header `SK NACE`) by
  [module:l10n_sk_fs](module:l10n_sk_fs), which pads a shorter code with zeros
  to five digits.

Check that the code is in the classification the form expects for the period you
file.

## Readable industries (EU NACE) {#industries}

Odoo's **Industry** field on a contact is a readable label from a list of
industries. OCA's [module:l10n_eu_nace](module:l10n_eu_nace) fills that list
with the NACE classification from the EU vocabulary service, in every installed
language it is published in.
[module:l10n_eu_nace_cssk](module:l10n_eu_nace_cssk), which installs itself when
both modules are present, links the list to the code:

- **Import by version.** *Contacts → Configuration → Import NACE industries*
  asks which version to import: **NACE Rev. 2.1** (default) or the former
  **NACE Rev. 2**. The two reuse codes with different meanings, so each industry
  remembers its version and its code; the industry list shows both columns.
- **Czech subclasses.** With Rev. 2.1, *Czech subclasses (CZ-NACE 2025)* adds
  the national fifth digit — 716 subclasses, from the Czech Statistical Office's
  codelist — under their classes, named in English and Czech.
- **One classification at a time.** *Archive the other version* (on by default)
  archives the industries of the other version, so the list offers one.
  Partners keep the industry they have.
- **Code → industry.** Saving a NACE code sets the contact's **Industry** to the
  matching one: the code itself, otherwise its four-digit class, Rev. 2.1 first,
  then Rev. 2. A **five-digit code of a Slovak contact** is SK NACE Rev. 2 —
  Slovakia's Rev. 2.1 has no fifth digit — so it is matched in Rev. 2 only,
  even when that version is archived: the same four digits can mean another
  activity in Rev. 2.1. A national subclass matches only contacts of its own
  country. An industry you picked that is not a NACE industry is left alone.
- **Industry → code.** Picking a NACE industry on the form fills the code.

Industries imported before this module was installed are tagged as NACE Rev. 2,
the only version OCA's import could fetch.

## Limitations {#limitations}

- The field holds one code, the main activity. Secondary activities are not
  kept; for the Slovak register's predmety podnikania see
  [module:l10n_sk_trade_registry](module:l10n_sk_trade_registry).
- Nothing checks that a code exists in the classification, only that it is 2 to
  6 digits.
- A **four-digit** code of a Slovak contact is taken as Rev. 2.1, the version
  the Slovak register publishes from 2026. An older four-digit Rev. 2 code
  typed in by hand gets the Rev. 2.1 industry; check it. A contact with no
  country is matched like a Czech one.
