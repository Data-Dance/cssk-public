=========
Changelog
=========

All notable changes to **l10n_cssk_translation_override** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.1.1.0] — 2026-11-05
-------------------------

Added
~~~~~

- Catalogues for 61 more Community and OCA modules that a Czech or Slovak
  company commonly installs, though none of our modules depends on them:
  attendance (with the kiosk), skills and résumé, timesheets and OCA timesheet
  sheets, home working, public holidays, project and to-dos, credit control,
  Peppol responses, document management (OCA ``dms``), wiki
  (``document_page``), SMS and letters by post, two-factor login, passkeys,
  the inactivity lock, the dashboards, ratings, privacy lookup and the OCA
  web add-ons. 2,825 Slovak and 2,484 Czech terms that had no translation.
  OCA ``hr_timesheet_sheet`` is built against its 19.0 migration
  (OCA/timesheet#941), which is not merged yet.

Fixed
~~~~~

- ``hr_attendance``: Czech *Check in / Check out* is *Příchod / Odchod*, not
  *Přihlásit se / Odhlásit se* (log in / log out), on the kiosk, in the PIN
  prompt and in the messages.
- ``hr_skills``: *Resume* (the CV) is *Životopis* in both languages, not
  *Shrnutí* (summary) or *Pokračovať* (continue); Czech *Certifikace* was
  misspelt.
- ``account_statement_import_file``: the journal dashboard's *Import (OCA)*
  is *Import výpisu* in both languages. l10n_cssk's own copy of the module
  already said so; OCA's copy, when it is the one loaded, left it English.
- ``hr_attendance``: Slovak *Management* is *Správa* (as the Czech), not
  *Manažment*; ``account_credit_control``: *Policies* on a run is *Pravidlá* /
  *Politiky*, as the policy itself is named.

[19.0.1.0.5] — 2026-11-05
-------------------------

Fixed
~~~~~

- Slovak and Czech override catalogues: filled terms that were still English
  in Odoo's and OCA's own catalogues (chiefly the Czech website builder and CRM).
- New catalogues for ``hr_work_entry`` and ``hr_work_entry_holidays``, which the
  payroll modules depend on: Odoo ships no Slovak for them and only part of the
  Czech, so work entry types and their forms were English.

[19.0.1.0.4] — 2026-11-05
-------------------------

Changed
~~~~~~~

- ``account``: the Slovak *To Validate* counter on the journal dashboard is
  *na schválenie* (as the Czech *ke schválení*), not *na zaúčtovanie*.

[19.0.1.0.3] — 2026-11-05
-------------------------

Changed
~~~~~~~

- ``account``: the counters on the journal dashboard follow a number, so they
  start lower-case (*1 na zaúčtovanie*, *14 nezaplatené*, *3 k úhrade*,
  *2 na kontrolu*; Czech likewise). *Late* is *po splatnosti*, which agrees
  with any number. Only the dashboard view is affected; filters keep their
  capitals.
- ``account``: Czech *Payment Reference* is *Reference platby*, not
  *Variabilní symbol*. It is a free-text field; the variable symbol is the
  separate digits-only field of ``l10n_cssk_payment_symbols``.

[19.0.1.0.2] — 2026-11-04
-------------------------

Added
~~~~~

- Catalogue for OCA ``account_lock_date_update`` (its wizard was English in
  both languages; upstream Slovak and Czech had 8 of 26 terms).

Changed
~~~~~~~

- Lock dates follow one pattern, as the company fields and the OCA wizard:
  *Globálny dátum uzamknutia* (Odoo's *Globálne* was a grammar error),
  *Dátum uzamknutia DPH* / *Datum uzamčení DPH* for the tax return lock date
  (was *Termín uzávierky daňového priznania*, which reads as a filing
  deadline, and *Datum uzamčení zúčtování daně*), and the help texts and
  messages that name them (*dátum daňového zámku*, *pevného zámku*, "Nové
  dátum" and a Czech message that lost its meaning).
- ``account``: *Reverse Entry* → *Stornovať* (was *Záznam storna*),
  *Change Period* → *Zmeniť obdobie* (was *Obdobie zmeny*); the company's
  fiscal year end fields say *účtovné obdobie / účetní období*, and Slovak
  *Last Month* no longer reads as "previous month".
- ``account_usability``: the *Fiscal Year Last Day* setting of OCA
  19.0.1.1.0 is translated. That version aliases ``account.menu_finance`` as
  ``account_usability.menu_finance``; the *Accounting* entry carries both, and
  ``catalogue_check`` accepts an alias the target's template carries.

[19.0.1.0.1] — 2026-11-04
-------------------------

Fixed
~~~~~

- A record field's translation (menu, group, category name) is written only
  while the record's English equals the entry's msgid. Odoo's importer writes
  these by xmlid without looking at the source, so with OCA
  ``account_usability`` installed the main menu read "Accounting" in English
  but "Fakturácia" / "Fakturace" in Slovak / Czech, and a reload of
  ``account``'s terms would have put the old name back. Candidates are kept
  per source text and the current English picks one, in any load order.
- Records that a module renames in English but does not own
  (``account_usability``: ``account.menu_finance``,
  ``account.group_account_user`` / ``_manager`` / ``_readonly``,
  ``base.module_category_accounting_accounting``) now get Slovak and Czech
  names. Odoo exports them under an xmlid that does not exist, so no template
  can carry them; the override targets the real xmlid, ``catalogue_check``
  verifies the msgid against the target's XML, and the entry is written even
  on a ``noupdate`` record, whose old translation belongs to the old English.
- ``mis_builder``: "Template" → Šablóna / Šablona (as in the menus),
  "Duration" → Počet období, Czech "To" → Do, "Widget" translated.

[19.0.1.0.0] — 2026-11-02
-------------------------

Added
~~~~~

- Override catalogues ``i18n_override/<module>/{sk,cs}.po`` for other
  modules' terms. Field, selection, menu, action and view terms are re-applied
  with overwrite after every load of module terms (install, upgrade, language
  activation or reload), so they survive Odoo's own catalogue and
  ``--i18n-overwrite``; ``noupdate`` records are left alone.
- Code terms (``_()``, ``_lt``, JS) merged over the target module's own, by
  wrapping ``CodeTranslations._get_code_translations``; process-wide, and a
  changed catalogue needs a restart.
- ``catalogue_check``: every override must match a msgid and occurrence in the
  target's template, so an override gone stale upstream fails a test instead
  of silently showing Odoo's text.
- Records named from code messages (warehouse operation types, routes and
  rules, code-created journals, POS payment methods) get their Slovak / Czech
  name from the code translations when a database was set up in English:
  after every load of module terms, deferred to the end of a module install,
  and daily for records created since. A name already translated or edited by
  hand is kept. Written as a jsonb merge: where en_US is not an active
  language Odoo's ORM writes en_US along with the other language, which
  replaced the English source and left the second language untranslatable.
- The catalogues: Slovak and Czech for the 102 Community and OCA modules the
  CZ/SK modules depend on (Odoo 19.0 upstream as of 2026-11-02, OCA 19.0
  branches as of the same day): 13,859 SK and 6,526 CS terms that had no
  translation, and 1,204 SK and 758 CS existing translations corrected
  against one glossary (wrong terms, untranslated text, the same source
  translated differently in different modules). Built and validated with the
  pipeline in the repository's docs/translation-audit/.
- Re-applies only the catalogues of the modules whose terms were just loaded
  (all of them on its own install and on a language install), so installing
  N modules no longer parses every catalogue N times.
