=====================
Account Debit Note DD
=====================

Data Dance refinements on top of Odoo's core ``account_debit_note``. It tidies up
the customer debit-note (vrubopis / opravný daňový doklad zvyšující základ) user
experience and labels the printed document correctly.

This is a thin UI/report layer — it does not change how debit notes are posted or
numbered; it only adjusts the form, the menu action and the invoice report.

Features
========

* The printed invoice document is titled **Debit Note** (draft / cancelled
  variants included) whenever a posted customer invoice carries a
  ``debit_origin_id``.
* The standard **Reverse** button is hidden on the invoice form (debit notes are
  created through the dedicated debit-note flow, not via reversal).
* The customer *Credit Notes* action is widened to also list documents that have
  a ``debit_origin_id``, so debit notes are reachable from the same place.

Usage
=====

Install on top of ``account_debit_note``. Create a debit note from a posted
customer invoice using Odoo's standard *Add Debit Note* flow; the resulting
document prints with the **Debit Note** title and appears alongside credit notes
in the customer list.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
