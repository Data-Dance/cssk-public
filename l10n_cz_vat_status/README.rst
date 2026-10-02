========================================================
CZ VAT Status (plátce / identifikovaná osoba / neplátce)
========================================================

.. |badge1| image:: https://raster.shields.io/badge/license-AGPL--3-blue.png
    :alt: License: AGPL-3

|badge1|

| The Czech company's own VAT registration status over time, and what it does
| to invoices, vendor bills, DPHDP3 and the kontrolní hlášení.

**Table of contents**

.. contents::
   :local:


Why
===

A Czech company is not a plátce DPH for its whole life. It starts as a
neplátce, becomes a plátce when its turnover crosses the § 6 threshold or when
it registers voluntarily (§ 6f), may be an **identifikovaná osoba** in between
(§ 6g–6l) and may be deregistered again (§ 106, § 107b). Each change happens on
a particular day, usually mid-year, and every document is taxed by the status
on *its* day.

Until this module the localisation treated every Czech company as a plátce:
``res.company._l10n_cz_typ_platce`` in ``l10n_cz_statutory`` returned "P".


What it adds
============

* **VAT status history** on the company (*Company → VAT status*): rows of
  *from date → status*, each with an optional legal basis, event date and
  č. j. rozhodnutí. A row applies until the day before the next one.
* **"What was the status on date D"** — ``company._l10n_cz_vat_status_on(D)``
  — used by everything below.
* **DPHDP3** ``VetaD/typ_platce`` from that status on the return's last day:
  P / I / N (``_l10n_cz_typ_platce`` override; the signature is unchanged).
* **Taxes on documents** chosen by the status on the document's DUZP:

  .. list-table::
     :header-rows: 1

     * - tax (by its DPHDP3 row)
       - plátce
       - identifikovaná osoba
       - neplátce
     * - sale: domestic, export, § 64 goods (ř. 1, 2, 20, 22, 25, 26 …)
       - as is
       - **none**
       - **none**
     * - sale: § 9 odst. 1 service to the EU (ř. 21), triangular (ř. 31)
       - as is
       - as is (SH and ř. 21)
       - **none**
     * - purchase: domestic (ř. 40/41)
       - as is
       - **no deduction**, VAT to cost
       - **no deduction**, VAT to cost
     * - purchase: § 92a domestic reverse charge (ř. 10/11)
       - as is
       - ordinary VAT, to cost
       - ordinary VAT, to cost
     * - purchase: EU goods, EU and foreign services (ř. 3–6, 12, 13)
       - as is
       - **self-assessed, no deduction**
       - **none** (the supplier's VAT is in the price)
     * - purchase: import (ř. 7/8, 32, 42)
       - as is
       - **none** (paid to customs)
       - **none** (paid to customs)
     * - purchase: new means of transport (ř. 9)
       - as is
       - as is
       - as is

* **Kontrolní hlášení** only for days the company was a plátce.
* **Invoice PDF**: a document dated while the company is not a plátce is not
  presented as a daňový doklad, and carries the statement "Nejsem plátce DPH."
  (configurable per status on the company; empty prints nothing).
* **Sales and purchase orders** propose taxes by the status on the order date —
  in the auto-installed bridges ``l10n_cz_vat_status_sale`` and
  ``l10n_cz_vat_status_purchase``, so this module does not depend on ``sale``
  or ``purchase``.

**No history, no change.** Every effect is gated on the company having at least
one status row. A database that never records one keeps "P" on DPHDP3, the same
taxes, the same KH and the same invoice, and gets no new taxes.


The law it follows
==================

zákon č. 235/2004 Sb., o dani z přidané hodnoty, in its current wording
(read from the consolidated text, including the 2025 small-business changes).

Who owes and who deducts
------------------------

* **§ 108 odst. 1** — a *plátce* owes VAT on its taxable supplies. A neplátce
  and an identifikovaná osoba charge none on domestic supplies.
* **§ 108 odst. 4 písm. g)** — whoever states VAT on a document owes it. That
  is the liability the module keeps a non-payer from creating by accident, and
  why posting is refused rather than merely warned about.
* **§ 72 odst. 1** — the right to deduct belongs to a *plátce*; **§ 72
  odst. 5** — it arises when the obligation to declare the tax arose, i.e. at
  the supplier's tax point.
* **§ 108 odst. 2** — a plátce **or identifikovaná osoba** owes VAT on an
  intra-Community acquisition of goods (§ 16, tax point § 25).
* **§ 108 odst. 3 písm. a)** — a plátce **or identifikovaná osoba** owes VAT on
  a service (§ 9–10d), goods with installation, or goods through networks
  supplied by a person not established in CZ.
* **§ 108 odst. 3 písm. b)**, **odst. 4 písm. a)** (domestic reverse charge,
  § 92a) and **odst. 4 písm. c)** (import self-assessment) name only a
  *plátce*. **§ 108 odst. 5 písm. a)** — a non-payer pays import VAT to the
  customs office.

Filings
-------

* **§ 101 odst. 1** — a plátce and an identifikovaná osoba file DPHDP3; **§ 101
  odst. 5** — an IO with nothing to declare files nothing.
