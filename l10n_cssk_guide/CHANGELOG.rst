=========
Changelog
=========

All notable changes to **l10n_cssk_guide** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.1.1.0] — 2026-11-04
-------------------------

Added
~~~~~

- Task guides: how to get a job done across Odoo's own modules, the OCA
  modules we ship and ours, written for a Slovak or Czech accountant
  (Community edition). They are listed first under their topic on the Guides
  page, filtered by country like the module guides, and served from
  ``static/guides/``. The first one is *Management reports with MIS Builder*.
  Sources are ``guide/workflows/<key>/<lang>.md``, rendered by
  ``tools/gen_module_docs.py``.
- Screenshots in the task guides, one set per language (the Slovak screen
  on the Slovak page), kept in ``static/guides/<key>/img/``.

[19.0.1.0.0] — 2026-10-29
-------------------------

Added
~~~~~

- Initial release. *Accounting → Configuration → Guides* opens the start
  page of the user guide: the first steps, then the guide of every Czech and
  Slovak localization module on the server, by topic, installed ones first,
  filtered to the company's country, in English, Slovak or Czech. The text
  is generated from ``guide/`` by ``tools/gen_module_docs.py``; the page
  finds the modules by the topic stamped on their guide pages, so it covers
  every delivery repository on the server.
