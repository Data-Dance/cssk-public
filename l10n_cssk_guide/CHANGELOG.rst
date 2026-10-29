=========
Changelog
=========

All notable changes to **l10n_cssk_guide** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

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
