================================================================================
Dual Depreciation (danove vs ucetni/uctovne odpisy) - Accounting Cheat Sheet
================================================================================

This cheat sheet shows, group by group and method by method, how the
``account_asset_tax`` engine lays out the **tax-depreciation** plan (danove
odpisy) that runs *in parallel* with the ordinary **accounting-depreciation**
plan (ucetni / uctovne odpisy) on Czech and Slovak assets. It mirrors the style
of the *Method A* and *Advance Invoice* cheat sheets in this repository.

Every worked example below is also encoded as an automated test
(``account_asset_tax/tests/test_engine.py``), so the documentation and the
software cannot drift apart.

.. contents::
   :local:

What "dual depreciation" means
==============================

Czech and Slovak income-tax law makes every depreciable asset carry **two**
independent depreciation plans that almost never coincide:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Plan
     - Accounting depreciation (ucetni / uctovne)
     - Tax depreciation (danove)
   * - Governed by
     - Accounting act (CZ 563/1991 Sb. / SK 431/2002 Z.z.) + the company's own
       depreciation policy
     - Income-tax act (CZ 586/1992 Sb. / SK 595/2003 Z.z.)
   * - Useful life
     - Management estimate of real wear
     - Fixed by the statutory group (odpisova skupina)
   * - Posted to the GL?
     - **Yes** - monthly to account 551
     - **No** - it is a tax-base figure only
   * - Can be suspended?
     - No
     - Yes (CZ shifts the calendar; SK extends the life)
   * - Where it surfaces
     - Profit & loss, balance sheet
     - Corporate income-tax return (DPPO) as an adjustment

Because only the accounting plan hits the ledger, this module keeps the tax plan
as a **non-posted board** (``account.asset.tax.line`` records). The difference
between the two plans is what the year-end tax return reconciles.

The two boards side by side
===========================

A machine bought for 100 000 (CZ group 2, 5-year tax life), depreciated for
accounting over 8 years straight-line, in service in March 2026::

    Year   Accounting (posted 551)   Tax (not posted)   Difference   DPPO line
    2026         12 500                 11 000             +1 500       150 (add-back)
    2027         12 500                 22 250             -9 750       250 (deduction)
    2028         12 500                 22 250             -9 750       250
    2029         12 500                 22 250             -9 750       250
    2030         12 500                 22 250             -9 750       250
    2031         12 500                  0                +12 500       150
    2032         12 500                  0                +12 500       150
    2033         12 500                  0                +12 500       150
    ----------------------------------------------------------------------
    total       100 000                100 000               0

* **Accounting > Tax** in a year -> the excess is a **non-deductible add-back**
  (CZ DPPO radek 50; SK DPPO **line 150**).
* **Tax > Accounting** in a year -> the excess is an extra **deduction**
  (SK DPPO **line 250**).
* Over the whole life the two columns sum to the same base, so the timing
  difference reverses to zero (the source of *deferred tax* for audited
  entities).

Depreciation groups
===================

Czech Republic - zakon 586/1992 Sb. SS 30(1)
--------------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 10 14 38 19 19

   * - Group
     - Tax life
     - Examples
     - Linear SS 31 (1st / next / increased)
     - Accelerated SS 32 (k1 / kn / k-incr.)
   * - 1
     - 3 y
     - tools, computers
     - 20 / 40 / 33.3 %
     - 3 / 4 / 3
   * - 2
     - 5 y
     - machines, cars
     - 11 / 22.25 / 20 %
     - 5 / 6 / 5
   * - 3
     - 10 y
     - furnaces, large machinery
     - 5.5 / 10.5 / 10 %
     - 10 / 11 / 10
   * - 4
     - 20 y
     - towers, pipelines
     - 2.15 / 5.15 / 5.0 %
     - 20 / 21 / 20
   * - 5
     - 30 y
     - buildings, halls
     - 1.4 / 3.4 / 3.4 %
     - 30 / 31 / 30
   * - 6
     - 50 y
     - hotels, admin buildings
     - 1.02 / 2.02 / 2.0 %
     - 50 / 51 / 50

The method (linear vs accelerated) is chosen **per asset and cannot change** for
its whole life (SS 30(2)).