* **dphdp3_epo2.xsd** ``typ_platce``: *P – plátce § 6 až § 6fa, I –
  identifikovaná osoba § 6g až § 6l, S – skupina § 5a, N – neplátce dle § 108,
  R / D – nový dopravní prostředek § 19c / § 19b*. The XSD documentation of
  ř. 21 (``pln_sluzby``) confirms an IO reports its § 9 odst. 1 services there
  and on the SH.
* **§ 101c** — "*Plátce* je povinen podat kontrolní hlášení". The DPHKH1 XSD
  has no filer-type attribute and speaks only of "plátce"; its only answer for
  a non-filer is the výzva response "B – Nemám povinnost podat KH". So:
  **no KH for an IO or a neplátce.** A KH period with no plátce day cannot be
  computed; a period with some is computed from the plátce days' documents only.
* **§ 102 odst. 3 písm. a)** — an IO files the souhrnné hlášení for its § 9
  odst. 1 services to another member state. Their tax is kept, so
  ``l10n_cz_ec_sales`` reports them as it does for a plátce.

* **§ 72 odst. 1, § 73** — the *VAT period declared*
  (``cssk_vat_deduction_date``, from ``l10n_cssk_core``) exists for a plátce
  who exercises a deduction later than it arose. An IO or a neplátce has no
  deduction, so on a document whose DUZP falls in such a status the date is
  **ignored**: the document is reported in the period of its tax point, and
  its VAT is not moved off 343 by the deferral entries. What an IO carries on
  343 is a liability (§ 108 odst. 2 with § 25, § 108 odst. 3 písm. a) with
  § 24), declared for the period in which it arose (§ 101 odst. 1, § 20a).
  The form says so when such a date is recorded. A later change of the
  history withdraws or creates the deferral entries of the documents it moves
  across; one in a locked period is left as it is and says so in its chatter.

Documents
---------

* **§ 28 odst. 1** — the duty to issue a *daňový doklad* is a plátce's;
  **§ 28 odst. 3** — any osoba povinná k dani (so an IO too) issues one for a
  cross-border service. **§ 29 odst. 1** lists what a daňový doklad carries,
  among them the DUZP (písm. h)) apart from the issue date (písm. g)).

When a status begins and ends
-----------------------------

The *legal basis* + *event date* on a row propose its first day:

.. list-table::
   :header-rows: 1

   * - legal basis
     - the Act
     - first day
   * - § 6 odst. 1
     - plátce from 1 January of the following year
     - 1. 1. of the next year
   * - § 6 odst. 2
     - "dnem následujícím" after the threshold was exceeded
     - event + 1 day
   * - § 6f / § 94a (voluntary)
     - "ode dne následujícího po dni oznámení rozhodnutí"
     - event + 1 day
   * - § 6g / § 6h / § 6i
     - IO "ode dne" of the first acquisition / receipt / supply
     - event
   * - § 6j–6l / § 97a
     - IO from the day after oznámení
     - event + 1 day
   * - § 107b odst. 5
     - a plátce deregistered on request becomes an IO "dnem, kdy přestal být plátcem"
     - event
   * - § 106 odst. 8 písm. a) (ex officio)
     - ceases "dnem nabytí právní moci"
     - event
   * - § 107b odst. 3 (on request)
     - ceases "dnem následujícím po dni oznámení rozhodnutí"
     - event + 1 day
   * - § 106b (zánik registrace)
     - ceases the day before the triggering registration
     - event
   * - § 107 odst. 3 / § 107b odst. 4 (IO)
     - právní moc / the day after oznámení
     - event / event + 1 day

**§ 95 is repealed** in the current wording; registration is § 94 (mandatory)
and § 94a (voluntary). For a § 6 plátce the status arises by law on the day
above, whatever the date of the decision — enter that day, not the decision's.


Which date decides — and why the DUZP
=====================================

A document takes the status on its **DUZP** (``taxable_supply_date``), falling
back to the invoice date, then the accounting date.

The status answers two questions, and the Act anchors both on the tax point:

* **Does output VAT arise?** § 20a odst. 1: "Povinnost přiznat daň … vzniká ke
  dni uskutečnění zdanitelného plnění", and § 108 odst. 1 puts it on whoever is
  a plátce then.
* **Is input VAT deductible?** § 72 odst. 5: "Nárok na odpočet daně vzniká
  plátci okamžikem, kdy nastaly skutečnosti zakládající povinnost tuto daň
  přiznat" — again the supplier's tax point, not the day the bill is received
  or booked.

The issue date (§ 29 odst. 1 písm. g)) and the accounting date decide neither.
``l10n_cz`` fills the DUZP on every Czech invoice, so the fallbacks only cover
documents that arrive without one.

**Boundary days.** A row applies from its first day inclusive; the previous row
ends the day before. A document whose DUZP is the first day of a new status
falls under the new status; one dated the day before, under the old one.
Tested on both sides of a 30 June / 1 July change.

**Credit notes** follow the document they correct: a § 42 correction adjusts the
base of the original supply, so the original supply's regime applies even when
the credit note is issued after the change.

