=====================================
SK Účtovná závierka — závierkové účty
=====================================

Slovak accounting closes the year through three **závierkové účty**, which Odoo
has no concept of:

* **710 — Účet ziskov a strát**: collects trieda 5 (náklady) and trieda 6
  (výnosy); its balance is the výsledok hospodárenia.
* **702 — Konečný účet súvahový**: collects every súvahový účet (triedy 0–4) plus
  the result carried from 710.
* **701 — Začiatočný účet súvahový**: reopens those balances in the new year.

This ships as a **closing template** on the OCA ``account_fiscal_year_closing``
engine, wired to ``l10n_sk``. Creating a closing copies the template into an
editable record, so the mapping is a starting point the accountant adjusts.

Two deliberate deviations from the generic engine
=================================================

**1. The závierkové účty are retyped.** ``l10n_sk`` ships 701/702/710 with
``account_type = off_balance``, and Odoo hard-refuses any entry that mixes an
off-balance account with an ordinary one
(``account_move_line._check_off_balance``). As shipped, the Slovak závierka is
therefore impossible to post at all. This module retypes them to ``equity`` — for
new companies through the chart template, for existing ones through a post-init
hook. It does **not** disturb the statutory statements, because ``l10n_sk_fs``
maps rows by account **code**, not by type; it does make the accounts visible to
Odoo's own generic balance sheet, which is the price of being able to close.

**2. 702 carries a counter-entry per account, not just the net.** The generic
engine posts one destination line holding the *net* of all sources — and on a
complete balance sheet that net is zero, so 702 would not appear in the entry at
all, leaving assets simply contra-posed against liabilities. Mechanically
balanced, but not the Slovak závierka: 702 is precisely the account every
súvahový účet is closed *against*. The module mirrors each closed account onto
it, so 702's own total is zero by the bilančná rovnosť rather than by omission.

What it does **not** do
=======================

The **transfer of the approved result to 431** (and on to 428/429) is a separate
event — it happens when the závierka is approved, not when it is closed. That
posting ships as a *predkontácia* in ``l10n_sk_account_move_template``
(*Preúčtovanie schváleného zisku / straty*).

Honesty flag
============

Closing conventions vary between účtovné jednotky, in particular whether the
result reaches 702 straight from 710 or via 431 within the closing itself. The
template implements the mainstream route (710 → 702) and stays editable per
closing. Real-data validation against MRP's 2024 books already showed the
result-to-431 convention is where implementations differ, so this mapping wants
**accountant sign-off** before a live závierka.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3 (see the LICENSE file) — it depends on the AGPL OCA engine.