Slovakia - zakon 595/2003 Z.z. SS 26(1)
---------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 10 14 46 30

   * - Group
     - Tax life
     - Examples
     - Accelerated SS 28 (k1 / kn / k-incr.)
   * - 0
     - 2 y
     - electric vehicles, e-bikes/e-scooters (from 2025)
     - - (linear only)
   * - 1
     - 4 y
     - cars, notebooks, phones
     - - (linear only)
   * - 2
     - 6 y
     - machines, furniture
     - 6 / 7 / 6
   * - 3
     - 8 y
     - furnaces, generators
     - 8 / 9 / 8
   * - 4
     - 12 y
     - boilers, ships, aircraft
     - - (linear only)
   * - 5
     - 20 y
     - industrial buildings
     - - (linear only)
   * - 6
     - 40 y
     - hotels, admin buildings
     - - (linear only)

Slovak linear rate is simply ``entry price / life`` (no rate table). The
accelerated method is **only** available for groups 2 and 3 (since 1.1.2015).

Method walk-throughs
====================

CZ straight-line (SS 31) - full first year, no proration
--------------------------------------------------------

*Golden test:* ``test_cz_linear_full_first_year_no_proration``.

Group 2 machine, base 100 000, in service **March** 2026. The first year still
gets the **full** table rate - CZ bakes the "half" into the lower first-year
rate, so the in-service month is irrelevant::

    Y1  100000 * 11%    = 11 000     residual 89 000
    Y2  100000 * 22.25% = 22 250     residual 66 750
    Y3  100000 * 22.25% = 22 250     residual 44 500
    Y4  100000 * 22.25% = 22 250     residual 22 250
    Y5  100000 * 22.25% = 22 250     residual      0

A **first depreciator** of a group 1-3 asset may elect an increased first-year
rate (SS 31(1) b/c/d, +10/+15/+20 %). For group 2 the first-year/next rates
become 21/19.75 (+10 %), 26/18.5 (+15 %) or 31/17.25 (+20 %); each table still
sums to 100 %. Set it via *Increased First-Year Rate* on the asset.

CZ accelerated (SS 32)
----------------------

*Golden test:* ``test_cz_accelerated_known_series``.

Same machine, accelerated. Year 1 = base / k1; later years =
``2 * residual / (kn - years_done)``::

    Y1  100000 / 5                 = 20 000   residual 80 000
    Y2  2 * 80000 / (6 - 1)        = 32 000   residual 48 000
    Y3  2 * 48000 / (6 - 2)        = 24 000   residual 24 000
    Y4  2 * 24000 / (6 - 3)        = 16 000   residual  8 000
    Y5  2 *  8000 / (6 - 4)        =  8 000   residual      0

CZ extraordinary (SS 30a) - emission-free vehicles
--------------------------------------------------

*Golden test:* ``test_cz_extraordinary_60_40_split``.

Only zero-emission vehicles acquired 1.1.2024 - 31.12.2028, by the first
depreciator. 100 % over **24 months**, computed monthly starting the month after
the asset is put into use: 60 % spread over months 1-12, 40 % over months 13-24.
For a 600 000 EV in service March 2026 -> 30 000/month Apr 2026-Mar 2027, then
20 000/month Apr 2027-Mar 2028.

SK straight-line (SS 27) - monthly proration + remainder
--------------------------------------------------------

*Golden tests:* ``test_sk_linear_monthly_proration_and_remainder``,
``test_sk_linear_january_no_remainder``.

Slovakia prorates the first year by **whole months** from the in-service month
to year end; the unclaimed slice is deducted in the year **after** the end of
the life. Group 1 car, base 12 000 (annual 3 000), in service **March** (10
months)::

    Y1 (2026)  3000 * 10/12 = 2 500   residual 9 500   <- prorated
    Y2 (2027)  3000          = 3 000   residual 6 500
    Y3 (2028)  3000          = 3 000   residual 3 500
    Y4 (2029)  3000          = 3 000   residual   500
    Y5 (2030)    500 (remainder)        residual     0   <- life + 1

If the same asset is put into use in **January**, year 1 is the full 3 000 and
there is no remainder line (life = 4 years exactly).

SK accelerated (SS 28) - the "as-if full year" trap
---------------------------------------------------

*Golden test:* ``test_sk_accelerated_uses_full_first_year_residual``.

The actual first-year charge is prorated, **but** the residual that feeds the
year-2 formula is computed as if the *full* first-year charge had been taken
(SS 28(2)). Group 2 machine, base 60 000, in service March (10 months)::

    full Y1 = 60000 / 6 = 10 000   (used only to build the residual)
    Y1 actual = 10000 * 10/12      =  8 333.33
    Y2 = 2 * (60000 - 10000)/(7-1) = 16 666.67   <- 50000, not 51666.67
    Y3 = 2 * 35000 / (7 - 2)       = 13 333.33
    Y4 = 2 * 21666.67 / (7 - 3)    = 10 000.00
    Y5 = 2 * 11666.67 / (7 - 4)    =  6 666.67
    Y6 = 2 *  5000 / (7 - 5)       =  3 333.33
    Y7  remainder                  =  1 666.67   <- life + 1

