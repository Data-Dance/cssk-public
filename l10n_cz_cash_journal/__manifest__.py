{
    "name": "Czechia — Peněžní deník (daňová evidence)",
    "version": "19.0.1.0.4",
    "summary": "Czech cash journal for daňová evidence (§ 7b ZDP): the členění "
               "vendors settled on, the peněžní deník, and the figures for "
               "Příloha č. 1 including oddíl D.",
    "description": """
Czechia — Peněžní deník
=======================

The Czech half of the cash-journal family. The engine lives in
``l10n_cssk_cash_journal_base``; this module supplies what Czech practice and
the tax return need.

**There is no statutory column layout here.** § 7b ZDP asks only for příjmy and
výdaje "v členění potřebném pro zjištění základu daně" plus a record of majetek
and dluhy, and the term *peněžní deník* appears nowhere in the income-tax act —
it is defined only for jednoduché účetnictví (§ 13b zákona o účetnictví), which
an OSVČ may not keep (§ 1f). So the členění here follows what the established
products do (POHODA, Money S3): daňové and nedaňové on both sides, průběžné
položky, and a separate non-cash part for odpisy and the § 23 adjustments.

**Pojistné podnikatele is NOT deductible in the Czech Republic**
(§ 25 odst. 1 písm. g ZDP), unlike Slovakia — which is why the two catalogues
are not translations of each other.

Provides the figures for **Příloha č. 1**: ř. 101 příjmy, ř. 102 výdaje, and
**oddíl D**, the start-and-end balances of hmotný majetek, hotovost, bankovní
účty, zásoby, pohledávky, ostatní majetek, dluhy, rezervy and mzdy — the de
facto "přehled o majetku a dluzích" that daňová evidence has no separate form
for. The year-end stock-take required by § 7b odst. 4 is recorded with it.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_cssk_cash_journal_base", "l10n_cz"],
    "data": [
        "security/ir.model.access.csv",
        "data/cssk_cash_category.xml",
        "report/l10n_cz_cash_journal_reports.xml",
        "report/penezni_denik_template.xml",
        "wizard/l10n_cz_cash_priloha_views.xml",
        "views/l10n_cz_cash_journal_menus.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
