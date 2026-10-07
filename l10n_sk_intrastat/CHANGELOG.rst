=========
Changelog
=========

All notable changes to **l10n_sk_intrastat** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.0] — 2026-10-03
-------------------------

Fixed
~~~~~

- **Supplementary units are filed by their official code.** OCA names eight
  units differently from the Eurostat codes (``items`` for ``p/st``,
  ``1000 kWh`` for ``1 000 kWh``, …), and the adapter filed the name.
  ``SUCode`` now carries the code, spelled as Odoo Enterprise's
  ``account_intrastat`` spells it, so both editions file the same unit.
- **Mode of transport and delivery terms are filed.** A full declaration
  carries ``modeOfTransportCode`` and ``TODCode`` on every item. The engine
  has both, and this adapter wrote neither.
- The nature of transaction now reaches INSTAT as its A and B codes, via
  ``l10n_cssk_intrastat_base`` 19.0.1.1.0. It used to be one A code, ``11``.
- The description said the shared renderer is LGPL-3. It is AGPL-3, and the
  Enterprise variant reuses it under dual licensing.

[19.0.1.0.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the source are
  deliberately left untranslated — the source IS the translation, per the
  hybrid convention for these modules — so an empty ``msgstr`` there is correct
  rather than missing.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Baseline: INTRASTAT-SK country layer on the OCA ``intrastat_product`` 19.0 declaration engine (CE-clean). The engine collects intra-EU goods movements and computes the grouped declaration lines; this module renders them as the official Finančná správa INTRASTAT-SK **INSTAT (instat62)** XML via ``l10n_cssk_intrastat_base``.
- AGPL-3 (subclasses the AGPL OCA engine); the shared INSTAT renderer is LGPL-3 so the EE variant can reuse it without inheriting AGPL.
