=========
Changelog
=========

All notable changes to **l10n_sk_ec_sales** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.2.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Code translations that Odoo was never loading.** An entry whose references
  are ``code:addons/...`` is treated as a Python translation only if it carries
  the extracted comment ``#. odoo-python`` — ``_load_python_translations``
  filters on exactly that and never on the reference. Without it an entry can
  name the right ``.py``, carry a correct msgstr, pass ``msgfmt --check``, and
  be silently ignored for ever. This module's hand-added entries were in that
  state. Repaired by ``tools/fix_po_code_comments.py``, which is also the CI
  check; the offline exporter now emits the comment itself.

[19.0.1.2.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Terms the translation catalogue never carried.** Strings that reach the
  user were absent from the template — a field with no ``string=``, a mixin
  field addressed to the abstract model's ``ir.model.fields`` row rather
  than each concrete one, or a whole category the offline exporter never
  emitted. An absent term cannot be translated and shows English in an
  otherwise Slovak screen. The template and the catalogues now carry them,
  and the Slovak is written.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **The 2010 Súhrnný výkaz vzor (19.0.1.2.0) is owed to 18.0.** The vintage
  split is a fact about Finančná správa, not about Odoo: ``svdph2010.xsd``
  covers 2010-2019 and ``svdph20.xsd`` 2020 onwards, and the module on 18.0
  ships only the later one over the whole span. A pre-2020 period there is
  filed in a structure that did not exist then — 12+12 records to a page
  against the 27 the vzor wants. Port the schema, the ``sdv_2010`` template,
  the version record and the migration that narrows the existing one; all four
  are Odoo-version-independent.

[19.0.1.2.0] — 2026-09-09
-------------------------

Added
~~~~~

- **The 2010 vzor.** FS SR publishes one XSD per vintage and keeps the old
  ones, so a period is filed in the structure in force AT THE TIME. This
  module shipped only ``svdph20.xsd`` and offered it back to 2010, which
  would have filed a 2019 period in a structure that did not exist then.
  ``svdph2010.xsd`` and its own template now cover 2010-01-01 – 2019-12-31.

  What separates the two is the Quick Fixes (smernica 2018/1910, § 8a zákona
  o DPH) from 1. 1. 2020: the SV gains the call-off-stock register
  (``zaznamCast2``) and the page goes from 27 records to 12 + 12. The earlier
  vzor also carries ``oznacenie`` and ``pocet2Stran`` and a structured fax,
  none of which survive into 2020. Same root element in both, so nothing in
  the document tells you which one you are holding.
- ``data/SCHEMA_VERSION`` pinning both schemas by size and digest, both
  verified byte-identical against the published copies on 2026-09-09, with a
  test that no bundled schema sits unpinned. Neither file can prove it is
  current: ``svdph2010.xsd`` carries no vintage and no revision at all, and
  ``svdph20.xsd`` stamps a vintage only.

Changed
~~~~~~~

- The existing version record is narrowed to 2020-01-01 and renamed. It lives
  in a ``noupdate="1"`` file, so a migration does it — without one an existing
  database keeps a version claiming 2010 onwards, and a 2014 period resolves
  to BOTH vintages.

Documented
~~~~~~~~~~

- ``readme/ROADMAP.rst``: what the dodatočný / opravný súhrnný výkaz does and
  does not do today. The type flags and the amendment link work; there is no
  correction machinery, and ``svdph20.xsd`` gives a supply record no place to
  put one — so filing the full recomputed period is probably right, but that
  reading needs confirming against the poučenie rather than the schema alone.
  Nothing in the suite exercises an amendment, which is why the question had
  not come up.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.2] — 2026-07-04
-------------------------

Changed
~~~~~~~

- Manual overrides on EC-summary lines now survive recompute (snapshot/re-apply) (Wave 3).
- Export pipeline consolidated into the shared ``cssk.statutory.submission.mixin``; kontroly now run before render.

[2026-07-01] — Wave 1 (P0 correctness)
--------------------------------------

Fixed
~~~~~

- Multi-company leak closed with an ``ir.rule [('company_id','in',company_ids)]``.

Changed
~~~~~~~

- Statutory rounding unified on ``statutory_round()`` (HALF-UP).

[2026-06-30] — Initial baseline
-------------------------------

Added
~~~~~

- Slovak Súhrnný výkaz (EC sales list) on ``l10n_cssk_ec_summary_base``: transaction codes **0** = goods (dodanie tovaru), **1** = triangulation (trojstranný obchod), **2** = services (dodanie služby), driven by ``account.tax.cssk_ec_summary_code``.
- FS SR ``SDV`` XML export (QWeb template + stand-in XSD; replace with the official schema before live filing). CE-clean (no ``account_reports``).
- sk_SK translations (Odoo 19 jsonb) as part of the localization i18n sweep.