**Orders** have no tax point. Their date only *proposes* taxes; the invoice is
decided again by its own DUZP, and cannot be posted with taxes that do not fit.


How it works
============

Taxes are recognised by the **DPHDP3 row their base declares on** — the
``VAT <n> Base`` tags of ``l10n_cz``'s tax report — the same signal
``l10n_cz_vat_return`` uses for the ř. 43/44 deduction.

A tax that must change becomes a **twin**: a copy linked to its source
(``l10n_cz_vat_status_source_id``), generated when the company first records a
non-payer status, and never before.

* *No deduction* — one tax leg with **no account and no tags**. Odoo posts such
  a leg onto the base line's own account, so the supplier's VAT becomes part of
  the cost, 343 is never touched, and nothing reaches the return or the KH.
* *Self-assessed, no deduction* — the source's two legs and output tags
  (ř. 3–6, 12, 13) unchanged, except that the positive leg — the deduction side,
  on the input account 343 1xx — loses its account, so it lands on the cost,
  and every deduction-section tag (ř. 40–53) is removed. The liability stays on
  343 2xx and DPHDP3 reports the output tax and no ř. 43/44.

Because every twin points back to its source, a document's taxes can be
normalised to the plátce taxes and re-mapped for any status: changing the DUZP
of a draft across a status boundary moves the taxes both ways.

**Posting is refused** if an invoice's taxes do not fit the status on its DUZP
(including a tax whose twin could not be built), with *Apply VAT status taxes*
on the form to fix it. Imports that must reproduce a historical document as it
was can pass the context key ``l10n_cz_vat_status_skip_check``.

Two chart-wide passes of other modules are kept off the twins:
``l10n_cz_vat_return._cz_tag_selfassessed_deduction`` (which would tag a
ř. 43/44 deduction onto every two-legged purchase tax — an IO has none) and the
historical-rate generator of ``l10n_cssk_vat_return_base`` (the historical rates
get twins of their own).

A change to the status history recomputes the stored KH section of the posted
lines dated from the earliest changed day on.


Not handled
===========

* **§ 78–79 adjustments on a status change** — the odpočet of VAT on stock and
  assets when becoming a plátce (§ 79), and the snížení / odvod on
  deregistration (§ 79 odst. 1, § 78 ff.). Book them by hand.
* **The § 6 turnover-threshold monitor** — nothing watches the 2 000 000 Kč /
  2 536 500 Kč limits. The status is what you record.
* **Skupina (§ 5a, typ_platce S)** and **nový dopravní prostředek**
  (§ 19b / § 19c, typ_platce R / D): never returned; ř. 9 taxes are left alone.
* **Import VAT paid to customs** by a non-payer: the import taxes are removed
  from the vendor bill; the VAT the customs office assesses is booked from the
  customs document, as a cost.
* **Advance tax documents** (``sale_order_advance_invoice``) are titled "Tax
  Document" by that module; a non-payer should not issue them, and nothing here
  stops it.
* **OSS / small-business scheme (§ 110zc ff.)** registrations are not statuses
  of this module.


Open questions for the accountant
=================================

#. **ř. 12/13 for an identifikovaná osoba.** The chart's ř. 12/13 taxes cover
   both § 108 odst. 3 písm. a) (IO owes: services, installation, networks) and
   písm. b) (only a plátce owes: other goods from an unregistered foreign
   person). They are treated as IO-owed. Is that the right default, or should
   písm. b) goods get a separate tax?
#. **Intra-Community acquisitions around a boundary.** The status is taken on
   the DUZP the bill carries. For an acquisition the § 25 tax point (15th of the
   following month or the invoice date) can fall after the status change while
   § 6g counts from the day of the acquisition itself. Which date should decide?
#. **Credit notes after deregistration.** A credit note takes the status of the
   invoice it corrects. How should a former plátce document a § 42 correction
   of a supply made while it was a plátce?
#. **A DPHDP3 month split by a status change.** ``typ_platce`` is the status on
   the return's last day; the return's chatter flags the change. Does the tax
   office expect a separate return for part of the month?
#. **A plátce's own self-assessment with a later declared period.** For an
   IO the declared date is now ignored. For a plátce it still moves the whole
   document — liability (ř. 3–13) and deduction (ř. 43/44) together — to the
   declared period, as ``l10n_cssk_core`` always has. § 73 lets a plátce defer
   the deduction, but the liability arises at the tax point either way. Should
   the liability leg stay in the tax-point period while only the deduction
   moves?
#. **The invoice statement.** The default is "Nejsem plátce DPH." for both
   statuses (with "(identifikovaná osoba)" for an IO). A legal entity may prefer
   "Nejsme plátci DPH." — it is a company setting.


Configuration
=============

*Settings → Companies → (Czech company) → VAT status.* Leave it empty and nothing
changes. Otherwise record every change from the start — days before the first
row count as plátce. *Regenerate non-payer taxes* re-creates any missing twins
(it runs on its own whenever the history changes and before posting).


Author
======

* Data Dance s.r.o.

Contact
=======
https://www.datadance.eu/
