{
    "name": "CZ/SK Control Statement — Shared Framework",
    "version": "19.0.2.2.0",
    "summary": "Abstract framework for the Slovak KV DPH and Czech KH DPH VAT "
               "control statements: versioned templates, section/summary/"
               "reconciliation row mixins, move-line section assignment and an "
               "XSD-validated XML export pipeline.",
    "description": """
CZ/SK Control Statement — Shared Framework
==========================================

The country-neutral engine behind the Slovak **Kontrolný výkaz DPH (KV DPH)**
and Czech **Kontrolní hlášení (KH DPH)**. Country modules
(``l10n_sk_kv_dph`` / ``l10n_cz_kh_dph``) plug in their concrete section
sets, thresholds and XML schemas.

Deliberately depends on **Odoo core only** (``account``, ``mail``,
``l10n_cssk_core``) — **no** ``account.report`` / ``account_reports`` — so
the statement and its XML export are Community- and Enterprise-clean.

Provides
--------

* ``cssk.control.statement.version`` — versioned template + section registry +
  submission types + threshold (legislative changes ship as new version
  records, not new modules).
* ``cssk.control.statement`` — the statement aggregate (mail.thread; draft →
  preview → exported → submitted), with ``action_compute_lines`` and
  ``action_export_xml`` (QWeb render + ``lxml`` XSD validation).
* Three row mixins — detail / summary / reconciliation — for concrete section
  models to inherit.
* ``account.move.line`` — stored ``cssk_control_section_code`` (computed via a
  country-overridable resolver, **reverse-charge first**), multi-VAT override
  and ``cssk_control_rate_declared`` (the rate a tags-only line's source
  states, where the statutory line named none).
* ``account.tax`` — ``cssk_control_section_default`` + ``cssk_control_is_reverse_charge``.
* ``account.journal`` — default-section override.

See the ``l10n_cssk_kv_kh_base`` design note for the data model and the
section-resolution algorithm.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["account", "mail", "l10n_cssk_core",
        "l10n_cssk_submission_base"],
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "views/cssk_control_statement_version_views.xml",
        "views/cssk_control_statement_views.xml",
        "views/cssk_kv_kh_menus.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
}
