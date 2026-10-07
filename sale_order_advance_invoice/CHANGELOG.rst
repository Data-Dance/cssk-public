=========
Changelog
=========

All notable changes to **sale_order_advance_invoice** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.2.7.1] — 2026-09-30
-------------------------

Fixed
~~~~~

- On a fresh database where the chart and this module are installed in one
  run, loading the chart deletes the company's journals, the new TDADV
  included, and left the module's journal xmlid pointing at nothing. After
  every chart load the xmlid is re-adopted if it dangles.

[19.0.2.7.0] — 2026-09-29
-------------------------

Fixed
~~~~~

- **Upgrade failed where a TDADV journal already existed without the module's
  xmlid** (``duplicate key value violates unique constraint
  account_journal_code_company_uniq``; found on a customer's database, where a localization
  helper had created it). The journal is no longer a data record: a function run
  on every install and upgrade adopts the company's existing TDADV journal, or
  creates it, and gives it the xmlid. A live xmlid is left alone.

Tests
~~~~~

- The lump-sum characterisation asserted 105, which holds only for a 15 %
  default rate (no chart); on the CZ and SK charts it failed before 19.0.2.6.0
  too. It now states the rule: the deduction gives back the advance's VAT and
  the final invoice settles the difference to the order's VAT.
- The foreign-currency tests set the DUZP as well: with ``l10n_cz`` the rate is
  the DUZP's (§ 38 ZDPH), which defaults to today.
- Run on both a CZ-chart and an SK-chart database.

[19.0.2.6.0] — 2026-09-29
-------------------------

Fixed
~~~~~

- **A foreign-currency advance is deducted at the rate its VAT was declared
  at.** The tax document for a received advance declares its VAT in CZK at
  the rate of its own date (§ 38 ZDPH); the final invoice gave it back at the
  final invoice's rate, so the return reversed a different amount than it had
  declared. The deduction now uses the rate of the advance's posted tax
  documents, and the part of the supply the advance paid for is valued at
  that rate too (a received advance is a non-monetary item). Only the
  uncovered remainder is converted at the invoice's rate, so a fully covered
  supply nets to zero VAT and leaves nothing on the receivable in either
  currency. A posted invoice keeps the rates it was booked at.
- **A single-rate advance was deducted at the advance product's default
  tax, not the tax it charged.** A 21 % advance deducted at 15 % billed the
  customer the difference again. The deduction now carries the advance's own
  taxes; advances at several rates were already split per rate.

Known limitation
~~~~~~~~~~~~~~~~

- A credit note of such a final invoice is valued at its own rate.
- An advance without a tax document (no VAT) is still deducted at the final
  invoice's rate.

[19.0.2.5.3] — 2026-09-13
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

[19.0.2.5.2] — 2026-09-13
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

