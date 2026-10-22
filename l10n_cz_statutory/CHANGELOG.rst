=========
Changelog
=========

All notable changes to **l10n_cz_statutory** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a
Changelog. The ``19.0.x.y.z`` sections below are the 19.0 series' history,
kept verbatim: this branch reached 1.3.0 by one port rather than by those
releases, and the entries are what the port brought over.

[Unreleased]
------------

[18.0.1.3.0] — 2026-10-19
-------------------------

Added
~~~~~

- **``account.move.l10n_cz_bad_debt``** and the statutory-submission hooks that
  read it (``models/account_move.py``, ``models/cssk_statutory_submission.py``,
  ``views/account_move_views.xml``). The flag decides which DPHDP3 row and
  which KH section a document lands on, so it is readonly once posted.

  Ported because ``l10n_cz_kh`` is written against it: without the field 18 of
  its 34 tests errored at ``'account.move' object has no attribute
  'l10n_cz_bad_debt'``, which is every test it has that touches a bad debt.

- **Dependency added: ``partner_nace``**, as on 19.0. Already vendored on this
  branch at 18.0.1.0.0, so nothing new has to be obtained.

Changed
~~~~~~~

- **Merged, not copied, for the second time in this module.** This branch keeps
  four files 19.0 does not have — ``models/l10n_cz_tax_office.py``,
  ``data/l10n_cz.tax_office.csv``, its ACL row, and the
  ``res.company.l10n_cz_tax_office_id`` declaration in ``models/res_company.py``
  — because Odoo core added ``l10n_cz.tax_office`` to ``l10n_cz`` in 19.0 and
  the 19.0 copy of this module therefore READS the field without declaring it.
  Copying 19.0 over this module would delete the whole back-port and take
  ``c_pracufo`` off every CZ statutory report with it, silently.

  Verified after the merge rather than assumed: 214 tax offices load,
  ``res_company.l10n_cz_tax_office_id`` and ``account_move.l10n_cz_bad_debt``
  both exist, and the new view's two anchors
  (``//page[@id='other_tab']//group[@name='accounting_info_group']``) each
  resolve exactly once in 18.0's ``account.view_move_form``.

Added
~~~~~

- **The EPO filer identity on ``res.company``**, ported from 19.0: the fourteen
  ``l10n_cz_epo_*`` fields (natural person, signatory, preparer, agent) with
  their helpers, and the ``res_company_view_form_cz_epo_filer`` page that
  ``l10n_cz_epo`` extends. Without it ``l10n_cz_epo`` cannot install — its view
  inherits an xmlid that did not exist here.

  **Merged, not copied.** This file declares
  ``res.company.l10n_cz_tax_office_id``, which 19.0 only READS because Odoo core
  added it to ``l10n_cz`` in 19.0. Copying 19.0's file over this one would have
  silently dropped that back-port and with it ``c_pracufo`` on every CZ
  statutory report. The field now carries a comment saying so.

  Still behind 19.0 after this: ``models/account_move.py``,
  ``models/cssk_statutory_submission.py`` and ``views/account_move_views.xml``
  are 19.0 content this does not bring, because ``l10n_cz_epo`` does not need
  them. 18.0.1.1.0 is the EPO-filer slice, not full parity with 19.0.1.3.0.

[19.0.1.0.3] — 2026-07-04
-------------------------

Fixed
~~~~~

- Fresh-install crash fixed: the finanční-úřad seed hook no longer fails on databases without
  the ``cs_CZ`` res.lang — the office name language is guarded (``cs_CZ`` if active, else the
  default). (Wave 1)

[2026-06-30] — Baseline & i18n
------------------------------

Added
~~~~~

- Czech statutory reference data for the country-neutral registries in ``l10n_cssk_core``:
  ``cssk.tax.authority`` (regional finanční úřady, c_ufo codes seeded from the official
  ``l10n_cz.tax_office`` codelist plus the Specializovaný finanční úřad) and ``cssk.person.type``
  (FO / PO taxpayer types).
- cs_CZ jsonb translations (i18n sweep).
