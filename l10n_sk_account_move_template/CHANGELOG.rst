=========
Changelog
=========

All notable changes to **l10n_sk_account_move_template** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the source are
  deliberately left untranslated — the source IS the translation, per the
  hybrid convention for these modules — so an empty ``msgstr`` there is correct
  rather than missing.

[19.0.1.0.1] — 2026-08-23
-------------------------

Changed
~~~~~~~

- **Renamed** to *SK Účtovné vzory — predkontácie interných dokladov*. The old name,
  *SK Predkontácie (účtovné vzory)*, promised the POHODA / ABRA Gen meaning of the word —
  a predkontácia selected **on a document**, driving its zaúčtovanie. The engine has no
  link to any document (``account_move_template`` never touches ``account.move`` except to
  ``create()`` one), so the module covers only the *interný doklad* slice. The manifest
  description and the README now state that limit first and point at the Odoo objects that
  actually decide invoice, bank and cash postings.
- README usage section corrected: the templates list is under *Konfigurácia ▸ Účtovníctvo*,
  not directly under Účtovníctvo, and the posting wizard has its own menu
  (*Vytvoriť zápis podľa vzoru*). Both menu paths were wrong before.
- Filled the Slovak and Czech translation catalogues of the vendored
  ``account_move_template`` (57 + 8 SK entries, 54 + 8 CZ; upstream shipped them empty), so
  the menus a Slovak or Czech accountant navigates are no longer English. Only the formula
  examples and the stray ``&gt;`` are left untranslated, deliberately.

[19.0.1.0.0] — 2026-08-05
-------------------------

Added
~~~~~

- Baseline: Slovak *predkontácie* on the OCA journal-entry template engine
  (``account_move_template``), delivered as ``account.move.template`` records on the
  ``l10n_sk`` chart.

- Starter set:

  - výber z pokladnice (261/211)
  - príjem na bankový účet (221/261)
  - výber z bankového účtu (261/221)
  - vklad do pokladnice (211/261)
  - preúčtovanie schváleného zisku (431/428)
  - preúčtovanie schválenej straty (429/431)

- One-amount postings — line 1 is user input, further lines compute from it via ``L1``.
- Names shipped in Slovak: ``account.move.template.name`` is not translatable and the chart
  loader's ``@lang`` mechanism covers only ``TEMPLATE_MODELS`` (and strips ``@`` keys at the
  top level only, so one nested in a ``Command.create`` payload would raise).
- New companies get the templates from the chart template; existing SK companies via a
  sudo post-init hook that reuses ``_load_data`` so the xmlids match either way.
- The hook loads only templates the company lacks. ``_load_data`` calls ``_load_records``
  without ``update=True`` and ``noupdate`` only applies on a module upgrade, so an existing
  record is always rewritten and the ``Command.create`` line payloads append a duplicate of
  every line — which violates the ``(sequence, template_id)`` unique constraint and would
  revert accountant edits. Both failure modes are covered by tests (and negative-tested).
- AGPL-3 (depends on the AGPL OCA engine).
