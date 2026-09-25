=========
Changelog
=========

All notable changes to **l10n_sk_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the source are
  deliberately left untranslated — the source IS the translation, per the
  hybrid convention for these modules — so an empty ``msgstr`` there is correct
  rather than missing.

[19.0.1.0.0] — 2026-09-05
-------------------------

Added
~~~~~

- ``res.partner.l10n_sk_dic`` (mirrored on ``res.company``) — the Slovak DIČ,
  the income-tax identifier. Slovakia issues three identifiers where most
  countries manage two: **IČO** (``company_registry``), **DIČ** (this field)
  and **IČ DPH** (``vat``). A subject can hold a DIČ and no IČ DPH at all —
  anyone registered for income tax who is not a VAT payer — which is why the
  DIČ needs a field of its own.
- An install hook carrying existing values over from ``l10n_cssk_dic``.

Notes
~~~~~

- **The field moved here out of ``l10n_cssk_core``**, the shared CZ/SK base,
  where it sat on the premise that both countries need a separate DIČ field.
  Czech usage does not: there *DIČ* **is** the VAT number (``CZ`` + IČO), so
  ``vat`` already holds it, and ``l10n_cz_invoice`` was printing the same
  number from a second field. That report now prints ``vat``.
- The carry-over runs in ``post_init_hook`` rather than a migration script,
  because a migration in a brand-new module never fires. Removing a field does
  not drop its column, so the old values are still there on arrival. It fills
  only rows where the new field is empty, so a value entered after the upgrade
  wins.
- The view is priority **10**, ahead of ``base_vat``'s 15, which *moves* the
  ``vat`` field into a div — anything anchored after it lands inside and
  renders with no label.

19.0.2.0.0 (2026-09-16)
=======================

* **``res.company.income_tax_id`` is now the partner's DIČ.** ``l10n_sk``
  defines it as a plain stored ``Char`` on ``res.company`` only, so it could not
  be recorded for a customer or a vendor, and this module's own
  ``l10n_sk_dic`` sat beside it as a second company field for the same number.
  Both are now ``related="partner_id.l10n_sk_dic"``, so they are two views of
  one value and cannot diverge, and ``l10n_sk``'s field is hidden on the company
  form to stop the number appearing twice under two names. This is the shape
  Odoo's own `PR #280178 <https://github.com/odoo/odoo/pull/280178>`_ takes,
  down to the partner field's name, so a database that later installs the
  upstream module finds the value already where it expects it.

* **``l10n_sk_dic`` is a commercial field.** A child contact of a company files
  nothing of its own, so it now inherits the parent's DIČ rather than holding a
  blank of its own.

* **The install migrates two more legacy columns, and this is the point of the
  release.** ``l10n_sk_hr_payroll_prehlad`` and ``l10n_sk_hr_payroll_hlasenie``
  each declared ``res.company.l10n_sk_dic`` independently, as a plain stored
  ``Char``. Installing one of those without this module gave an accountant a
  real column to fill; installing this module afterwards made the merged field
  ``related``, at which point the ORM stopped reading that column and the value
  went invisible with nothing having moved it. The hook now carries
  ``res_company.l10n_sk_dic`` and ``res_company.income_tax_id`` onto the
  company's partner alongside the existing ``res_partner.l10n_cssk_dic``.

  It does so in two halves: a ``pre_init_hook`` copies the company values into a
  scratch table before the new field definitions reach the registry, and the
  ``post_init_hook`` applies them. Whether Odoo blanks a column when its field
  changes from plain to stored-related during install is version-sensitive, and
  a migration that depends on that is one that loses the value on the version
  where it goes the other way.

* **Two different DIČ values in one ``create``/``write`` are now refused.**
  ``l10n_sk_dic`` and ``income_tax_id`` both inverse onto the same partner
  field, so a call naming both with different numbers was resolved by dict
  order — last one wins, silently, on a statutory identifier. Nothing in this
  repository does that, but an import or an RPC caller easily could. The same
  number in both is not a conflict.

* **Note for databases with child contacts carrying their own DIČ.** Making
  ``l10n_sk_dic`` a commercial field means a child contact takes its parent's
  value the next time the parent's commercial fields sync. That is the intended
  semantics — a contact person has no DIČ of their own; a separate taxpayer is
  its own company partner, not a child contact — but it does mean a
  child-specific value entered before this release will be replaced rather than
  kept.

* Depends on ``l10n_sk`` and declares ``countries: ["sk"]``. The dependency is
  required to override ``income_tax_id``, and it costs a Slovak database
  nothing: ``l10n_sk`` is ``countries: ['sk']`` with ``auto_install: ['account']``
  and ``ir_module.must_install`` gates on the company's country, so it is
  already installed anywhere this module belongs.

* ``19.0.2.0.0``: **breaking** for anything that installed ``l10n_sk_base``
  without ``l10n_sk``, which the new dependency now pulls in.
