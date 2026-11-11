=========
Changelog
=========

All notable changes to **l10n_cssk_banks** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- ``base_bank_from_iban`` is no longer vendored in this repository: it comes
  from OCA ``community-data-files`` 19.0, which every deployment carries.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **Not ported.** ``l10n_cssk-18.0`` has no ``l10n_cssk_banks``; 18.0
  databases (and 16.0/17.0) keep ``l10n_banks_cz_sk`` from the datadance
  repository's own branches, with the 2023 data and its defects (``bank_8211``
  in both files, Fio SK ``FIOZSKBAX``). Porting needs ``base_bank_from_iban``
  18.0 vendored there, this module (hooks and migrations take ``env`` /
  ``(cr, version)``, as on 18.0) and ``tools/rename_banks_cz_sk.sh`` taught to
  accept series 18.

[19.0.2.0.0] — 2026-11-02
-------------------------

Changed
~~~~~~~

- **Moved from the datadance repository and renamed** from
  ``l10n_banks_cz_sk`` (19.0.1.0.0, 2023 data). xmlids are now per country,
  ``bank_cz_<code>`` / ``bank_sk_<code>``; ``tools/rename_banks_cz_sk.sh``
  carries an installed database across without touching any ``res.bank`` id.
- **Data regenerated from the official registries** by
  ``tools/gen_banks_cz_sk.py``: ČNB *Číselník kódů bank* (47 banks) and the NBS
  *Prevodník identifikačných kódov*, verzia 227 of 2026-11-02 (30 banks),
  both fetched 2026-11-02 and pinned in ``data/SOURCE_VERSION``.
- Names follow the registries (e.g. SK 6500 is now ČSOB's run-off code,
  formerly 365.bank / Poštová banka; SK 8400 is COFIDIS, not Banco Mais).

Added
~~~~~

- CZ: 2060, 2200, 2220, 6300, 6363, 6600, 6800, 8198, 8220, 8255, 8500, 8610,
  8620, 8660. SK: 8191, 8450, 9950, 9952, 9955, 9956.
- Registry sync on every version change: name, code, BIC and country follow
  the registry; banks that left it are archived, never deleted; an existing
  bank with the same code is adopted instead of duplicated.

Fixed
~~~~~

- **CZ 8211 resolved to nothing**: ``bank_8211`` (Saxo Bank) was in both data
  files under one xmlid. It is ``bank_cz_8211`` now — and archived, because
  ČNB no longer lists code 8211.
- **Fio banka SK BIC** was ``FIOZSKBAX`` (nine characters); it is ``FIOZSKBA``.
- Other BICs from the registry: CZ 4300 ``NROZCZPP`` (was ``CMZRCZP1``),
  CZ 8265 ``ICBKCZPP`` (was ``ICBKLUL``), SK 8370 ``OBKLSKBA`` (was empty).
  CZ 7960 and 8060 (building societies) carried their parent bank's BIC; the
  registry gives them none, so the shipped one is removed.

Removed
~~~~~~~

- No longer in the registries, archived on upgrade: CZ 3040, 4000, 4141, 5051,
  8211, 8231, 8241; SK 5200, 8050, 8170, 8380, 8440.
- The hand-collected addresses, phones and e-mails of 2023, which neither
  registry publishes — cleared on upgrade only where still unchanged.
