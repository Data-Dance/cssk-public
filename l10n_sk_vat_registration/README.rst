==========================================
SK VAT Registration Category (§ 4 / § 7)
==========================================

.. |badge1| image:: https://raster.shields.io/badge/license-AGPL--3-blue.png
    :alt: License: AGPL-3

|badge1|

| Which paragraph of the SK VAT Act a partner's IČ DPH was issued under.

**Table of contents**

.. contents::
   :local:


Why
===

An IČ DPH does not mean the same thing for everyone who holds one.

A subject registered under **§ 7** (nadobudnutie tovaru z iného členského
štátu) or **§ 7a** (dodanie / prijatie služby) receives a valid IČ DPH that
**VIES confirms** — and is **not a platiteľ dane**. They deduct no input VAT,
charge no VAT on domestic supplies, and **§ 69 ods. 12 domestic reverse charge
cannot apply to them**, because that provision names a platiteľ on both sides.

VIES cannot tell you this. It answers *valid* or *not valid*. The paragraph is
in the Finančná správa registration record, which ORSF republishes as
``vatRegistration.druhReg``.


What it adds
============

On ``res.partner``:

#. **Druh registrácie DPH** — § 4 / § 4b / § 5 / § 6 / § 7 / § 7a
#. **Platiteľ DPH od**
#. **Platiteľ dane** — computed, true only for § 4 / § 4b / § 5 / § 6

On a customer invoice, a **warning** when a domestic reverse-charge tax is used
for a § 7 / § 7a customer.


The warning never blocks
========================

It computes onto the form, and posts its reason to the chatter on posting. It
does not stop the posting, for the same reason
``l10n_cssk_payment_reliability`` does not: the register is an aggregator's
copy, the categories move, and refusing to post an invoice on that basis would
be worse than the error it prevents.

An **unknown** category is treated as unknown, never as "not a platiteľ" — the
difference changes how an invoice is taxed, so the parser rejects anything it
does not recognise rather than guessing.

The check recognises a reverse-charge supply through ``l10n_sk_invoice``'s
per-tax ``l10n_sk_reverse_charge`` flag, detected at runtime rather than
declared as a dependency. Without that module there is no reliable signal and
the check stays quiet.


Scope
=====

**Have an accountant confirm the mapping for your own tax setup.** This module
records a register fact and raises one narrow inconsistency. It does not decide
a fiscal position, and it is not a substitute for a VIES check —
``l10n_cssk_vies`` still answers whether the number is valid at all.


Filling it from the register
============================

Install ``partner_autocomplete_orsf_sk``. It fills both fields on enrichment,
and writes a category only when the register actually stated one.


Author
======

* Data Dance s.r.o.

Contact
=======
https://www.datadance.eu/
