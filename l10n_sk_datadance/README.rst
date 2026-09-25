==========================================================
Slovak Accounting Localization (Data Dance) — full suite
==========================================================

The one-click Slovak statutory localization meta-module. Installing it pulls in
the **Slovak statutory core** in a single step: KV DPH (control statement),
Súhrnný výkaz (EC sales list), DPH priznanie (VAT return), Súvaha + VZS
(financial statements), DPPO (income tax), SK invoice, VIES, saldokonto + zápočet
and dohadné (accruals).

Optional workflow pieces (FX sync, deferrals, the guarantor-liability /
supplier-reliability check, dual depreciation, Method A inventory and advance
invoices) are **selectable in Settings → Accounting → Slovak localization** — tick
the box to install the corresponding module.

On top of bundling, this module adds **cross-form reconciliation** between the
already-filed Slovak statements: it ties the kontrolný výkaz, súhrnný výkaz, DPH
priznanie, účtovná závierka (VZS) and DPPO to one another and to the ledger,
flagging structurally impossible mismatches.

Features
========

* Meta-installer for the Slovak statutory core (one dependency set).
* Settings toggles for the optional workflow modules.
* Cross-form reconciliation (porovnanie) between KV DPH, súhrnný výkaz, DPH
  priznanie, VZS/DPPO and the ledger account 343.

Usage
=====

Install the module to provision the Slovak core. Open *Settings ▸ Accounting ▸
Slovak localization (Data Dance)* to tick the optional pieces you need. The
reconciliation checks are launched from the statement forms (see Wizards).

Wizards
=======

* **SK cross-form reconciliation** (``l10n.sk.dph.reconciliation``) — an advisory
  comparison (porovnanie) between the Slovak statutory statements that share the
  same tax-tagged move lines. It is launched from buttons added to the existing
  statement forms (visible once the statement is out of *draft*):

  * On the **DPH priznanie** form: *Porovnať s účtovníctvom* — ties output VAT
    (r17) and input deduction to account 343, and reports the base-vs-revenue
    (trieda 60) gap as informational.
  * On the **Súhrnný výkaz** form: *Porovnať s priznaním* — ties EC-sales goods
    (code 0) to priznanie r14.
  * On the **DPPO** form: *Porovnať s účtovnou závierkou* — ties the accounting
    result before tax (VZS r56) to DPPO r100 (an exact tie).

  KV ⊆ DP relationships are reported as expected non-KV content; only impossible
  cases (KV > priznanie, SV ≠ r14, VZS ≠ r100) are flagged as warnings/errors.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
