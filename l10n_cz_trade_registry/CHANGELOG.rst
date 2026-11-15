=========
Changelog
=========

All notable changes to **l10n_cz_trade_registry** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-11-15
-------------------------

Added
~~~~~

- Register coordinates on ``res.partner`` — **Rejstřík**, **Rejstříkový
  soud**, **Spisová značka** (oddíl and vložka) — mirrored onto
  ``res.company``, and the statement **§ 435 občanského zákoníku** requires on
  business documents composed from them: *Obchodní rejstřík vedený Městským
  soudem v Praze, oddíl C, vložka 12345*. It is kept in step with
  ``l10n_cz``'s ``res.company.trade_registry``, which is what the invoice
  prints; wording typed by hand is never overwritten, and clearing the
  coordinates clears the statement the module wrote. The register's status,
  the dates of establishment and dissolution, the entry's předmět podnikání
  and činnosti and previous names and seats are stored on the contact, with a
  banner, a *Neaktivní subjekty (CZ)* list and a non-blocking warning on
  invoices and bills for a partner the register shows as zaniklý, historický
  or pozastavený. Filled by hand or from ARES by
  ``partner_autocomplete_ares_cz`` 19.0.1.4.0.
