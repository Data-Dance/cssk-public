=========
Changelog
=========

All notable changes to **l10n_cz_kh** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **19.0.1.6.6 (2026-09-21), not yet on 18.0.** The resolver reads a
  cash-basis entry through ``_cssk_vat_document`` (commit 02eda35); ports with
  the ``l10n_cssk_kv_kh_base`` change it depends on.

[19.0.1.6.6] — 2026-09-21
-------------------------

Fixed
~~~~~

- **Cash-basis entries are classified by the document they settle.** Shares
  the ``l10n_cssk_kv_kh_base`` fix: a tax "Based on Payment" no longer puts an
  unpaid document into the KH, and Odoo's cash-basis entry is read with the
  settled document's type and partner instead of as a partnerless entry. The
  upgrade re-resolves the affected lines.

[19.0.1.6.5] — 2026-09-17
-------------------------

Fixed
~~~~~

- **An Administrator could not open it.** An accounting **Administrator**
  could reach a control statement (KH DPH) but not its sections and hit *not
  allowed to access*. On Community, ``account.group_account_manager`` does not
  imply ``account.group_account_user`` (and on Enterprise
  ``account_accountant`` only adds ``group_account_basic``), so a model
  granted to ``group_account_user`` alone is closed to an Administrator who
  lacks "Show Full Accounting Features". The control statement already granted
  it; the section models did not. ``group_account_manager`` now has the same
  access as ``group_account_user`` on the sections A.1–A.5 and B.1–B.3. Takes
  effect on module update.

[19.0.1.6.4] — 2026-09-17
-------------------------

Fixed
~~~~~

- **A statement computed on existing accounting came out empty.** Every line's
  control section was computed when ``l10n_cssk_kv_kh_base`` installed, before
  this module's resolver was loaded, and nothing recomputed it afterwards — so
  on a database with history every line kept no section and the statement
  had nothing to populate, with no error. The install hook now recomputes the
  section on all posted lines of the CZ companies, and the upgrade to
  19.0.1.6.4 repairs databases that were already installed.

[19.0.1.6.3] — 2026-09-13
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

[19.0.1.6.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Terms the translation catalogue never carried.** Strings that reach the
  user were absent from the template — a field with no ``string=``, a mixin
  field addressed to the abstract model's ``ir.model.fields`` row rather
  than each concrete one, or a whole category the offline exporter never
  emitted. An absent term cannot be translated and shows English in an
  otherwise Czech screen. The template and the catalogues now carry them,
  and the Czech is written.

[19.0.1.6.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- The same pre-migration collapse and post-migration assertion as the
  Slovak side. Expected to be a no-op here — the Czech types always had
  xmlids on a single version — which is precisely why it is worth
  asserting rather than assuming.

[19.0.1.6.0] — 2026-09-12
-------------------------

Changed
~~~~~~~

- The three type records (``cz_kh_type_B`` / ``_O`` / ``_E``) point at
  ``country_id`` instead of ``version_id``. Their xmlids are unchanged, so
  they are updated in place and nothing here needs remapping — see
  ``l10n_cssk_kv_kh_base`` 19.0.2.0.0.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.1.1] — 2026-08-14
--------------------------

Fixed
~~~~~

- Section rows were selected by a raw accounting-date range instead of the
  shared period helper, so the control statement could disagree with the VAT
  return it reconciles against — in particular over a deduction claimed in a
  later period than the bill was booked.

[19.0.1.0.4] — 2026-07-14
-------------------------

Fixed
~~~~~

- Received-document sections **A.2, B.1, B.2** now export the supplier's evidence
  number (``move.ref``) as ``c_evid_dd`` instead of our internal move name — KH §101c
  requires the number as stated by the supplier. Issued sections (A.1, A.4) keep our
  own number.
- Detail rows now report DUZP from ``taxable_supply_date`` when set (e.g. advance tax
  documents: the payment date), falling back to the invoice date as before.

[19.0.1.0.3] — 2026-07-04
-------------------------

Changed
~~~~~~~

- Now inherits the shared ``cssk.control.statement.section.mixin`` — removed ~55 lines of
  duplicated section-classification code; the A5/B3 aggregate rows now carry their source
  detail lines. (Wave 3)
- Adopted ``normalize_vat()`` from ``l10n_cssk_core`` for DIČ handling.
- Manual section overrides now survive a recompute (snapshot/re-apply). (Wave 3)

[2026-07-02] — Wave 2 (robustness)
----------------------------------

Added
~~~~~

- Pre-export preflight checks (``_cssk_preflight_export``) before the DPHKH1 XML is generated.

Changed
~~~~~~~

- Locked filed copy retained on submit (filed-history integrity).

[2026-07-01] — Wave 1 (correctness)
-----------------------------------

Changed
~~~~~~~

- Statutory rounding unified to HALF-UP (``statutory_round()``/``statutory_whole()``).
- Multi-company ``ir.rule`` (``company_id in company_ids``) added so control statements no longer
  leak across companies.

Fixed
~~~~~

- EPO Pisemnost/DPHKH1 XML: empty attributes now emitted as ``None`` (omitted) instead of ``""``
  (XSD-invalid).

[2026-06-30] — Baseline & i18n
------------------------------

Added
~~~~~

- Czech VAT control statement (Kontrolní hlášení / DPHKH1) on ``l10n_cssk_kv_kh_base``:
  per-document A1–B3 sections with the 10 000 CZK split (A4/B2 detail vs A5/B3 aggregates),
  reverse-charge supplies/acquisitions to A1/B1, EU acquisitions to A2.
- EPO Pisemnost/DPHKH1 XML export (VetaD/VetaP, per-document VetaA1/A2/A4/B1/B2 rows, VetaA5/B3
  aggregates, VetaC control totals), validated against the official DPHKH1 XSD
  (``data/dphkh1_epo2.xsd``, ``schema.assertValid``).
- cs_CZ jsonb translations (i18n sweep).
