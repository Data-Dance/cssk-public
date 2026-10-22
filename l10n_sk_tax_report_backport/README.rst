=================================================================
Slovakia — VAT Tax Template + Report Tags (18.0 backport of 19.0)
=================================================================

Backports the full **Odoo 19.0 core** ``l10n_sk`` VAT tax template and DPH
report-tag set onto the smaller **18.0** ``l10n_sk`` chart, bringing 18.0 SK to
VAT parity with 19.0.

Why
===

18.0 CE ``l10n_sk`` ships only **7** taxes and **no** tax tags / tax report. The
DPH report-tag set (codes 01..29 + lettered sub-codes) and the extended tax
template — 5 % rate, service/goods scope, reverse charge (§ 69), intra-EU
acquisition (§ 11), triangular trade, import with postponed accounting (§ 84a),
customs-paid VAT, bad-debt adjustment, § 53b unpaid-invoice correction and the
special regime — were only added to CE ``l10n_sk`` in **19.0**. Without them,
every ``kind='tags'`` line in the SK VAT return / kontrolný výkaz / súhrnný výkaz
evaluates to 0, and the RC / intra-EU auto-flagging hooks find no taxes to flag.

What it does
============

* Creates **53 DPH report tags** (``account.account.tag``, applicability
  ``taxes``, country SK) with stable XML-IDs ``tag_sk_<code>``
  (``data/account_tax_report_tags.xml``). Only the ``+`` sign of each code is
  created — our evaluator resolves a code via ``=like '_<code>'`` (either sign)
  and encodes the display sign in the version-data formula.
* Creates the **5 % VAT tax group** (``tax_group_vat_5``), absent from 18.0.
* Backports **43 VAT taxes** (adapted from the 19.0 ``account.tax-sk.csv``) via
  ``@template('sk', 'account.tax')``, each bound to its DPH tags. The 5 taxes
  18.0 already ships have their repartition replaced to add tags; the 38 missing
  ones are created. The two 18.0-only legacy taxes (``vy_dod_eu``,
  ``vs_nad_eu``) are also kept tagged.
* **Invoice legal notes** (EU directive articles: § 196 reverse charge, § 138
  intra-community supply, § 141 triangular) on the intra-EU sale taxes, printed
  on the invoice — matching 19.0.
* **Fiscal-position tax auto-substitution** (invoice-side parity). 19.0 declares
  this on ``account.tax`` (``fiscal_position_ids`` / ``original_tax_ids``, fields
  that do not exist on 18.0); we reproduce it with classic
  ``account.fiscal.position.tax`` mapping records:

  - Domestic / EU-private: generic rate -> its goods-scoped ``_m`` variant.
  - EÚ intra (B2B): services -> ``vy_eu_s``, goods -> ``vy_eu_m``, purchases ->
    ``vs_nad_eu_{23,19,5}`` (replacing the base chart's mapping to the legacy
    ``vy_dod_eu`` / ``vs_nad_eu``).
  - Export outside the EU: a new ``fiscal_position_template_3`` mapping every
    domestic sale to the 0 % export tax ``vy_mimo_eu`` (a no-country/no-group
    auto-apply fallback that never outranks the domestic/intra-EU positions).

Any SK company's chart is augmented on install, so posted moves carry the tags
the CE-clean SK VAT/KV/EC evaluators read — and ``l10n_sk_kv_dph`` /
``l10n_sk_ec_sales`` can flag the ``vs_rc_*`` / ``vs_nad_eu_*`` / ``vy_eu_*``
taxes exactly as on 19.0.

18.0 mechanics
==============

* Tag references in the ``@template`` data are **XML-IDs**, not bare names.
  18.0's ``_deref_account_tags`` runs only on the CSV parsed by core's
  None-code loader, not on data returned by ``@template`` methods, so a bare
  name would reach ``_load_data.deref_values`` and crash as
  ``account.<company>_<name>``.
* The ``@template('sk', 'account.tax')`` methods run in the ``sk`` pass, after
  core parses the base ``l10n_sk`` CSV, so their data merges on top.

On-screen tax report: skipped
=============================

The 19.0 on-screen Odoo SK tax report (``account.report`` from
``data/tax_report.xml``) is **not** loaded, deliberately:

* Its ``tax_tags`` expressions would auto-create their own ``+``/``-`` tag pairs
  on install — a second, uncontrolled tag set colliding by name with the
  XML-ID'd tags this module creates and references.
* Those auto-created tags have no stable XML-ID to reference from ``@template``
  tax data.
* Our statutory filing (``l10n_sk_vat_return`` / ``_kv_dph`` / ``_ec_sales``) is
  CE-clean and reads ``account.account.tag._get_tax_tags``, **not** the
  ``account.report`` / ``account_reports`` engine — so the UI report is not
  needed for parity.

The tags and tax bindings (the load-bearing part) are fully backported; only the
optional on-screen report view is out of scope.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

Tax template + tag data adapted from Odoo 19.0 core ``l10n_sk`` (LGPL-3).

License: LGPL-3 (see the LICENSE file).
