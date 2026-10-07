{
    "name": "SK Corporate Income Tax Return (DPPO)",
    "summary": "Slovak DPPO return on the income-tax framework: full r-line set "
               "+ header mapping + XSD-validated XML export against the official "
               "dppo2025 schema.",
    "description": """
SK Corporate Income Tax Return (DPPO)
=====================================

The Slovak country layer for the income-tax framework
(``l10n_cssk_income_tax_base``). Provides the **DPPOv25** form:

* The full body line set (r100 … r1192) as version data; ``r100`` (výsledok
  hospodárenia pred zdanením) is computed from the P&L, the rest are entered by
  the accountant (override UI).
* Header mapping from the company (DIČ, IČO, obchodné meno, sídlo, zdaňovacie
  obdobie, typ priznania).
* The official **dppo2025.xsd** is vendored and the XML export is validated
  against it.

**Scope note:** v1 auto-computes the accounting result and produces a
schema-valid XML; the accounting→tax transformation (the adjustment lines, loss
deduction, tax credits, minimum tax) is the accountant's domain and is entered
manually. The inter-line computation formulas need accountant validation before
being automated.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.4.3",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_cssk_income_tax_base", "l10n_sk", "l10n_sk_base"],
    "data": [
        "report/dppo2013_report.xml",
        "report/dppo2014_report.xml",
        "report/dppo2015_report.xml",
        "report/dppo2017_report.xml",
        "report/dppo2018_report.xml",
        "report/dppo2019_report.xml",
        "report/dppo2020_report.xml",
        "report/dppo2021_report.xml",
        "report/dppo2022_report.xml",
        "report/dppo2024_report.xml",
        "report/dppo_report.xml",
        "data/dppo_version_2013_data.xml",
        "data/dppo_version_2014_data.xml",
        "data/dppo_version_2015_data.xml",
        "data/dppo_version_2017_data.xml",
        "data/dppo_version_2018_data.xml",
        "data/dppo_version_2019_data.xml",
        "data/dppo_version_2020_data.xml",
        "data/dppo_version_2021_data.xml",
        "data/dppo_version_2022_data.xml",
        "data/dppo_version_2024_data.xml",
        "data/dppo_version_data.xml",
    ],
    "installable": True,
}
