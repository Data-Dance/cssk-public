==========================================
Slovakia — VAT Return (Daňové priznanie)
==========================================

Slovak VAT return (DPHv25) on top of ``l10n_cssk_vat_return_base``. Line
definitions mirror the ``l10n_sk`` DPH report tag formulas, computed CE-clean
(no ``account_reports``).

Depends on ``l10n_sk`` + the shared framework.

Status
======

**Functional (core).** Output base/tax lines (categories 01/03/05), deduction
lines (19/20) and the output-total / deductions / net aggregates compute from
real l10n_sk tags and export to a stand-in ``DPH`` XML (verified by a test:
1000 base → 230 tax → net 230). To complete:

* The full SK form line set + the net-payable lines Odoo computes with
  ``sum`` / custom engines (sk_30+) — need extended engine support.
* Official FS SR XSD + element names (the shipped XSD is a stand-in).
* Accountant validation of line semantics and the net-payable computation.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
