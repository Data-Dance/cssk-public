=========
Changelog
=========

All notable changes to **account_payment_mode_pay_on_post** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-09-28
-------------------------

Added
~~~~~

- *Register payment on validation* on a payment mode with a fixed journal:
  posting an invoice in that mode registers its full payment in the journal,
  dated the invoice date, through the core payment wizard. For cash and card
  sales paid on the spot.
