=========
Changelog
=========

All notable changes to **l10n_sk_tax_report_backport** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Added
~~~~~

- **Fiscal-position tax auto-substitution** (19.0 invoice-side parity). 18.0's
  tax template does not support the 19.0 ``fiscal_position_ids`` /
  ``original_tax_ids`` columns, so the same domestic→counterpart swaps are
  produced with classic ``account.fiscal.position.tax`` mapping records via a
  new ``@template('sk', 'account.fiscal.position')`` method
  (``_get_sk_tax_report_backport_fiscal_positions``):

  - *EU intra-community B2B* (``fiscal_position_template_2``): domestic services
    → ``vy_eu_s``, domestic goods → ``vy_eu_m``, domestic purchases →
    ``vs_nad_eu_23`` / ``vs_nad_eu_19`` / ``vs_nad_eu_5``. This **replaces** the
    stale pre-19.0 mappings 18.0 core shipped (``vy_dod_eu`` / ``vs_nad_eu``).
  - *Export outside the EU* (``fiscal_position_template_3``): created here (18.0
    core does not ship it) — every domestic sale rate/scope → ``vy_mimo_eu``.
  - *Domestic / EU-private B2C* (``fiscal_position_template_1`` /
    ``fp_intra_private``): the generic rate → its goods (``_m``) variant.

- **Invoice legal notes** on the three intra-EU sale taxes (``vy_eu_s`` §196,
  ``vy_eu_m`` §138, ``vy_eu_t`` §141 of Directive 2006/112/EC) via a new
  ``@template('sk', 'account.tax')`` method — matching the only taxes 19.0
  populates ``invoice_legal_notes`` on.

Notes
~~~~~

- 18.0's ``account.tax.invoice_legal_notes`` exists but, unlike 19.0, is **not**
  ``translate=True``. Only the English base value is stored/printed; the ``@sk``
  variant is supplied for faithfulness to the 19.0 row but is inert on 18.0
  (the chart-template translation pass only handles translatable fields).

[18.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Initial release. Backports the Odoo 19.0 core ``l10n_sk`` VAT tax template
  and DPH report-tag set onto the 18.0 ``l10n_sk`` chart:

  - 53 DPH report tags (``account.account.tag``, codes 01..29 + lettered
    sub-codes + 24_PR) with stable XML-IDs ``tag_sk_<code>``.
  - The 5 % VAT tax group ``tax_group_vat_5`` (absent from 18.0).
  - 43 VAT taxes (adapted from the 19.0 ``account.tax-sk.csv``) bound to their
    DPH tags via ``@template('sk', 'account.tax')`` — 38 new (5 % rate,
    service/goods scope, reverse charge, intra-EU acquisition, triangular,
    import postponed, customs, bad-debt, § 53b unpaid, special regime) plus
    the 5 taxes 18.0 already ships (repartition replaced to add tags).
  - The two 18.0-only legacy taxes ``vy_dod_eu`` / ``vs_nad_eu`` kept tagged.

- Consolidates the minimal tag backport that previously lived in
  ``l10n_sk_vat_return`` (``data/sk_vat_tax_tags.xml`` + an inline
  ``@template`` binding) into this single source of truth.

Notes
~~~~~

- The 19.0 on-screen tax report (``account.report``) is intentionally not
  loaded — see README (it would auto-create a duplicate +/- tag set, and the
  CE-clean statutory filing does not use it).
