=========
Changelog
=========

All notable changes to **l10n_sk_datadance** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.4.3] — 2026-09-17
-------------------------

Fixed
~~~~~

- **An Administrator could not open it.** An accounting **Administrator**
  could reach the books reconciliation on a VAT return, control statement or
  EC sales list and hit *not allowed to access*. On Community,
  ``account.group_account_manager`` does not imply
  ``account.group_account_user`` (and on Enterprise ``account_accountant``
  only adds ``group_account_basic``), so a model granted to
  ``group_account_user`` alone is closed to an Administrator who lacks "Show
  Full Accounting Features". Those filings already granted it.
  ``group_account_manager`` now has the same access as ``group_account_user``
  on ``l10n.sk.dph.reconciliation``. Takes effect on module update.

[19.0.1.4.2] — 2026-09-13
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

[19.0.1.4.1] — 2026-09-13
-------------------------

Added
~~~~~

- Slovak and Czech for the filed-vs-computed comparison screen —
  the kind and state values, the ``basis`` discriminator and its
  label, the search filters and the three explanatory alerts on the
  form. The screen is what a migrated filing is read through, and
  the accountant reading it works in Slovak.

[19.0.1.4.0] — 2026-09-13
-------------------------

Changed
~~~~~~~

- **The three reconciliations write comparison rows instead of chatter.**
  ``action_reconcile_books`` (priznanie ↔ účet 343), ``action_reconcile_dph`` on
  the KV (KV ↔ priznanie) and on the súhrnný výkaz (SV ↔ priznanie) each posted
  a ``<ul>`` to the record and returned a toast reading "pozri záznam". At 217
  filings that is unreadable, and a log is not a worklist. Each row now becomes
  a ``cssk.filing.discrepancy`` on its own basis, and the action opens them.

- The KV ⊆ priznanie gap is recorded as ``expected`` and the tržby tie as
  ``info``, so neither reads as a difference. Both were already treated that
  way by ``check_kontroly_*``; the screen now says so as well.

[19.0.1.3.3] — 2026-09-13
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