[19.0.2.5.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- **The Slovak catalogue was a third done, and two ACTIONS were among the
  missing.** *Register Payment* and *Link Manual Transfer* rendered English in
  a Slovak UI — the first of them translated perfectly well in the sibling
  purchase module. Slovak now covers 179 of 179.

- Worth recording because it is a hole in how this was being measured: an entry
  with an empty ``msgstr`` is neither translated nor a duplicate, so BOTH
  quality checks applied to this file were blind to it. It read 57 translated /
  57 distinct, zero fuzzy — a clean bill from every metric — while 122 entries
  were simply absent. Coverage finds what is missing; distinctness finds what
  is wrong. ``tools/check_translation_quality.py`` now reports both.

[19.0.2.5.0] — 2026-09-13
-------------------------

Fixed
~~~~~

- **The Czech catalogue had the same class of defect as the Slovak one**, and
  19.0.2.4.0 did not look at it. Three strings reused across labels that are
  not the same thing:

  - ``Bank Account`` carried ``Číslo účtu``, the translation of
    ``Account Number`` — two different fields on two different reports;
  - ``Invoice Date`` and ``Issue Date`` both carried ``Datum vystavení``, and
    they appear on the SAME invoice report, so one of them was mislabelled on
    screen. ``Datum vystavení`` is precisely the issue date and stays there;
    the invoice date becomes ``Datum faktury``;
  - ``Sales Advance Payment Invoice`` (a model name) carried the same string as
    the ``Advance Invoice`` field label. Slovak already distinguished these two,
    which is what showed the Czech was wrong rather than merely terse.

  ``Fixed Amount`` / ``Fixed amount`` still share a translation. That one is a
  case difference in the SOURCE and is harmless.

- The three Czech mail-template bodies are verified translated — fluent Czech
  prose inside the same HTML scaffolding — and their ``#, fuzzy`` flags are
  cleared. Comparing the raw strings makes a correct mail translation look like
  an untranslated copy, because the markup is identical by design; the prose
  has to be compared on its own.

Added
~~~~~

- The four report labels above are now translated in Slovak too, where they had
  been left empty: account number, bank account, invoice date, issue date.

Notes
~~~~~

- Both catalogues now carry **no fuzzy entries at all**. Slovak is 57
  translated / 57 distinct, Czech 99 / 98 with the one harmless pair.

[19.0.2.4.0] — 2026-09-13
-------------------------

Fixed
~~~~~

- **The Slovak catalogue was not merely thin, it was WRONG, and Odoo was
  serving it.** Three mail-template names had been smeared across every message
  containing "Advance Invoice" — one Slovak string on ten different msgids,
  another on six, another on four — plus one message carrying a different
  message's translation. 18 entries in all. A menu reading
  *"Predaj: Odoslať zálohovú faktúru"* opened a LIST of advance invoices, and a
  button with the same label created one.

  **The mechanism is the ``#, fuzzy`` flag**, which is what ``msgmerge`` writes
  when it GUESSES a translation from a similar string — and
  ``PoFileReader.__iter__`` skips only ``obsolete`` entries, never fuzzy ones.
  So a machine guess loads into the database and reaches the screen exactly
  like a human translation. Worth knowing before the next ``msgmerge``: in this
  repository a fuzzy entry is live text, not a draft.

  The 18 are rewritten from the source strings and their flags cleared. The
  ~35 entries that were sound — three full mail bodies and the account help
  texts, with correct chart references (475 / 324) — are untouched; they are
  careful human work and the vocabulary for the rewrite was taken from them
  rather than invented.

- ``Advance Invoices Journal`` and ``Advance Tax Documents Journal`` collapsed
  to one string in BOTH languages, so two different journals displayed the same
  name. Now distinct in Slovak and Czech.
- Czech ``Journal Item`` was translated as ``Účetní záznam`` — the same as
  ``Journal Entry``. Corrected to ``Účetní položka``.
- The committed ``.mo`` files are regenerated to match. They are build
  artefacts under version control, which is worth revisiting; Odoo does not
  read them.

Notes
~~~~~

- The Slovak catalogue now carries **no fuzzy entries at all** (53 translated).
  Czech keeps three, on mail-template bodies that have not been read here —
  clearing a fuzzy flag asserts that somebody reviewed the entry.
- Still incomplete, and not addressed here: 126 of 179 messages untranslated in
  Slovak, 80 in Czech.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.2.3.0] — 2026-09-02
-------------------------

Added
~~~~~

* **Itemised advance invoices.** *Include the ordered items* on the Create
  Advance Invoice wizard puts the order's own products on the advance, each
  carrying its own taxes, instead of one generic *Advance* line per order line.
  Percentage and fixed amounts scale the unit prices and keep the quantities.
* The deduction of an advance on the final invoice is split into one line per
  VAT rate the advance charged.

Fixed
~~~~~

* An order at more than one VAT rate could not be advanced correctly: every
  advance line carried the *Advance* product's single rate, which the tax
  document raised on payment then accounted, and the deduction gave back. On a
  2 500 order bearing 480 of VAT the tax document accounted 375 and the final
  invoice billed the 105 difference to a customer who had already paid it.
  Itemising closes the cycle exactly; a lump-sum advance is unchanged.
* An advance never runs a stock rule. With ``sale_stock`` installed, an
  itemised advance would otherwise have raised a second delivery order
  reserving the same goods twice.

[19.0.2.2.8] — 2026-07-21
-------------------------

Fixed
~~~~~

- Hardened ``sale.order._get_advance_product``: it now also sets
  ``base_unit_count`` (guarded by a ``_fields`` check) when creating the
  Advance product. ``website_sale`` adds that field to ``product.template`` as
  required / NOT NULL, and its default is not applied on a bare template create
  (no variant yet), so the create raised a ``NotNullViolation`` on databases
  with ``website_sale`` installed.
- Reverted the ``19.0.2.2.7`` attempt to load ``data/product_data.xml`` from
  the manifest. That is unsafe on any database with ``website_sale`` installed
  (required ``base_unit_count`` / ``publish_date`` cannot be populated from
  static XML, and this module does not depend on ``website_sale``). The product
  is created lazily and website_sale-aware by ``_get_advance_product`` instead;
  the XML file is kept only as a reference and carries a comment warning against
  re-adding it to the manifest.

[19.0.2.2.6] — 2026-07-18
-------------------------

Added
~~~~~

- "Advance Invoices" menu entry under Accounting → Customers, just before
  Payments (visible to salespeople and accounting users).

[19.0.2.2.5] — 2026-07-18
-------------------------

Fixed
~~~~~

