==================================
CZ/SK Payment Symbols (VS/KS/SS)
==================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Variable, constant and specific payment symbols on invoices, credit notes and bank statement lines.**

Canonical home of the Czech/Slovak payment symbols. Depends on Odoo core
``account`` only, so it installs standalone on Community and Enterprise.

* ``account.move``: ``l10n_cssk_variable_symbol`` (computed — digits of the
  document number, capped at 10; credit notes follow a company policy: own
  number or the original invoice's symbol), ``l10n_cssk_constant_symbol``
  (company default on customer documents) and ``l10n_cssk_specific_symbol``,
  all validated digits-only (10/4/10).
* Optional company toggle: use the variable symbol as the invoice's
  ``payment_reference`` on posting — core QR codes, UBL payment IDs and bank
  matching then carry the VS with no further glue.
* ``account.bank.statement.line``: ``variable_symbol`` / ``constant_symbol``
  / ``specific_symbol``, extracted on create from explicit values, the bank
  connector's ``transaction_details`` (including the ``variable_code`` key
  used by odoo/odoo#275611) or ``VS:``-style tokens in the label; the
  variable symbol is prefixed into ``payment_ref`` (``"<vs> - <label>"``,
  never twice) so stock matching heuristics see it. Field names and
  semantics are deliberately compatible with upstream PR odoo/odoo#275611.
* QR integration: invoices pass their symbols to the QR generator via
  context (``cssk_payment_symbols``) — consumed by the Data Dance QR modules
  (QR Platba CZ, PAY by square, payme.sk).

.. rubric:: Module facts

- **Technical name:** ``l10n_cssk_payment_symbols``
- **Version:** 18.0.1.4.0
- **Licence:** AGPL-3
- **Requires:** ``account``

Authors: Data Dance s.r.o.
