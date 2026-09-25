=========
Changelog
=========

All notable changes to **account_qr_code_payme_sk** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.3] — 2026-09-13
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

[19.0.1.1.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- **A field label was being INVENTED, not missing.** ``fields.Float("Night
  work %", ...)`` passes ``string`` positionally, and
  ``tools/i18n_export_offline.py`` read it from keyword arguments only — so it
  fell back to deriving a label from the field name and wrote "Noc Pct" into
  the catalogue where Odoo's own export writes "Night work %". Every
  translation keyed to the derived form was therefore keyed to a msgid the
  runtime never looks up: present, valid, and dead.
- The exporter now reads the positional slot, which differs per field type
  (``Many2one`` puts ``comodel_name`` first, ``One2many`` two arguments,
  ``Many2many`` four, ``Selection`` its selection). Positional ``selection``
  lists are extracted too, which is where the stupne-náročnosti and VRP2
  receipt-state labels had been going missing entirely.
- Catalogues regenerated against the corrected msgids and re-translated.

[19.0.1.1.1] — 2026-09-13
-------------------------

Added
~~~~~

- **Slovak catalogue — the module had none.** Generated with
  ``tools/i18n_export_offline.py`` (no database is available here) and verified
  back through Odoo's own ``PoFileReader``, so every entry resolves to the
  record it belongs to rather than importing as code strings only.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.1.0] — 2026-07-14
-------------------------

Added
~~~~~

- Payment identification (``PI``) uses the structured ``/VS…/SS…/KS…`` form
  when the invoice provides its payment symbols (via
  ``l10n_cssk_payment_symbols`` context).

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Slovak **payme** payment QR code as a ``res.partner.bank`` QR method, rendered on
  reports via the shared frame provider.
- Builds the payme.sk payment-link URL (SBA Payment Link standard 2.0) from the
  IBAN, amount, EUR currency, payment identification (PI), creditor name, and an
  optional message.
