---
title: EU NACE — Rev. 2.1 and the Czech Subclasses
summary: Imports NACE Rev. 2.1 industries with the CZ-NACE 2025 fifth digit and keeps a contact's Industry in step with its NACE code.
verified: 19.0.1.0.1
family: partner_nace#industries
---

Extends OCA's NACE import (*Contacts → Configuration → Import NACE industries*) with a choice of version — NACE Rev. 2.1 or the former Rev. 2 — and the 716 Czech national subclasses of CZ-NACE 2025, and keeps each industry's version and code. A contact's **Industry** then follows its NACE code, and picking a NACE industry fills the code.

It installs itself when both OCA's `l10n_eu_nace` and the partner NACE code module are installed, and has no settings of its own beyond the options of the import wizard.
