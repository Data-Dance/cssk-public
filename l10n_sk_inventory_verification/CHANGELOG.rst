=========
Changelog
=========

All notable changes to **l10n_sk_inventarizacia** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- **Renamed from ``l10n_sk_inventarizacia``.** The technical name is now
  English, like most of the repository. No migration is shipped, because the
  module was not yet installed in production. A development database that
  had it installed keeps an orphaned ``l10n_sk_inventarizacia`` row. Install
  ``l10n_sk_inventory_verification`` there.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **19.0.1.2.0 (2026-11-24), not yet on 18.0:** booking of inventarizačné
  rozdiely, with the new dependency ``l10n_cssk_inventory_verification_base``
  (port that first). 18.0 deltas to expect: ``<list>`` and ``<chatter/>`` are
  fine there; check ``_get_violated_lock_dates`` and ``_format_lock_dates`` on
  ``res.company``, the ``reversal_move_ids`` field and whether ``_post``
  moves a locked-period entry at all on 18.0 before porting the guard.

- **19.0.1.1.2 (2026-11-15), not yet on 18.0:** the three súpis amounts are
  computed by three methods, so a typed účtovný stav saved with the items no
  longer leaves the skutočný stav at 0.

- **19.0.1.1.0 (2026-10-27), not yet on 18.0:** súpis opens in a form, print
  and refresh buttons, seat on both printouts, the § 30 ods. 3 písm. d)
  label.

- DISCHARGED 2026-09-30 by 6f9cc41 on branch 18.0-catch-up (reaches 18.0
  when that branch lands) — do not port this again.
  **The rename (2026-09-30), not yet on 18.0.** 18.0 still ships
  ``l10n_sk_inventarizacia``. Rename it together with the rest of the
  2026-09-30 batch (the fiscal-year closing, surcharges, annual tax
  settlement and inventory verification modules). Rename every reference
  too: dependent manifests, ``odoo.addons.*`` imports, the ``.pot`` file
  name and ``module_*`` settings toggles. The 19.0 commit is the checklist.

Carry-over to 20.0
~~~~~~~~~~~~~~~~~~

- DISCHARGED 2026-09-30 by 51a5085 on branch 20.0 — do not port this again.
  **The rename (2026-09-30), not yet on 20.0.** 20.0 still ships
  ``l10n_sk_inventarizacia``. Rename it together with the rest of the
  2026-09-30 batch (the fiscal-year closing, surcharges, annual tax
  settlement and inventory verification modules). Rename every reference
  too: dependent manifests, ``odoo.addons.*`` imports, the ``.pot`` file
  name and ``module_*`` settings toggles. The 19.0 commit is the checklist.

[19.0.1.2.0] — 2026-11-24
-------------------------

Added
~~~~~

- **Inventarizačné rozdiely are booked.** A new tab settles the difference of
  each súpis — manko or schodok, úbytok do normy, prebytok, and the náhrada
  claimed from the liable person — and creates a draft journal entry dated the
  deň, ku ktorému bola inventúra vykonaná (§ 30 ods. 7). Accounts are proposed
  from the postupy účtovania: a cash schodok as a receivable 335 / 211
  (§ 11 ods. 1 písm. b)), stock 549 / 501 / 504 / 648, own production through
  61x, a newly found depreciated asset against 384. Both accounts stay
  editable.
- A súpis whose difference is settled elsewhere is marked as not booked here,
  with a reason; the entry is refused until every difference is either
  explained in full or so marked.
- Reopening the inventarizácia, or *Zrušiť zaúčtovanie rozdielov*, deletes a
  draft entry and reverses a posted one on the same day.
- The zápis prints the settlement: kind, debit and credit account, amount and
  the journal entry.
- *Účet* can be filled on a fyzická inventúra too; the proposal starts from
  it.

Changed
~~~~~~~

- Depends on the new ``l10n_cssk_inventory_verification_base``, which holds
  the booking logic shared with the Czech module.
- **Multi-company record rules.** An inventory verification, its count
  sheets and its differences are visible only in the companies the user is
  working in; until now they had no rule and showed across companies.
- **A locked period refuses the booking.** Odoo moves an entry dated in a
  locked period to the first open day when it is posted; for an inventory
  difference that is another accounting period. Creating, posting and
  reversing these entries stop with a message instead.

[19.0.1.1.2] — 2026-11-15
-------------------------

Fixed
~~~~~

- **A typed účtovný stav no longer zeroes the skutočný stav.** On a fyzická
  inventúra, an účtovný stav entered and saved together with the items left
  the skutočný stav and the rozdiel of the súpis at 0, on screen and on the
  printout. Súpisy saved that way show the right amounts once an item or the
  účtovný stav is saved again.

[19.0.1.1.1] — 2026-11-05
-------------------------

Fixed
~~~~~

- Czech catalogue: translated the strings that were still English.

[19.0.1.1.0] — 2026-10-27
-------------------------

Fixed
~~~~~

- **The items of a súpis could not be entered.** The súpisy were an
  inline-editable list, so the súpis form holding its položky never opened.
  Adding or clicking a súpis now opens it in its own window.
- **The inventúrny súpis could not be printed.** *Tlačiť inventúrne súpisy*
  at the top of the inventarizácia prints them.
- **The seat was missing on both printouts.** The súpis and the zápis now
  print the company's address next to its name (§ 30 ods. 2 písm. a) and
  ods. 3 písm. a) zákona 431/2002).
- The person on the zápis is *Zodpovedný za vykonanie inventarizácie*, as
  § 30 ods. 3 písm. d) words it (was *Zápis vyhotovil*).

Added
~~~~~

- **Načítať zostatok účtu** (in a súpis) and **Načítať účtovné stavy** (on the
  inventarizácia) re-read the ledger for a dokladová inventúra, picking up
  entries posted after the súpis was made. A fyzická inventúra's typed
  účtovný stav is left alone.

[19.0.1.0.2] — 2026-10-27
-------------------------

Fixed
~~~~~

- **Field help cited the wrong letters of § 30 ods. 2.** Miesto uloženia
  majetku is písm. d) (was f)), hmotne zodpovedná osoba písm. e) (was g)).
  The day of the inventory is § 29 ods. 2 (was ods. 1) and the physical /
  documentary inventory § 30 ods. 1 (was § 29 ods. 2).

[19.0.1.0.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the source are
  deliberately left untranslated — the source IS the translation, per the
  hybrid convention for these modules — so an empty ``msgstr`` there is correct
  rather than missing.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.0] — 2026-08-05
-------------------------

Added
~~~~~

- ``l10n.sk.inventarizacia`` with the three § 30 ods. 2 dates, the § 30 ods. 3
  zápis fields (porovnanie, posúdenie reálnosti ocenenia, signature) and totals.
- ``l10n.sk.inventurny.supis`` — fyzická or dokladová, with miesto uloženia,
  hmotne zodpovedná osoba and the person who established the actual state.
- ``l10n.sk.inventurny.supis.line`` carrying množstvo, jednotka and cena
  separately, per § 30 ods. 2 písm. e).
- Dokladová inventúra reads the account's ledger balance as at the deň ku
  ktorému (posted entries only), so the comparison is computed.
- Closing is refused without a súpis, and without the § 30 ods. 2 písm. i)
  signature on each súpis.
- QWeb reports for both the inventúrny súpis and the inventarizačný zápis.
- 8 tests.
