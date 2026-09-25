=========================================
Intrastat in the statutory footprint
=========================================

Adds Intrastat to the reverse drill: a document says which Intrastat
declaration reports it, alongside the VAT return, control statement, EC sales
list and financial-statement rows it feeds.

Why it is a separate module
===========================

``l10n_cssk_intrastat_base`` — the INSTAT renderer — depends on ``base`` alone,
deliberately, so the Community (OCA) and Enterprise adapters can share it. And
neither country adapter depends on ``l10n_cssk_core``, where the footprint hook
lives. The glue therefore belongs in neither and installs itself when both
sides are present.

What it does not do
===================

It does not decide whether a line is Intrastat-reportable. That question is
answered by the declaration's own generation, with the company's thresholds,
exclusions and transaction codes in hand; this reads the link the declaration
already stored. Re-deriving eligibility would be a second reader of that
question, and every contributor to this footprint that parsed rather than read
has drifted from the forward direction at least once.

The consequence is worth knowing: **a period whose declaration has not been
generated reports nothing**. A document is not on an Intrastat declaration
until one exists, and saying otherwise would be predicting an obligation
rather than reporting one.

Community only, for now
=======================

The OCA path (``intrastat_product``) is the only live one — Odoo Enterprise
ships no Slovak Intrastat at all. An Enterprise adapter would need its own
bridge reading ``account.move.line``'s Enterprise-side link.
