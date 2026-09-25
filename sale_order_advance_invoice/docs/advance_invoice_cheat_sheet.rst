===============================================================
Advance Invoices (zálohová / preddavková faktura) — Cheat Sheet
===============================================================

A practical reference for the advance-invoice flow implemented by
``sale_order_advance_invoice`` and its Czech/Slovak localizations.
All journal entries are written **debit account / credit account**
(CZ *MD / Dal*, SK *MD / D*).

.. contents:: Contents
   :local:

Concept: the three-document flow
================================

In Czech and Slovak accounting an advance ("záloha" / "preddavok") follows a
three-document model:

1. **Advance / proforma invoice** (zálohová / preddavková faktura) — a *payment
   request only*. It is **not** an accounting or tax document and is **not
   posted**. In this module it is a dedicated sale order with
   ``is_advance_invoice = True``.
2. **Tax document on the received payment** (CZ *daňový doklad k přijaté platbě*,
   SK *faktúra k prijatej platbe*) — issued **within 15 days** of receiving the
   payment. This is the accounting/tax document that declares the VAT.
3. **Final / settlement invoice** (CZ *vyúčtovací faktura*, SK *vyúčtovacia /
   ostrá faktúra*) — the full supply, with the advance **deducted** and the VAT
   already declared on the advance **reversed** so it is not paid twice.

The VAT liability arises on **receipt of the payment**, not on issuing the
proforma.

Account roles
=============

The module is country-neutral; the localization modules map these roles onto the
statutory chart of accounts.

.. list-table::
   :header-rows: 1
   :widths: 32 12 12 44

   * - Role (company setting)
     - CZ
     - SK
     - Purpose
   * - Advance **clearing** account (``advance_received_account_id``)
     - 324001 *
     - 324001 *
     - Reconcilable transit account where the payment and the tax-document
       receivable meet and are reconciled to zero.
   * - Received advance, **short-term** (``advance_tax_doc_account_id``)
     - 324000
     - 324000
     - Net (ex-VAT) advance liability until settled on the final invoice.
   * - Received advance, **long-term** (``advance_tax_doc_account_lt_id``)
     - 475000
     - 475000
     - As above, for advances settled after more than one year.
   * - VAT (``343``)
     - 343xxx
     - 343xxx
     - Output VAT declared on the tax document.
   * - Bank / AR / revenue
     - 221 / 311 / 60x
     - 221 / 311 / 60x
     - Standard accounts used by the payment and final invoice.

\* The reconcilable clearing sub-account is shipped by the localization module
because the standard chart's 324000 is a non-reconcilable liability.

Configuration
=============

Install a localization module — ``l10n_cz_sale_order_advance_invoice`` or
``l10n_sk_sale_order_advance_invoice`` — and the accounts and a dedicated tax
document journal are configured automatically for every company on that chart
template (existing manual configuration is preserved).

Manual setup lives in **Settings → Sales → Advance Invoices**: the tax-documents
journal and the three accounts above.

Creating an advance invoice
===========================

From a confirmed sale order, **Create Advance Invoice** opens a wizard that can
charge:

* the **full** amount,
* a **percentage** of the untaxed total, or
* a **fixed** amount.

Optionally **Copy Products** reproduces the order's lines (description only) so
the advance itemizes what it covers. A tracking "Advance Invoices" section is
added to the parent order, mirroring Odoo's down-payment tracking.

Worked example: receiving and taxing the advance
================================================

Customer advance of 1 210 (1 000 net + 210 VAT @ 21%).

**1. Payment received** — registered on the advance invoice (QR, manual payment,
or by linking a bank transfer):

.. list-table::
   :header-rows: 1
   :widths: 60 20 20

   * - Posting
     - Debit
     - Credit
   * - Bank 221 / Clearing 324001
     - 221  1 210
     - 324001  1 210

**2. Tax document** (within 15 days, *taxable supply date* = payment date):

.. list-table::
   :header-rows: 1
   :widths: 60 20 20

   * - Posting
     - Debit
     - Credit
   * - Clearing 324001 (receivable side)
     - 324001  1 210
     -
   * - Net received advance 324000
     -
     - 324000  1 000
   * - Output VAT 343
     -
     - 343  210

The two 324001 legs (payment credit and tax-document debit) are **reconciled**,
netting the clearing account to zero. Result: 221 debit 1 210, 324000 credit
1 000, 343 credit 210.

Worked example: settlement on the final invoice
===============================================

The final invoice posts the full supply, then deducts the advance:

* Full revenue and full VAT are posted as normal (311 / 60x + 343).
* A deduction line debits the **net received advance** (324000) for 1 000 and
  **reverses the advance VAT** already declared (343) — so VAT is ultimately paid
  only once, on the full supply.

If the advance had **no** tax document yet, the deduction instead removes the
gross amount with no VAT split, and the clearing balance is cleared by a separate
entry after posting.

Long-term advances
==================

Tick **Long-term Advance** on the advance invoice to settle it against the
long-term received-advance account (475) instead of the short-term one (324).
Everything else in the flow is identical.

Standalone advance invoices
===========================

An advance invoice created without a parent order can be attached to a final
invoice with the **Link Advance Invoices** wizard, which only offers advances of
the same customer that are not already settled elsewhere. The same with/without
tax-document accounting rules apply to the deduction lines.

Statuses and deadlines
======================

* **Payment status** — none / partially / fully / overpaid / cancelled.
* **Accounting status** — *nothing to account* → *waiting* (a tax document is due)
  → *accounted* (tax document posted, or the advance was settled on the parent's
  final invoice).
* **Accounting due date** — the statutory tax-document deadline, by default the
  earlier of 15 days after payment and the end of that month
  (``_advance_invoice_tax_doc_deadline``, overridable per localization).

Czech vs Slovak notes
=====================

The structural model, account numbers and the 15-day rule are shared. The
differences are terminology (CZ *daňový doklad k přijaté platbě* vs SK *faktúra k
prijatej platbe*; CZ *vyúčtovací* vs SK *vyúčtovacia / ostrá faktúra*) and CZ's
more consistent use of 475 for long-term received advances.

EDI / ISDOC
===========

The module exposes ``is_advance_invoice`` and ``is_advance_invoice_tax_document``
(plus the tracking fields) as a stable contract. The ISDOC bridge
``account_edi_isdoc_sale_advance`` keys off these to export advance invoices and
their tax documents in the correct ISDOC document types.
