{
    "name": "Slovakia — Súhrnný výkaz (EC Sales List)",
    "version": "19.0.1.2.2",
    "summary": "Slovak EC sales list (Súhrnný výkaz) — codes 0/1/2 (goods / "
               "triangulation / services), FS SR SDV XML export. Built on the "
               "shared l10n_cssk_ec_summary_base framework.",
    "description": """
Slovakia — Súhrnný výkaz (EC Sales List)
========================================

Concrete Slovak EC sales list on top of ``l10n_cssk_ec_summary_base``.

* Transaction codes: **0** = goods (dodanie tovaru), **1** = triangulation
  (trojstranný obchod – prostredná osoba), **2** = services (dodanie služby).
* FS SR ``SDV`` XML export (template + stand-in XSD; see the base module note
  on replacing it with the official schema before live filing).

Tag the intra-EU supply taxes with ``account.tax.cssk_ec_summary_code`` (the
relevant 0 %% intra-community goods/services taxes) so supplies are picked up.

Depends on ``l10n_sk`` + the shared framework — no ``account_reports`` — so it
runs on Community and Enterprise, 18.0 and 19.0.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_cssk_ec_summary_base", "l10n_sk", "l10n_sk_statutory"],
    "data": [
        "report/l10n_sk_ec_sales_templates.xml",
        "data/cssk_ec_summary_version_data.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
