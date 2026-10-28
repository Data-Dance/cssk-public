---
title: SK VAT Control Statement — Point of Sale in D.1
summary: Reports the sales of every Odoo Point of Sale session in oddiel D.1 of the Slovak kontrolný výkaz DPH, as eKasa turnover, instead of D.2.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

A Slovak VAT payer reports the turnover recorded by its eKasa cash registers
in oddiel **D.1** of the kontrolný výkaz DPH, and only what eKasa did not record
in D.2. A sale at an Odoo Point of Sale till is such a turnover: the till is a
*pokladnica eKasa*, for instance the Finančná správa's virtual cash register
through [module:pos_vrp2](module:pos_vrp2).

Odoo posts a session's sales as one closing entry with no customer, so the
Slovak section rules of [module:l10n_sk_kv_dph](module:l10n_sk_kv_dph) read it
as a supply to private individuals and filed it in **D.2**, unless its journal
had been marked `D.1` by hand. With this module installed every session's
closing entry goes to **D.1**.

## Legal background {#legal}

- The [VAT act (zákon o DPH)](law:sk/2004/222), § 78a: the kontrolný výkaz.
- The poučenie to the kontrolný výkaz, oddiel D.1: the data are reported by
  the payer "ktorý je povinný evidovať tržby pokladnicou e-kasa klient", and
  D.2 takes "len tie dodania tovaru alebo služby, ktoré nezahrnul do D.1".
- The act on the recording of sales (zákon č. 384/2025 Z. z., before 2026
  zákon č. 289/2008 Z. z.) obliges the seller to record every sale at the
  point of sale in a pokladnica eKasa.

## How it works {#usage}

Nothing to set up: the module installs itself when both the Slovak control
statement and Point of Sale are installed.

- The **closing entry of a POS session** is reported in D.1: the turnover
  including VAT and the base and tax at the basic and the reduced rates (see
  the D.1 row in [module:l10n_sk_kv_dph](module:l10n_sk_kv_dph#sections)).
  Returns made in the session are netted into it.
- An **invoiced POS order** is an invoice and stays in A.1 (or D.2 for a
  private customer); the receipt for its payment is not turnover.
- A journal with its own **Control-statement section override** keeps it.

Sections already stored on posted entries are not recomputed by installing
the module; an administrator recomputes them, as the shared guide describes.

## Limitations {#limitations}

- Only the session's closing entry is recognised. A cash-register sale booked
  any other way still needs its journal set to `D.1`.
