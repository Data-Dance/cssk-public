=========
Changelog
=========

All notable changes to **l10n_cssk_payment_symbols** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Carry-over to 19.0
~~~~~~~~~~~~~~~~~~

- **None of 18.0.1.2.0 - 18.0.1.3.0 is on 19.0, and none of it is
  18.0-specific.** Odoo core's ``cs_CZ`` catalogue labels ``payment_reference``
  "Variabilní symbol" on 19.0 exactly as on 18.0, so the same trap exists
  there: a free-text field labelled for the variable symbol beside the real
  one. Port the view relabels (form, list, search), the VS/KS/SS placement
  after ``payment_reference`` on both document types, and the cs/sk catalogues.
- Two findings port with them, and both are cheap to get wrong a second time:
  ``payment_reference`` appears **twice** in ``account.view_move_form``, so
  every spec must be pinned on ``@invisible`` (``@string`` is refused as a
  selector); and the ``.po`` override of core's field label is **inert on an
  existing database**, so the view specs are the fix and the catalogue entry is
  a fresh-install convenience. Re-verify the node count against 19.0 core
  rather than assuming the line numbers carry over.

[18.0.1.3.0] — 2026-09-01
-------------------------

Changed
~~~~~~~

- **VS/KS/SS now sit directly after ``payment_reference`` on every document
  type.** They previously had a single placement in the main sheet, which put
  them beside the vendor-bill ``payment_reference`` and nowhere near the
  customer-invoice one — that field is repeated by core, once in the main sheet
  and once in the Other Info tab, so one placement can only ever sit beside one
  of them.

  The symbols are therefore placed twice, each copy carrying the same
  visibility condition as the node it follows. The two are disjoint and their
  union is the same six move types the single placement covered, so nothing
  becomes newly visible or hidden — only the position changes. Reading the
  reference and the symbols as one group is the point: they are the fields a
  user compares against each other, and the whole reason this module relabels
  ``payment_reference`` at all is that the two were easy to confuse.

[18.0.1.2.2] — 2026-09-01
-------------------------

Fixed
~~~~~

- **The relabel now covers the invoice list and the search panel too.**
  Measured on a live ``cs_CZ`` database after install: the catalogue override
  of ``account.field_account_move__payment_reference`` **did not apply**.
  ``TranslationImporter.save(overwrite=False)`` will not replace a value
  ``account`` has already written, so on any *existing* Czech database the
  override is inert and ``ir.model.fields`` still reads "Variabilní symbol".
  Only the form view's own label landed.

  That is now a measurement rather than a caveat, and it changes which half is
  load-bearing: the view specs are the fix, and the catalogue entry is a
  fresh-install convenience. So every other place core renders this label is
  pinned the same deterministic way — ``account.view_invoice_tree`` (the list
  column) and ``account.view_account_invoice_filter`` (the search panel). Both
  carry exactly one ``payment_reference`` node in 18.0, verified, unlike the
  form where there were two and the first silently won.

  What this deliberately does **not** reach: anything taking the label straight
  from the field definition rather than from a view — exports and the developer
  tooltip. Closing that would mean writing into another module's translation
  data from a hook, which is a worse thing to own than the residue.

[18.0.1.2.1] — 2026-09-01
-------------------------

Fixed
~~~~~

- **The relabel reached vendor bills only.** ``payment_reference`` appears
  **twice** in ``account.view_move_form`` — once in the main sheet for vendor
  bills (``account_move_views.xml:1033``) and once in the Other Info tab for
  customer invoices (``:1442``) — and view inheritance resolves an unqualified
  spec to the *first* match. So 18.0.1.2.0 relabelled the vendor-bill node and
  left customer invoices to the catalogue override alone.

  That is the wrong way round. A customer invoice is where a Czech variable
  symbol matters most, because it is the number the customer is asked to quote
  when paying; it is the placement that most needed the deterministic half of
  the fix and was the one that had only the conditional half.

  Both nodes are now pinned by xpath on their own ``@invisible``, which is not
  a translated attribute and so is valid as a selector — ``@string`` is not,
  since ``_valid_inheritance`` refuses translated attributes. Each of the three
  specs was checked against real 18.0 core and resolves to exactly one node.

  The symbol fields keep their main-sheet placement for every document type,
  now stated explicitly rather than inherited from whichever node matched
  first: the customer-invoice ``payment_reference`` sits behind the Other Info
  tab, and a variable symbol behind a tab is one nobody fills in.

[18.0.1.2.0] — 2026-09-01
-------------------------

Added
~~~~~

- **Czech and Slovak translations** (28 terms). The module had no ``i18n/``
  directory, so its fields showed in English on a Czech database — which was
  the only thing keeping the collision below from being visible.

Fixed
~~~~~

- **Core's ``payment_reference`` no longer reads "Variabilní symbol" on the
  invoice form.** Odoo's own ``cs_CZ`` catalogue translates it that way
  (``addons/account/i18n/cs.po``), for both ``account.move`` and
  ``account.payment`` — so a Czech database showed a field labelled for the
  variable symbol directly above the real one this module adds. One is free
  text, the other is digits-only and length-checked, and a user who typed the
  VS into the wrong one produced a payment the recipient could not match, with
  nothing to warn them. It is what made a live Fio payment run go to the bank
  with no symbol at all.

  Fixed twice over, deliberately:

  * The inherited invoice view restates the label on the ``payment_reference``
    node. In English that is a no-op — it is the same string core uses — and it
    exists so the label becomes a term of *this* module's catalogue, where
    ``cs_CZ`` renders it "Reference platby". This part is deterministic and
    does not depend on translation-load order.
  * The same catalogue entry also carries
    ``account.field_account_move__payment_reference`` and
    ``…__payment_payment_reference`` as references, so the field label is
    corrected everywhere else too — list views, filters, exports. This half
    depends on both modules' catalogues being loaded together (Odoo builds one
    ``TranslationImporter`` for all modules and saves once, so the later module
    wins), and on an existing value not blocking it, so it is the belt to the
    view's braces rather than the other way round.

  Slovak core is already correct ("Referencia platby"), so no override is
  needed there.

[18.0.1.1.0] — 2026-07-18
-------------------------

Added
~~~~~

- VS/KS/SS fields on ``account.payment`` (``l10n_cssk_*``, editable,
  digits-validated) — prefilled by the Register Payment wizard from the paid
  document(s) when every covered document agrees on the symbol, left empty
  otherwise. Shown on the payment form.

[18.0.1.0.0] — 2026-07-18
-------------------------

Added
~~~~~

- Initial release (port of the 19.0 module). Canonical VS/KS/SS fields on
  ``account.move`` (moved here from ``l10n_cssk_core``) with digits-only
  validation (10/4/10), variable symbol capped at the last 10 digits, company
  policy for credit-note VS (own number — default — or the reversed invoice's
  symbol), company default constant symbol on customer documents.
- Optional company toggle **Payment Reference = Variable Symbol** — customer
  documents then carry the VS in ``payment_reference`` on posting.
- ``variable_symbol`` / ``constant_symbol`` / ``specific_symbol`` on bank
  statement lines, populated on create from explicit values, connector
  ``transaction_details`` (incl. the ``variable_code`` key of upstream
  odoo/odoo#275611) or ``VS:``-style label tokens; the VS is prefixed into
  ``payment_ref`` (never twice) so stock matching heuristics see it.
- Invoice symbols travel to the QR generation stack via the
  ``cssk_payment_symbols`` context key.
