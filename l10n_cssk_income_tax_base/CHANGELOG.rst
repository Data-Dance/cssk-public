=========
Changelog
=========

All notable changes to **l10n_cssk_income_tax_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.5.5] — 2026-09-17
-------------------------

Fixed
~~~~~

- **An Administrator could not open it.** An accounting **Administrator**
  could reach the income-tax return list but could not open a return and hit
  *not allowed to access*. On Community, ``account.group_account_manager``
  does not imply ``account.group_account_user`` (and on Enterprise
  ``account_accountant`` only adds ``group_account_basic``), so a model
  granted to ``group_account_user`` alone is closed to an Administrator who
  lacks "Show Full Accounting Features". The return already granted it; its
  lines did not. ``group_account_manager`` now has the same access as
  ``group_account_user`` on ``cssk.income.tax.return.line``. Takes effect on
  module update.

[19.0.1.5.4] — 2026-09-16
-------------------------

Fixed
~~~~~

- Version bump only. 775995c changed the module's behaviour without moving its
  version, and downstream deployments track versions, so a module that changed
  behaviour under an unchanged version is its own defect.

  ⚠️ IT DOES NOT CARRY THE FIX, and the first version of this entry said it did.
  A field's ``context`` is never persisted: it is not among the parameters
  ``_reflect_field_params`` writes to ``ir.model.fields``
  (``odoo/addons/base/models/ir_model.py`` — field_description, help, ttype,
  relation, index, store, related, readonly, required, translate and the rest;
  no ``context``), and ``ir.model.fields`` has no such column. It is a plain
  Python attribute read off the class every time the registry is built.

  So **a pull and a restart** delivered 775995c to every database on that code,
  upgraded or not, with no ``-u`` and no version change. Boxes on the previous
  version were never at risk once the code was there. Said explicitly because
  the opposite reading costs somebody an ``-u`` across every database to fix
  something a restart had already fixed.

[19.0.1.5.3] — 2026-09-14
-------------------------

Fixed
~~~~~

- **Archiving a superseded vzor would have made old periods unenterable.** The
  ``version_id`` dropdown filtered archived records out, so a historical filing
  could not be created or re-pointed once its vintage was tidied away. The
  field now carries ``context={'active_test': False}``. The domain already
  scopes by period — a 2026 filing never sees the 2014 vzor regardless — so
  archiving stays a presentation decision rather than one that removes
  capability.

  ⚠️ As first written this did NOT work: the context was given as a STRING,
  ``context="{'active_test': False}"``. That is view-XML syntax; a field's
  ``context`` is a dict (``odoo/orm/fields_relational.py:38``,
  ``context: ContextType = {}``), and the string was passed through raw and
  ignored, so archived vintages stayed invisible in the dropdown. Corrected in
  775995c. This entry described the broken form as if it worked — the text
  above is repaired rather than left standing.

[19.0.1.5.2] — 2026-09-13
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

