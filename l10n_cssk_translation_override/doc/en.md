---
title: CZ/SK Translation Overrides
summary: Slovak and Czech wording for Odoo and OCA screens where their own translation is missing, wrong or inconsistent with Czech/Slovak accounting terminology.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

Odoo and the OCA modules ship their own Slovak and Czech translations. Some
terms are missing and show in English, some are literal translations of the
English that no Czech or Slovak accountant would use, and the same concept is
sometimes translated three different ways on three screens. This module
carries our corrections, so that the whole interface reads in one consistent
language, without changing Odoo's or OCA's own files.

It needs nothing but `base` and is useful on Community and Enterprise alike.
Corrections for a module you do not have installed are simply skipped.

## What it changes {#scope}

- **Field labels, help texts, selection values, menus, actions and view
  texts** of other modules. These are written into the database and are what
  you see on every form and list.
- **Messages produced in code** — error and warning messages, notifications,
  labels built in Python or in the web client. These are served from the
  module's catalogues directly.

## When the corrections apply {#when}

Automatically, every time Odoo loads translations:

- when this module is installed or upgraded;
- when **any** module is installed or upgraded afterwards, including the
  modules being corrected;
- when you add or update a language in *Settings ▸ Languages*, also with
  *Overwrite Existing Terms* ticked.

Messages produced in code change after the Odoo server is restarted.

## Things to know {#notes}

- A translation you changed yourself in the interface is **replaced** by our
  correction the next time translations are loaded, where we carry one for
  that term. Records Odoo marks as yours to edit (e-mail templates and similar
  data loaded once) are never touched.
- Uninstalling the module leaves the corrected wording in place. To return to
  Odoo's own wording, reload the language in *Settings ▸ Languages* with
  *Overwrite Existing Terms*.
- The code-message corrections apply to the whole Odoo server, i.e. to every
  database on it, once the module is installed in one of them.
- Records Odoo names from a code message when it creates them — warehouse
  operation types such as *Receipts*, routes, code-created journals, POS
  payment methods — get their Slovak or Czech name too, also on a database
  set up in English. A name you translated or changed yourself is kept.
- Account, tax and journal names come from the chart of accounts and belong
  to each company; they are not changed by this module.
