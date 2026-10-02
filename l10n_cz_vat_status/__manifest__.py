# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ VAT Status (plátce / identifikovaná osoba / neplátce)",
    "summary": "The Czech company's own VAT registration status over time, "
               "and what it does to invoices, bills, DPHDP3 and the "
               "kontrolní hlášení.",
    "description": """
CZ VAT Status
=============

Records which VAT status the company had on which days — **plátce** (§ 6–6f),
**identifikovaná osoba** (§ 6g–6l) or **neplátce** — and applies it to every
document by its DUZP:

* a neplátce charges no VAT and deducts none: input VAT goes to the cost;
* an identifikovaná osoba charges no domestic VAT, deducts nothing, and still
  self-assesses on intra-Community acquisitions and on services received
  from abroad (§ 108 odst. 2 and 3), without a deduction;
* DPHDP3 ``typ_platce`` is P / I / N accordingly;
* no kontrolní hlášení for days the company was not a plátce (§ 101c);
* the invoice PDF does not present a non-payer's document as a daňový doklad.

With no history recorded nothing changes: the company is a plátce, exactly as
before this module was installed. See README.rst.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.1.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": [
        "l10n_cz",
        "l10n_cssk_core",
        "l10n_cz_statutory",
        "l10n_cz_vat_return",
        "l10n_cz_kh",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "views/res_company_views.xml",
        "views/account_move_views.xml",
        "views/account_tax_views.xml",
        "report/report_invoice.xml",
    ],
    "installable": True,
}
