=========================================================
CZ/SK OSS VAT Return — Shared Framework (Union scheme)
=========================================================

Country-neutral engine behind the quarterly **One-Stop-Shop VAT return**,
Union scheme (CZ *zvláštní režim jednoho správního místa — režim Unie*, SK
*osobitná úprava — úprava pre Úniu*). The Czech (``l10n_cz_oss``, EPO OSSEI1)
and Slovak (``l10n_sk_oss``, DPOSS_EUv01) layers render and validate the XML.

Built on Odoo core ``l10n_eu_oss``
==================================

Core creates an *OSS B2C* fiscal position per member state and a
destination-rate sale tax per mapped domestic rate; every repartition line of
those taxes carries the ``OSS`` tax tag. This module reads the journal items
carrying that tag:

* **rows** per member state of consumption × supplied-from state × goods /
  services × rate, from the base lines;
* **corrections** of earlier quarters per member state (VAT only): a credit or
  debit note whose original invoice lies in an earlier quarter corrects that
  quarter instead of producing a negative row;
* the **booked** OSS VAT from the tax lines, checked against the computed VAT.

Enterprise's ``l10n_eu_oss_reports`` exports Belgium and Luxembourg only, so the
return is ours on both editions.

EUR conversion
==============

Amounts invoiced in EUR are taken as invoiced. Any other document currency is
converted at the **ECB reference rate for the last day of the quarter, or the
next day of publication** — Directive 2006/112/EC Art. 369h(2); CZ § 110ze
odst. 2 písm. a) zákona č. 235/2004 Sb.; SK § 68b ods. 17 zákona č. 222/2004
Z. z. A correction uses the rate of the corrected quarter (CZ § 110ze odst. 2
písm. b)). Rates are proposed from the company's rate table and must be
**confirmed** as ECB rates before export, because the table may hold ČNB or
bank rates.

Slovak 5 % rate
===============

Core's ``EU_TAX_MAP`` has no Slovak 5 % rate (in force since 1. 1. 2025) in
either direction. ``res.company._map_eu_taxes`` adds it without editing core:

* the lookup core performs is answered through a scoped overlay (a
  ``ContextVar`` set only while this module's mapping runs), so databases in
  the same server process that do not have this module keep core's map;
* **SK 5 % → another state** maps to whatever core maps SK 10 % to (the old
  band of books, medicines and basic food);
* **another state → SK 5 %**: each source state's lowest reduced rate, plus
  CZ 12 % (the merged Czech reduced rate since 2024);
* 19.0 core links only the FIRST domestic tax per foreign rate; the others are
  linked afterwards, as 18.0 did, which is what lets SK 5 % and SK 19 % share
  a destination rate.

These are proposals, as core's own mapping is: check them against what is sold.

Not covered
===========

* The non-Union and import (IOSS) schemes — core has no taxes for them.
* Supplies from another member state (a warehouse or establishment abroad) are
  not detected from the documents; enter them as manual rows, which survive a
  recompute.
* Rows are typed goods/services from the product (a line without a product
  counts as goods).

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
