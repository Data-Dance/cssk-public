=====================================
SK DPPO ↔ účtovná závierka porovnanie
=====================================

Glue module that wires the Slovak **DPPO** income-tax return (``l10n_sk_dppo``)
to the **účtovná závierka** — Súvaha + VZS, UZPODv14 (``l10n_sk_fs``) — and adds
the cross-form reconciliation between them to the shared SK reconciliation
engine in ``l10n_sk_datadance``.

The income-tax return starts from the accounting result: DPPO **r100**
(*výsledok hospodárenia pred zdanením*, ``5,6,-591,-592,-595,-596``) is the same
figure as VZS **r56**. The tie is exact — both exclude daň z príjmov (591/592/595)
and prevod podielov (596) — so a difference is not a rounding artefact but a
disagreement between two filings about the same accounting result, and it is
reported as an error.

It ``auto_install``s when its two optional pieces are both present.

Why a separate module
=====================

``l10n_sk_fs`` and ``l10n_sk_dppo`` are **settings toggles** of the Slovak
bundle, not dependencies of it: both are delivered to subscribers rather than
published, and a hard dependency would make ``l10n_sk_datadance``
uninstallable from the public repository. Glue that ``_inherit``s
``cssk.income.tax.return`` therefore cannot live in the umbrella — the model is
not in the graph unless the DPPO toggle was ticked. It lives here instead.

Features
========

* *Porovnať s účtovnou závierkou* on the DPPO form: finds the UZPODv14 závierka
  covering the return's period (an exact period match wins over an overlap),
  compares VZS r56 against DPPO r100 and posts the comparison to the chatter.
* ``VZSDPPO_RECON`` — an **error**-severity kontrola when the two disagree
  beyond the reconciliation tolerance, typically a manual r100 override or a
  závierka built for a different obdobie.
* ``reconcile_vzs_dppo`` / ``check_kontroly_vzs_dppo`` on
  ``l10n.sk.dph.reconciliation``, alongside the KV ↔ priznanie, súhrnný výkaz ↔
  priznanie and priznanie ↔ účtovníctvo reconciliations.

Usage
=====

Build the účtovná závierka for the year (*Accounting ▸ Reporting ▸ Účtovná
závierka*) and the DPPO return for the same period, compute both, then press
*Porovnať s účtovnou závierkou* on the return. With no závierka for the period
the action explains that and stops rather than comparing against nothing.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
