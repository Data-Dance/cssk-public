=========
Changelog
=========

All notable changes to **account_reconcile_oca_counter_account** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.0] — 2026-11-04
-------------------------

Fixed
~~~~~

- **The dashboard button read "Párovať 10 Položky".** account_reconcile_oca
  labels it "Reconcile N Items", translated term by term around the number,
  so the noun can never agree with N in Slovak or Czech (položka / položky /
  položiek). It now reads "N to reconcile" as in Odoo Enterprise:
  "10 na párovanie", "10 ke spárování". To be dropped once OCA changes its
  label.
