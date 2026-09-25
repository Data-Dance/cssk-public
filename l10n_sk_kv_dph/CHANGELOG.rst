=========
Changelog
=========

All notable changes to **l10n_sk_kv_dph** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **19.0.2.0.7 (2026-09-21), not yet on 18.0.** Five items from one
  accountant review, in commits 02eda35, d61f9f5, ca4de2c, 7c85090, d380b99:
  cash-basis taxes reported once and when paid (the one that changes filed
  figures: an unpaid "Based on Payment" document was reported, and its
  payment reported again in B.3.1); 0 % purchases kept out of B.2/B.3;
  drill-down on B.3.1/B.3.2/D.1/D.2; A.2 TK/TD/Mn/MJ with a product field;
  the ``vs_eu_s_*`` xmlids added to the reverse-charge flag list. Check on
  18.0 that ``tax_cash_basis_origin_move_id`` / ``always_tax_exigible`` exist
  as on 19.0 before porting the first, and that ``uom._has_common_reference``
  does (18.0 still has UoM categories) before porting A.2.
- **19.0.2.0.8 (2026-09-21), not yet on 18.0.** EU private customers go to
  D.2 (drop the ``not is_eu`` from the D.2 test), with its recompute
  migration.

[19.0.2.0.8] — 2026-09-21
-------------------------

Fixed
~~~~~

- **A private person from another EU state goes to D.2, not A.1.** A supply
  taxed at Slovak rates to a customer with neither an IČ DPH nor an IČO went
  to D.2 only when the customer was outside the EU. Confirmed by an
  accountant (Atheo): "Fyzické osoby nepodnikatelia idú do D2", whatever the
  country — § 72 imposes no invoice obligation towards a private individual
  anywhere. An EU business recorded with its registry number stays in A.1.
  The upgrade recomputes the affected sales lines; recompute unfiled
  statements afterwards.

[19.0.2.0.7] — 2026-09-21
-------------------------

Fixed
~~~~~

- **A tax "Based on Payment" was reported twice.** With cash-basis taxes
  (customs VAT, issued advance invoices) the statement reported the document
  as soon as it was posted, unpaid, and after payment reported Odoo's
  cash-basis entry again — in **B.3.1**, because that entry carries no partner
  and a received document with no counterparty is treated as a simplified
  invoice. The document now stays out until it is paid; each payment is
  reported once, in the section of the document it settles (B.2, A.1, C.1 …),
  under that document's number and counterparty and dated by the payment. A
  payment that is un-reconciled within the period cancels out rather than
  filing +x and −x. The upgrade re-resolves the affected lines.
  Reported by an external accountant (Atheo).
- **A 0 % purchase reached B.2.** B.2 and B.3 report the tax the recipient
  deducts, and a received supply bearing no tax (exempt supply, duty-only
  customs line, a 0 % purchase tax) deducts none — its B.2 row filed
  ``D="0.00"``, which FS SR rejects. It now stays out, as a 0 % supply already
  did on the A.1 side. C.2 is unchanged.

Added
~~~~~

- **Drill-down on the aggregate sections.** B.3.1, B.3.2, D.1 and D.2 name no
  document in the form, so there was no way to see which receipts or sales a
  total was made of. Their rows now keep the source lines, and the tabs show
  a list with the same *Documents* button as the detail sections. D.2 also
  counts its documents (``row_count``) and no longer claims in its docstring
  that the resolver never assigns it.
- **A.2 reports what was supplied.** For goods under § 69 ods. 12 písm. f)
  to i) the A.2 row now carries the commodity code (TK, písm. f, g), the kind
  of goods (TD = MT / IO, písm. h, i), the quantity (Mn) and its unit (MJ).
  The schema has had these attributes in every vzor since 2014; the template
  never wrote them. The category is set on the product (*Tovar podľa § 69
  ods. 12*); the code comes from the product's own field or, failing that,
  from its OCA / Enterprise / CE customs code. Quantities are converted into
  kg, t, m or ks, a document mixing commodities files one row per commodity,
  and the export names any row missing its code or a convertible unit.

[19.0.2.0.6] — 2026-09-17
-------------------------

Fixed
~~~~~

- **An Administrator could not open it.** An accounting **Administrator**
  could reach a control statement (KV DPH) but not its sections and hit *not
  allowed to access*. On Community, ``account.group_account_manager`` does not
  imply ``account.group_account_user`` (and on Enterprise
  ``account_accountant`` only adds ``group_account_basic``), so a model
  granted to ``group_account_user`` alone is closed to an Administrator who
  lacks "Show Full Accounting Features". The control statement already granted
  it; the section models did not. ``group_account_manager`` now has the same
  access as ``group_account_user`` on the sections A.1–D.2. Takes effect on
  module update.