[19.0.1.3.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the source are
  deliberately left untranslated — the source IS the translation, per the
  hybrid convention for these modules — so an empty ``msgstr`` there is correct
  rather than missing.

[19.0.1.3.1] — 2026-09-13
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

- Three sites: the KV ↔ priznanie, priznanie ↔ účtovníctvo and SV ↔ priznanie
  reconciliation summaries, including the nested *Upozornenia* lists.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- Nothing to port **yet**. The 18.0 umbrella (18.0.1.1.0) still hard-depends on
  ``l10n_sk_fs`` and ``l10n_sk_dppo``, so the model it ``_inherit``s is always
  in the graph and the clean-database failure fixed in 19.0.1.3.0 does not
  exist there. **When the 19.0.1.2.0 toggle change is ported to 18.0, the
  ``l10n_sk_dppo_fs`` bridge must be ported with it in the same commit** —
  porting the toggles alone reproduces exactly the bug 19.0 just fixed.

[19.0.1.3.0] — 2026-09-06
-------------------------

Fixed
~~~~~

- **The bundle could not be installed on a clean database.** 19.0.1.2.0 moved
  ``l10n_sk_fs`` and ``l10n_sk_dppo`` out of ``depends`` and onto settings
  toggles, but left the DPPO ↔ účtovná závierka glue behind: a model
  ``_inherit``ing ``cssk.income.tax.return`` and a view inheriting
  ``l10n_cssk_income_tax_base.cssk_income_tax_return_view_form``, neither of
  which is in the graph unless the DPPO toggle was ticked. Installing
  ``l10n_sk_datadance`` on an empty database failed at registry load with
  ``TypeError: Model 'cssk.income.tax.return' does not exist in registry.``
  The glue moved to the new bridge module ``l10n_sk_dppo_fs``, which
  auto-installs where both toggles are on.

Changed
~~~~~~~

- ``reconcile_vzs_dppo`` / ``check_kontroly_vzs_dppo`` moved off
  ``l10n.sk.dph.reconciliation`` here and onto the same model in
  ``l10n_sk_dppo_fs``. The three reconciliations that need nothing beyond the
  bundle (KV ↔ priznanie, súhrnný výkaz ↔ priznanie, priznanie ↔ účtovníctvo)
  stay here.
- ``test_suite_coverage`` asserted a licensing firewall that 19.0.1.2.0 had
  already removed — that no hard dependency may be AGPL and that every one must
  be ``Other proprietary`` — while the bundle itself became AGPL-3 in that same
  release and every dependency is AGPL-3 with it. Both tests were red on any
  database that ran them. Replaced with the rule that now applies: a hard
  dependency must be publishable, so that the published bundle stays
  installable from the public repository. A third test covers bridges, which
  are reachable neither as a dependency nor as a toggle.

[19.0.1.2.0] — 2026-08-27
-------------------------

Changed
~~~~~~~

- Relicensed from ``Other proprietary`` to **AGPL-3**. This umbrella is part of
  the published set.
- ``l10n_sk_fs`` (Súvaha + VZS) and ``l10n_sk_dppo`` moved out of ``depends``
  and onto ``Settings → Accounting`` toggles. Both are delivered to
  subscribers rather than published, and a hard dependency would have made this
  bundle uninstallable from the public repository. Subscribers see no change:
  the modules are in their addons path and the toggle installs them. Where they
  are absent the toggle is inert, which is the same mechanism Odoo core uses to
  advertise Enterprise modules from Community.


[19.0.1.1.1] — 2026-08-23
-------------------------

Changed
~~~~~~~

- Settings toggle for ``l10n_sk_account_move_template`` relabelled from
  *Predkontácie* to **Účtovné vzory (interné doklady)**, with a help text saying
  explicitly that invoices, bank and cash are still posted by Odoo's own rules.
  In POHODA / ABRA Gen a predkontácia is chosen **on a document** and drives its
  zaúčtovanie; the OCA engine has no link to any document, so the old label
  promised something the module cannot do.

[19.0.1.1.1] — 2026-08-23
-------------------------

Changed
~~~~~~~

- Settings toggle for ``l10n_sk_account_move_template`` relabelled from
  *Predkontácie* to **Účtovné vzory (interné doklady)**, with a help text saying
  explicitly that invoices, bank and cash are still posted by Odoo's own rules.
  In POHODA / ABRA Gen a predkontácia is chosen **on a document** and drives its
  zaúčtovanie; the OCA engine has no link to any document, so the old label
  promised something the module cannot do.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Baseline: one-click Slovak statutory localization meta-module. Installs the statutory core in one step — KV DPH, Súhrnný výkaz, DPH priznanie, Súvaha + VZS, DPPO, SK invoice, VIES, saldokonto + zápočet, and dohadné (accruals).
- Optional workflow pieces (FX sync, deferrals, guarantor-liability check, dual depreciation, Method A, advance invoices) selectable in Settings → Accounting → Slovak localization.

[19.0.1.1.0] — 2026-08-06
-------------------------

Added
~~~~~

- The eight modules built on 2026-08-05 are now reachable from the bundle. Until
  this, a customer installing the umbrella got **none** of predkontácie, lízing,
  JCD, PHL, závierka, inventarizácia, protokoly or AI invoice extraction — the
  ``auto_install`` ones only arrive when their *other* dependency is already
  present, and nothing pulled those in either.
- ``l10n_sk_inventarizacia`` as a hard dependency: § 29 zákona 431/2002 makes
  inventarizácia mandatory for every účtovná jednotka, and it is proprietary, so
  it belongs in the core bundle.
- Settings toggles for the other seven.

Note on the licence split
~~~~~~~~~~~~~~~~~~~~~~~~~

Which of these is a dependency and which is a toggle is decided by **licence, not
usage**. Every hard dependency of this bundle is "Other proprietary"; every AGPL
module is reached through a ``module_*`` toggle, which installs it into the
customer's database without this module depending on it. AGPL is viral over
network use, so hard-depending on one would relicense the whole bundle. Four of
the seven new toggles are AGPL and must stay toggles regardless of how universal
the feature is. ``test_no_agpl_module_is_a_hard_dependency`` asserts it, and was
negative-tested.
