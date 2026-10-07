=========
Changelog
=========

All notable changes to **l10n_sk_dppo_fs** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.2] — 2026-09-13
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

[19.0.1.1.1] — 2026-09-13
-------------------------

Added
~~~~~

- Slovak and Czech for the filed-vs-computed comparison screen —
  the kind and state values, the ``basis`` discriminator and its
  label, the search filters and the three explanatory alerts on the
  form. The screen is what a migrated filing is read through, and
  the accountant reading it works in Slovak.

[19.0.1.1.0] — 2026-09-13
-------------------------

Changed
~~~~~~~

- **``action_reconcile_vzs`` writes a comparison row instead of chatter.** The
  VZS ↔ DPPO r100 tie becomes a ``cssk.filing.discrepancy`` and the action
  opens it, in line with the other reconciliations.

- The row is written **DPPO-first**: the left column holds the filing the user
  is standing on, on every comparator, even though ``reconcile_vzs_dppo``
  itself reads VZS-first. Flipped at the call site rather than in the
  reconciliation, which other callers and its own tests share.

[19.0.1.0.3] — 2026-09-13
-------------------------

Fixed
~~~~~

- **The reconcile toast told the user to read the record, and left the record
  unchanged on screen.** ``message_post`` wrote the comparison to the chatter,
  the action returned a bare ``display_notification``, and a notification does
  not reload the form — so the chatter still showed its pre-click state and the
  entry the toast referred to was not visible. A user who trusted the toast
  would conclude the warnings had never been written.
- The notification now carries
  ``"next": {"type": "ir.actions.client", "tag": "reload"}``, and the warning
  and danger variants are sticky: a toast that says "pozri záznam" must not
  dismiss itself before the record it points at has rendered.

[19.0.1.0.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the source are
  deliberately left untranslated — the source IS the translation, per the
  hybrid convention for these modules — so an empty ``msgstr`` there is correct
  rather than missing.

[19.0.1.0.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- **The chatter posted its own HTML as visible text.** ``message_post``
  ESCAPES a plain ``str`` and renders only a ``markupsafe.Markup`` —
  ``mail_thread.py`` says so on the parameter (``str|Markup body: … str
  content will be escaped``) and applies it at ``'body': escape(body)``. So a
  summary built by joining ``"<li>…"`` fragments arrived in the chatter as
  literal markup. Nothing failed: the post succeeded and the log was clean,
  which is why it survived to a user.

- Built as ``Markup(template) % args`` rather than by wrapping the finished
  string, and the difference is not cosmetic. ``%`` on a ``Markup`` escapes
  what it substitutes; wrapping the join renders it. The interpolated values
  here are not ours — a row code carries an invoice reference or a
  counterparty VAT, a warning detail carries a partner name — so the
  shorter fix would have turned an escaping bug into an injection one.

- One site: the VZS ↔ DPPO reconciliation summary and its *Nezhody* list.

[19.0.1.0.0] — 2026-09-06
-------------------------

Added
~~~~~

- Bridge module (auto-install) linking ``l10n_sk_dppo`` × ``l10n_sk_fs``: the
  VZS r56 → DPPO r100 reconciliation, the ``VZSDPPO_RECON`` kontrola and the
  *Porovnať s účtovnou závierkou* button on the DPPO form.
- Carries the code out of ``l10n_sk_datadance``, where it had been left behind
  when both modules moved from ``depends`` to settings toggles in
  ``l10n_sk_datadance`` 19.0.1.2.0. The umbrella ``_inherit``ed
  ``cssk.income.tax.return`` without the module that defines it, so installing
  the Slovak bundle on a clean database failed outright with
  ``TypeError: Model 'cssk.income.tax.return' does not exist in registry.``
