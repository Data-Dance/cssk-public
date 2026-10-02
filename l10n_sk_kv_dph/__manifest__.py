{
    "name": "Slovakia — Kontrolný výkaz DPH (KV DPH)",
    "version": "19.0.2.1.0",
    "summary": "Slovak VAT control statement (Kontrolný výkaz DPH) — sections "
               "A.1–D.2 incl. D.1, with FS SR XML export. Built on the shared "
               "l10n_cssk_kv_kh_base framework.",
    "description": """
Slovakia — Kontrolný výkaz DPH (KV DPH)
=======================================

Concrete Slovak control statement on top of ``l10n_cssk_kv_kh_base``.

* Sections **A.1, A.2, B.1, B.2, B.3.1, B.3.2, C.1, C.2, D.1, D.2** — note we
  implement **D.1** (which Consystech and most vendors skip).
* SK move-line section resolver (reverse-charge first).
* FS SR ``KVDPH`` XML export (QWeb template + XSD slot on the version record).

Depends on ``l10n_sk`` (chart) and the shared framework — **no
account_reports**, so it works on Community and Enterprise, 18.0 and 19.0.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_cssk_kv_kh_base", "l10n_sk"],
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "report/l10n_sk_kv_dph_templates.xml",
        "data/cssk_control_statement_version_data.xml",
        "views/account_move_views.xml",
        "views/cssk_control_statement_views.xml",
        "views/product_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
