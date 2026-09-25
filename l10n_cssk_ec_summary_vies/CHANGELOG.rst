=========
Changelog
=========

All notable changes to **l10n_cssk_ec_summary_vies** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.4] — 2026-09-13
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

[19.0.1.0.3] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Terms the translation catalogue never carried.** Strings that reach the
  user were absent from the template — a field with no ``string=``, a mixin
  field addressed to the abstract model's ``ir.model.fields`` row rather
  than each concrete one, or a whole category the offline exporter never
  emitted. An absent term cannot be translated and shows English in an
  otherwise Slovak or Czech screen. The template and the catalogues now carry them,
  and the Slovak or Czech is written.

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

- Export-time VIES check hardened alongside the direct-VIES base: a transient
  VIES outage no longer blocks the statutory filing (it is logged in the
  statement chatter for a repeat), while a VAT that VIES reports **invalid** stays
  a hard block on export.
- Snapshot re-apply: the consultation number, check timestamp and validity are
  frozen onto each reported line, so re-opening a filed statement shows exactly
  what was confirmed.

[2026-06-30] — i18n sweep & baseline
------------------------------------

Added
~~~~~

- Glue module (auto-install) linking ``l10n_cssk_ec_summary_base`` ×
  ``l10n_cssk_vies``: makes the EC sales list export perform a **real** direct-VIES
  check (not just a format gate) for companies in direct-VIES mode and snapshot
  the official consultation number onto each line.
- Full cs_CZ + sk_SK translations.