[19.0.2.0.5] — 2026-09-17
-------------------------

Fixed
~~~~~

- **A statement computed on existing accounting came out empty.** Every line's
  control section was computed when ``l10n_cssk_kv_kh_base`` installed, before
  this module's resolver was loaded, and nothing recomputed it afterwards — so
  on a database with history every line kept no section and the statement
  had nothing to populate, with no error. The install hook now recomputes the
  section on all posted lines of the SK companies, and the upgrade to
  19.0.2.0.5 repairs databases that were already installed.

[19.0.2.0.4] — 2026-09-13
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

[19.0.2.0.3] — 2026-09-13
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

[19.0.2.0.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the source are
  deliberately left untranslated — the source IS the translation, per the
  hybrid convention for these modules — so an empty ``msgstr`` there is correct
  rather than missing.

[19.0.2.0.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- The collapse of the twelve per-version types moved here, into a
  pre-migration, because it could not work from the base module — see
  ``l10n_cssk_kv_kh_base`` 19.0.2.0.1. A post-migration asserts the result.

[19.0.2.0.0] — 2026-09-12
-------------------------

Changed
~~~~~~~

- The three submission types are declared **once**, against Slovakia, with
  xmlids (``kv_dph_type_rdp`` / ``_odp`` / ``_ddp``) — replacing the inline
  ``statement_type_ids`` payload that was repeated on all four version records.
  See ``l10n_cssk_kv_kh_base`` 19.0.2.0.0 for the reasoning and the migration.

[19.0.1.11.0] — 2026-09-10
--------------------------

Fixed
~~~~~

- **Odpočítaná daň was a dead field: the row said 0.00 while the XML filed the
  full tax.** ``deducted_amount`` has been declared on the detail rows since
  the module was written and was never populated; the QWeb template rendered
  attribute ``O`` (``OR`` on C.2) straight from ``tax_amount`` instead. The
  filed figure was therefore right and the record disagreed with it — which
  surfaced when a filed statement was compared against a computed one and
  every B.1/B.2 row was reported as a difference in that position with nothing
  wrong in the XML at all (146 rows, 5 037.77, on one real agenda).

  The received sections (B.1, B.2, C.2 — including the § 53b bad-debt
  corrections) now write the deduction, and every vzor's template renders
  ``O``/``OR`` from it. **No filed figure moves** for a company deducting in
  full, which is what the template already asserted. The issued sections
  (A.1, A.2, C.1) have no such attribute and keep 0.00.

  A ``post-migration`` carries the old rendering into the data, so a statement
  computed before this version does not start exporting zeros. It matches only
  rows whose deduction is zero while tax was charged, so a hand-set § 50
  figure is never overwritten.

  Making the field honest is what makes the **§ 50 koeficient** case visible:
  a company that deducts only a fraction of its input VAT can now override
  ``deducted_amount`` on the row (it is in ``_KV_OVERRIDE_FIELDS``, so the
  override survives a recompute) and the override reaches the XML. Deriving
  the coefficient itself is still not modelled — it is a fact about the
  company and its year, not about the document.

[19.0.1.10.0] — 2026-09-08
--------------------------

Fixed
~~~~~

- **Supplies to private individuals were reported in A.1 instead of D.2.**
  A.1 carries "údaje z vyhotovenej faktúry"; D.2 (§ 78a ods. 2 písm. d) is the
  aggregate for domestic taxable supplies the platiteľ was not obliged to
  invoice, and § 72 obliges an invoice only towards a zdaniteľná osoba or a
  právnická osoba. The resolver now sends a domestic supply to a customer with
  neither IČ DPH nor IČO to D.2.

  **The test is the IČO, not the IČ DPH.** A Slovak neplatiteľ business — a
  živnostník or an s.r.o. under the registration threshold — holds no IČ DPH
  and *is* a taxable person, so it stays in A.1 with ``Odb`` omitted, which
  ``A1/@Odb use="optional"`` permits in every vzor we ship (2014/2016/2023/
  2025); only ``A2/@Odb`` is required. Keying the rule on the IČ DPH instead
  would misfile that population, which is larger than the one being fixed.

  Measured on a Slovak s.r.o.'s 2016–2019 agenda against the 32 control
  statements it actually filed (PREMIER import, cross-session report):
  86 moves with IČ DPH (18 835.98) and 3 with an IČO but no IČ DPH (148.62)
  were filed in A.1 — together the filed A.1 total to the cent — while 5 to
  private individuals (731.48) were filed in D.2. After the change A.1,
  B.3.1 and D.2 all reproduce the filed figures exactly and 92 of 95
  section-periods agree; the residual is two documents where the source's own
  ledger and filing disagree.

  ⚠️ **Depends on the IČO being recorded.** Until ``l10n_cssk_core`` 7babaf6
  (2026-09-08) core hid ``company_registry`` behind
  ``invisible="parent_id or not is_company"``, so on a CZ/SK partner stored as
  a natural person — what ``website_sale`` creates, and what a živnostník is —
  the field could not be entered. On a database predating that fix an
  unregistered business can carry an empty IČO and will be read as a private
  individual. Check domestic customers with sales history and no IČO before
  trusting the split; ``l10n_sk_trade_registry`` can fill it from the name.

  Still open with the accountant: whether a *voluntarily* issued faktúra to a
  private individual changes the answer. On the measured agenda it did not —
  all five were ordinary invoices and still went to D.2 — but that is one
  agenda.

Documented
~~~~~~~~~~

- C.2: recorded, from 134 filed statements of the same agenda, that **a filed
  C.2 correction can name an original that appears in no B.2 at all** — 4 of
  11, two suppliers with no B.2 row in any statement, the originals most
  likely inside the B.3.1 aggregate which carries no document numbers. The
  module's long-standing open question about C.2 over-production is unchanged,
  but the obvious-looking way to close it — only emit C.2 where the corrected
  invoice was itself reported — is now known to be wrong, and would have
  dropped 4 of those 11. No code change; a fence around a wrong fix.

Added
~~~~~

- ``KV_D2_BUSINESS`` — a **warning** where a D.2 supply's customer looks like a
  taxable person: flagged as a company, or previously reported in A.1, which a
  private individual never is. The IČO proxy fails in one direction that
  nobody can see from the statement, because D.2 is a total and the customer
  never appears in it — so a business whose IČO was simply never recorded is
  aggregated away silently. A warning and not an error on purpose: a genuine
  retail D.2 is ordinary and must still export.
- Test that ``KV_NO_TAX`` catches an aggregated B.3.1 base filed with no daň,
  covering the ``l10n_cssk_kv_kh_base`` 19.0.1.7.1 fix from the concrete
  Slovak section it was blind to.

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

- Section C.2 and B.3 selected by a raw accounting-date range instead of the
  shared period helper, so KV DPH could disagree with the VAT return it
  reconciles against.

[19.0.1.0.3] — 2026-07-14
-------------------------

Fixed
~~~~~

- Received-document sections **B.1, B.2, C.2** now export the supplier's poradové
  číslo faktúry (``move.ref``) instead of our internal move name; in C.2 the
  original-document column likewise uses the supplier's number of the reversed
  entry. Issued sections (A.1, A.2, C.1) keep our own number.
- Detail rows now report dátum dodania from ``taxable_supply_date`` when set
  (e.g. advance tax documents: the payment date), falling back to the invoice date.

[19.0.1.0.2] — 2026-07-04
-------------------------

Fixed
~~~~~

- Foreign-service §69/2 reverse charge and intra-EU §11 acquisitions now correctly land in section **B.1** — the section board reconciles **24/24** against the filed MRP reference.

Changed
~~~~~~~

- Manual section overrides now survive recompute (snapshot/re-apply) on KV sections (Wave 3).
- Export pipeline consolidated into the shared ``cssk.statutory.submission.mixin``; kontroly now run before render.
- ``normalize_vat()`` helper adopted for IČ DPH handling.

[2026-07-01] — Wave 1 (P0 correctness)
--------------------------------------

Fixed
~~~~~

- Reverse-charge routing: intra-EU acquisitions (§11, ``vs_nad_eu_*``) routed to KV section **B.1**.
- Multi-company leak closed with an ``ir.rule [('company_id','in',company_ids)]``.

Changed
~~~~~~~

- Statutory rounding unified on ``statutory_round()`` (HALF-UP).

[2026-06-30] — Initial baseline
-------------------------------

Added
~~~~~

- Slovak Kontrolný výkaz DPH (**KVDPHv17**) on ``l10n_cssk_kv_kh_base``: sections A.1, A.2, B.1, B.2, B.3.1, B.3.2, C.1, C.2, **D.1**, D.2 — D.1 is implemented (most vendors skip it).
- SK move-line section resolver (reverse-charge first).
- FS SR ``KVDPH`` XML export (QWeb template + XSD slot on the version record). CE-clean (no ``account_reports``).
- sk_SK translations (Odoo 19 jsonb) as part of the localization i18n sweep.