Lifecycle events
================

.. list-table::
   :header-rows: 1
   :widths: 22 39 39

   * - Event
     - Czech Republic
     - Slovakia
   * - Technical improvement
     - Threshold **80 000 CZK** / asset / year (SS 33). Raises the entry price;
       linear then uses the *increased-price* rate, accelerated the
       *increased-residual* coefficient.
     - Threshold **1 700 EUR** / asset / year (SS 29). Raises the residual;
       accelerated recomputes from the increased residual (SS 28(3)).
   * - Suspension
     - Voluntary (SS 26(8)); the calendar simply **shifts** - the life is not
       extended.
     - Whole tax periods only (SS 22(9)); the total life is **extended** by the
       interruption. Mandatory when the asset is not used for taxable income.
   * - Disposal
     - Only **half** the annual charge in the year of disposal (SS 26(7)).
     - Pro-rata to the month of disposal; remaining tax residual is handled per
       the disposal reason.
   * - Method change
     - Forbidden for the asset's whole life (SS 30(2)).
     - Forbidden (SS 26(3)); accelerated only ever for groups 2 & 3.

These events re-invoke the engine from the event date with an adjusted base /
residual; filed (closed) years are frozen and never recomputed.

Component depreciation
======================

Component depreciation (komponentní / komponentné odpisovanie) — splitting a
building into separately-depreciated components — is an **accounting** method
(ČÚS / SK postupy). For **tax** purposes the asset stays whole: one tax board on
the building as a single entry. So nothing special is needed here — model the
components as the host framework's accounting assets, and keep **one tax asset**
for the whole building. The larger accounting-vs-tax gap that component
depreciation creates simply flows through the reconciliation below.

Year-end reconciliation (DPPO)
==============================

For each fiscal year the accountant compares the posted **accounting**
depreciation with the **tax** board:

* SK DPPO **Table B** lists the annual tax depreciation per asset.
* ``sum(accounting) - sum(tax)`` for the year:

  * positive -> **add-back** (SK line 150 / CZ radek 50)
  * negative -> **deduction** (SK line 250)

The bridge module exposes this comparison (it needs the accounting board, which
is edition-specific); the core keeps only the tax side.

The Odoo model map
==================

.. list-table::
   :header-rows: 1
   :widths: 34 22 44

   * - Model / field
     - Module
     - Role
   * - ``account.asset.tax.class``
     - core
     - One statutory group (code, life, rates, coefficients, allowed methods)
   * - ``account.asset.tax.line``
     - core
     - One year (or SS 30a month) of the **non-posted** tax board
   * - ``account.asset.tax.mixin``
     - core
     - Tax fields + the engine orchestration, mixed into ``account.asset``
   * - ``engine.depreciation``
     - core
     - Pure-Python calculator (no ORM) - all statutory maths lives here
   * - ``asset_id`` on the tax line, ``tax_line_ids`` O2m
     - bridge
     - The asset <-> tax-line relation (kept out of core so it fits both editions)
   * - ``_tax_get_entry_value`` / ``_tax_get_in_service_date``
     - bridge
     - Read the base & start date from the EE or OCA asset fields

Configuration
=============

1. Install the **core** ``account_asset_tax`` plus the matching **bridge**:

   * Enterprise (``account_asset``) -> ``account_asset_tax_ee``
   * Community + OCA (``account_asset_management``) -> ``account_asset_tax_oca``

2. Install the **country data** layer: ``l10n_cz_account_asset_tax`` and/or
   ``l10n_sk_account_asset_tax`` (loads the groups & coefficients).

3. On an asset, open the **Tax Depreciation** page, tick *Track Tax
   Depreciation*, pick the **group** and **method**, confirm the **tax entry
   value**, and press **Compute Tax Board**.

Sources
=======

* CZ - zakon 586/1992 Sb., consolidated text valid 01.04.2026-31.12.2026
  (zakonyprolidi.cz, verze 156); SS 30, 30a, 31, 32, 33.
* SK - zakon 595/2003 Z.z., consolidated text valid from 01.01.2026
  (slov-lex.sk); SS 22, 26, 27, 28, 29; Financna sprava FAQ on rovnomerne /
  zrychlene odpisovanie.
* Software reference model: KROS Omega asset card (two plans; tax plan feeds
  DPPO Table B + lines 150/250).
