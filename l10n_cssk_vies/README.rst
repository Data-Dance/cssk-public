====================================================
CZ/SK VIES — direct EU check & proof of consultation
====================================================

Odoo 19 core ``base_vat`` validates EU VAT numbers through **Odoo IAP**
(``vies.api.odoo.com``) and stores only a ``vies_valid`` boolean. A self-hosted
instance without IAP gets no VIES check at all, and there is no record of *when*
a number was confirmed or the official **consultation number** that is the legal
proof of an intra-Community exemption check (*overenie IČ DPH* SK /
*ověření DIČ* CZ).

This module calls the European Commission VIES REST service **directly** (no
Odoo account, no IAP) and stores the consultation number and the rest of the
proof on the partner. Works on Community and Enterprise.

Features
========

* **Direct EU VIES** — per-company opt-in (*Use direct EU VIES*); calls the
  European Commission VIES REST service directly.
* **Proof of check** — logs every check per partner and requesting company:
  the VIES **consultation number** (``requestIdentifier``), the check
  timestamp, the VIES request date, and the registered trader name / address +
  name-match result. The automatic check core runs when a VAT number is
  entered is logged too.
* A manual **Check VIES (direct)** action on the partner.
* A daily **cron** that refreshes stale checks for companies in direct mode —
  foreign EU VAT numbers of contacts shared with or owned by the company.
* Transient VIES faults (member-state system down, rate limit) are reported as a
  *fault* — never silently flipping a partner to *invalid* or clearing proof.

Usage
=====

Turn on *Use direct EU VIES* in *Settings ▸ Accounting* for the company. On any
partner with an EU VAT number, press **Check VIES (direct)**: the consultation
number and registered name/address fill in on a valid qualified check. The daily
cron re-checks partners whose last check by the company is older than the
staleness window, leaving out domestic VAT numbers and other companies'
contacts.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
