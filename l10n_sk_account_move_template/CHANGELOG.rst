=========
Changelog
=========

All notable changes to **l10n_sk_account_move_template** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

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