- The sale-order PDF of an advance invoice is now named "Advance Invoice -
  ADV…" ("Zálohová faktúra - …" / "Zálohová faktura - …") instead of
  "Order - ADV…": ``sale.action_report_saleorder`` delegates its
  ``print_report_name`` to ``sale.order._get_saleorder_report_filename()``,
  which translates per rendering language. The post_init hook and a
  migration force the expression for every installed language (the field is
  translated and core ``sale`` ships per-language expressions). Fixed the
  fuzzy Slovak translations of "Advance Invoice" / "Advance Invoice #".

[19.0.2.2.4] — 2026-07-18
-------------------------

Fixed
~~~~~

- All three mail templates now render in the customer's language
  (``lang = {{ object.partner_id.lang }}``) — previously they rendered in
  the sending user's language. A post-migration backfills the ``noupdate``
  records on existing databases.

[19.0.2.2.3] — 2026-07-14
-------------------------

Fixed
~~~~~

- Posting an advance tax document now reconciles its clearing-account leg
  (``advance_received_account_id``, e.g. 324001) against the advance payments'
  legs on the same account — previously the documentation claimed this
  happened but the step was silently left to the user.

[19.0.2.2.2]
------------

Fixed
~~~~~

- Invoice report override: the "Invoice Date → Issue Date" xpath now anchors on
  the first label child of ``div[@name='invoice_date']`` (``t[1]``) instead of the
  exact ``t-if="o.move_type == 'out_invoice'"`` attribute string. The attribute
  match broke installation on databases where another inheriting view (a Studio
  relabel or a localization) had rewritten that ``<t>``, aborting with
  ``ParseError: ... cannot be found in parent view``.

[19.0.2.2.1]
------------

- Regenerated ``.pot`` from the current module and merged ``cs``/``cs_CZ``/``sk``/``sk_SK``
  ``.po`` (removed obsolete entries). Translated the renamed/added strings
  (advance clearing & received-advance accounts, long-term advance, tax-document
  label, settings help) into Czech and Slovak; recompiled ``.mo``.

[19.0.2.2.0]
------------

Fixed
~~~~~

- ``_ensure_advance_accounts`` now returns the created/looked-up accounts and
  ``_apply_advance_invoice_setup`` uses them directly (with a flush before resolving
  the remaining chart accounts). Previously a just-created company-dependent
  account code could resolve to the wrong account in the same transaction,
  swapping the clearing and short-term accounts on multi-company installs.

[19.0.2.1.0]
------------

Added
~~~~~

- ``res.company._ensure_advance_accounts()`` + a ``create_accounts`` key in the
  localization spec, so localization modules can ship accounts the standard chart
  lacks (e.g. the reconcilable ``324001`` advance-clearing account).

[19.0.2.0.0]
------------

Added
~~~~~

- **Localization support.** Country-specific accounts/journal are now wired by
  thin localization modules (``l10n_cz_sale_order_advance_invoice``,
  ``l10n_sk_sale_order_advance_invoice``) via ``tools.apply_advance_invoice_spec``
  and ``res.company._apply_advance_invoice_setup`` — accounts resolved by code per
  company on the matching chart template. Existing hand-configured deployments
  are preserved (only empty fields are filled).
- **Long-term received advances.** New ``advance_invoice_long_term`` flag on the
  advance invoice routes settlement to a dedicated long-term account
  (``advance_tax_doc_account_lt_id``, e.g. 475) instead of the short-term one.
- Overridable ``sale.order._advance_invoice_tax_doc_deadline()`` hook for the
  statutory tax-document deadline (default: min(paid + 15 days, end of month)).
- Interactive documentation under ``static/description``.

Changed
~~~~~~~

- **Account model.** ``advance_received_account_id`` is now described as the
  reconcilable *clearing* account; ``advance_tax_doc_account_id`` as the short-term
  *net received-advance* account (no longer requires ``reconcile=True``).
- The standalone-link wizard now routes the with-tax-document deduction to the
  net received-advance account, consistent with the parent-tracking path.
- Generic (country-neutral) field labels, help text and code comments.
- Author set to Data Dance s.r.o.

Fixed
~~~~~

- **Multi-company crash:** ``advance_invoice_journal_id`` was ``required=True`` with a
  cross-company ``env.ref`` default, breaking creation of additional companies. The
  default/required were removed; the journal is set by the install hook, the
  localization, or manually.
- Journal type/domain mismatch: the field domain now allows the dedicated general
  journal it actually uses (``type in ('sale', 'general')``).
- Removed dead commented code in the tracking-line description builder.

[19.0.1.0.0]
------------

- Initial version (built in VS Code Copilot Chat, see ``docs/creation_transcript.md``).