[19.0.1.5.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- ``_cssk_form_label`` was a bare Python string, so it was in no ``.pot`` at all
  — untranslatable in every language rather than merely untranslated. It is now
  a lazy translation (``_lt``), rendered in the reader's language, and the term
  is in the catalogue with its Slovak and Czech.

[19.0.1.5.0] — 2026-09-13
-------------------------

Added
~~~~~

- The statutory footprint now names the FILING each row belongs to, not just
  the form and the line code, so a reader can go and look at it. This module
  declares ``res_model`` in its footprint entries; ``l10n_cssk_core`` resolves
  it against the period. The key is optional in the contract — a contributor
  that omits it produces a row with a blank filing and nothing else changes.

[19.0.1.4.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- **The mixin's field labels reached the mixin and nothing else.** Odoo keeps
  one ``ir.model.fields`` row per CONCRETE model, so the translation of
  ``legacy`` — addressed to ``cssk.statutory.submission.mixin`` — landed there
  and on none of the six models that inherit it. A live instance showed a
  Slovak statusbar and an English ``Historical filing`` ribbon on the same
  record.
- ``--source`` could not see this: the string WAS in the template, addressed to
  one row out of seven. All seven mixin fields are now referenced per concrete
  model, with the Slovak and Czech already written for the mixin.

[19.0.1.4.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- **"Historical filing" was untranslatable, and it is the most visible label on
  a migrated filing.** It arrived with the ``legacy`` state and the templates
  were never regenerated, so the string existed in the source, in no ``.pot``
  and in no ``.po`` anywhere — 217 materialised filings on a live instance
  showed an English status on an otherwise fully Slovak form.
- It was not alone. Regenerating and diffing found **209 terms** across the
  statutory modules that exist in source and had never entered a template. A
  string missing from the TEMPLATE is invisible to coverage, to distinctness
  and to a fuzzy count alike, because all three compare a catalogue against its
  template — which is why the modules read as healthy.
- Merged additively rather than by regeneration: the committed templates carry
  terms a source-only export cannot see (menu and action names, view arch from
  data records), and replacing them destroyed 186 translations once already.
- Slovak and Czech filled for the new terms. ``Historical filing`` is
  **Historické podanie** / **Historické podání** — ``podanie`` is the statutory
  word for a filing made to the authority, and the sibling states already read
  Podané / Podáno.

[19.0.1.4.0] — 2026-09-12
-------------------------

Added
~~~~~

- ``("legacy", "Historical filing")`` on ``state``, and the list badge
  distinguishes it. Set automatically with the ``legacy`` flag — see
  ``l10n_cssk_core`` 19.0.1.9.0 for the reasoning and for why ``submitted``
  was the wrong value to reuse.

Fixed
~~~~~

- Buttons gated on ``state`` were written when ``legacy`` records sat in
  ``draft``, so the new value would have made some of them appear on a
  historical filing — Export XML, and the reconciliation / mapping indicators
  that count against a computation never run for one. Their conditions now
  name ``legacy`` alongside ``draft``.
- A post-migration moves existing historical filings onto the new state. Raw
  SQL, and not out of laziness: a write carrying ``state`` on a record that is
  already ``legacy`` is refused by ``_cssk_check_not_legacy``, which is exactly
  the guarantee the state exists to give, so the migration goes under it rather
  than around it.

[19.0.1.3.0] — 2026-09-10
-------------------------

Added
~~~~~

- **``cssk.income.tax.version._cssk_derived_codes()``** — which rows a country
  layer computes arithmetically. Returns an empty set here; the country layer
  answers it.

  ``kind`` names where a row's *input* comes from — the P&L (``account``), the
  asset register (``asset_diff``), or the accountant (``manual``) — and says
  nothing about whether the country layer then overwrites the row. On the
  Slovak DPPO nineteen rows are ``kind='manual'`` **and** derived, r310 and
  r400 among them, so a consumer asking "can I check this row?" could not
  answer it from ``kind`` and the answer lived only inside the country
  module's Python.

  A comparator against a filed return needs **three** states: rows we hold the
  input for, rows we derive (checkable arithmetically, but only where every
  input is held), and the accountant's judgment. Reporting the middle group as
  differences is how a comparison produces confident wrong answers that point
  at this engine.

  On the version rather than the return, so a bridge holding no computed
  record can reach it.

[19.0.1.2.4] — 2026-09-06
-------------------------

Fixed
~~~~~

- Tests wrote ``company.l10n_sk_dic`` directly while production
  feature-detects it with ``getattr`` — this module depends on neither
  ``l10n_sk_base`` nor anything that brings it, so the suite raised
  ``AttributeError`` on a CZ-only install, the one configuration the
  dependency list promises works. The tests mirror the production pattern now
  and assert the VAT half everywhere, the DIČ half where there is a DIČ.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.2.3] — 2026-07-04
-------------------------

Changed
~~~~~~~

- DPPO export consolidated onto the shared ``cssk.statutory.submission.mixin``
  pipeline (draft gate → preflight → kontroly → render → XSD validate → attach).

[2026-07-02] — Wave 2 (P1 robustness)
-------------------------------------

Added
~~~~~

- Filed-copy retention on submit and pre-export preflight
  (``_cssk_preflight_export``) before the DPPO XML is rendered.

[2026-07-01] — Wave 1 (P0 correctness)
--------------------------------------

Changed
~~~~~~~

- Line values rounded with ``statutory_round()`` (HALF-UP).

Fixed
~~~~~

- Multi-company leakage: ``ir.rule`` ``[('company_id','in',company_ids)]`` on the
  return model.

[2026-06-30] — i18n sweep & baseline
------------------------------------

Added
~~~~~

- Country-neutral framework for the corporate income-tax return (DPPO),
  mirroring the VAT-return / FS frameworks; CE-clean (``account`` only).
- ``cssk.income.tax.version`` + line definitions (``account`` = P&L result,
  ``aggregate`` = tax-computation spine, ``manual`` = accountant adjustments) +
  submission types.
- ``cssk.income.tax.return`` (mail.thread) — evaluator that auto-computes the
  accounting result and the formulaic spine, preserves manual overrides and feeds
  them into dependent aggregate lines on recompute, and produces XSD-validated
  statutory XML. Country layers (``l10n_sk_dppo`` …) supply the line set, header
  mapping and schema.
- Full cs_CZ + sk_SK translations.
