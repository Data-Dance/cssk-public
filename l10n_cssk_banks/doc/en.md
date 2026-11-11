---
title: CZ/SK Banks
summary: Every Czech and Slovak bank code with its BIC, taken from the ČNB and NBS registries, so an IBAN fills in its bank by itself.
verified: 19.0.2.0.0
---

## What it does {#purpose}

Adds the banks of the two official bank-code registries as **Banks**
(*Contacts → Configuration → Banks*):

- **Czech Republic** — Česká národní banka, *Číselník kódů bank*;
- **Slovakia** — Národná banka Slovenska, *Prevodník identifikačných kódov pre
  tuzemský platobný styk*.

Each bank carries its four-digit **bank code**, its **BIC** where the registry
has one, and its country. Names are written as the registry publishes them,
untranslated.

Together with OCA's *Bank from IBAN*, which it installs, entering a Czech or
Slovak IBAN on a bank account picks the bank by itself: `SK05 1100 …` is Tatra
banka, `CZ65 0800 …` is Česká spořitelna.

It installs itself together with *Bank from IBAN* and has no settings.

## Banks that change or disappear {#updates}

The registries change a few times a year. A new version of this module brings
the current lists, and when it is installed:

- a bank's **name, code, BIC and country** follow the registry — a corrected BIC
  replaces a wrong one;
- a bank whose code **left the registry is archived, never deleted**. Bank
  accounts that use it keep it; it is just no longer offered for new ones;
- **address, phone and e-mail** are yours: neither registry publishes them, so
  they are never overwritten;
- a bank you had already created by hand with the same code and country is
  **taken over** rather than duplicated.

If you need a bank to read differently from the registry, create your own bank
record rather than editing the shipped one.

## Coming from the earlier module {#migration}

This module replaces *Information about banks in Czech Republic and Slovakia*
(`l10n_banks_cz_sk`). Your administrator renames it in the database before
upgrading; the bank accounts keep their banks, and the contact details the old
module shipped are removed where you had not changed them.
