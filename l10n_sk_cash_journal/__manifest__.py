{
    "name": "Slovakia — Peňažný denník (jednoduché účtovníctvo / daňová evidencia)",
    "version": "19.0.1.0.0",
    "summary": "Slovak cash journal: the statutory členenie of opatrenie "
               "MF/27076/2007-74, the peňažný denník in its official column "
               "layout, and the DPFO typ B tabuľka 1 / 1a figures.",
    "description": """
Slovakia — Peňažný denník
=========================

The Slovak half of the cash-journal family. The engine lives in
``l10n_cssk_cash_journal_base``; this module supplies what the Slovak statute
says.

* **The členenie** (``data/cssk_cash_category.xml``) follows **opatrenie
  MF/27076/2007-74, § 4** — the columns of the statutory peňažný denník kept in
  jednoduché účtovníctvo: predaj tovaru, predaj výrobkov a služieb, ostatné
  príjmy; zásoby, služby, mzdy, poistné a príspevky, tvorba sociálneho fondu,
  ostatné výdavky; each side split into "zahŕňané do základu dane" and
  "neovplyvňujúce základ dane", plus priebežné položky. The same catalogue
  serves **daňová evidencia** (§ 6 ods. 11 ZDP), where the form is free but the
  členenie still has to be "potrebné na zistenie základu dane".
* **Poistné podnikateľa is a tax expense in Slovakia** (§ 19 ods. 3 písm. i
  ZDP), unlike the Czech Republic — which is the clearest single difference
  between the two catalogues.
* **The peňažný denník report** renders the book in the statutory grid, with
  the running cash and bank balances the opatrenie requires (§ 4 ods. 10).
* **DPFO typ B figures** (``l10n.sk.cash.dpfo``): tabuľka 1 príjmy/výdavky,
  tabuľka 1a start-and-end balances for daňová evidencia (zostatková cena HM
  and NM, zásoby, pohľadávky, záväzky, finančný majetok), and tabuľka 1b for a
  flat-rate payer.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_cssk_cash_journal_base", "l10n_sk"],
    "data": [
        "security/ir.model.access.csv",
        "data/cssk_cash_category.xml",
        "report/l10n_sk_cash_journal_reports.xml",
        "report/penazny_dennik_template.xml",
        "wizard/l10n_sk_cash_dpfo_views.xml",
        "views/l10n_sk_cash_journal_menus.xml",
    ],
    "installable": True,
}
