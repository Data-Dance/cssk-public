{
    "name": "Slovakia — VAT Return (Daňové priznanie k DPH)",
    "version": "19.0.1.12.0",
    "summary": "Slovak VAT return (DPHv25) — output/input lines wired to the "
               "l10n_sk tax tags, with FS SR DPH XML export. Built on the "
               "shared l10n_cssk_vat_return_base framework.",
    "description": """
Slovakia — VAT Return (Daňové priznanie k DPH)
==============================================

Concrete Slovak VAT return on top of ``l10n_cssk_vat_return_base``. Line
definitions mirror the **l10n_sk** DPH report tag formulas, so the per-line
values match what Odoo's own report would compute — but with a CE-clean
evaluator (no ``account_reports``).

Shipped lines (validate the full form + the net-payable computation with a SK
accountant):

* Output base/tax per category: ``sk01``, ``sk03`` (standard), ``sk05`` (reduced).
* Deductible tax: ``sk19``, ``sk20``.
* Aggregates: total output base/tax, total deductions, net VAT.

The net-payable lines that Odoo computes with ``sum`` / custom engines (sk_30+)
are out of scope of the simple tags+aggregate evaluator and need extended-engine
support or manual entry.

FS SR ``DPH`` XML export (template + stand-in XSD — replace with the official
schema before live filing).

Historical VAT rates (for history imports)
------------------------------------------

Generates the Slovak rates no longer in force — **20 %** (2011-01-01 to
2024-12-31) and **10 %** (2007-01-01 to 2024-12-31) — by cloning the whole
current-rate family, so every variant gets a twin: reverse charge, EU
acquisition, triangulation, import, customs, unpaid and the sale-side members.
Mapping a 2024 document onto today's 23 % is not a mapping decision but a
restatement, and a silent one: the base is the line amount, so only the tax
figure moves.

They are created **archived**, deliberately, so they cannot be picked when
raising today's invoice. Two consequences worth knowing:

* **They do not appear in a tax list, or in ``search()``, without
  ``active_test=False``.** The failure presents as "the migration did not run"
  rather than "you are not looking at them". They post, compute and carry
  their tags perfectly well — only *lookup* is affected.
* No historical twin is generated for a rate that has not changed. An
  intra-EU **supply**, for instance, is exempt with deduction under § 43 and
  has always been zero-rated, so ``0% EU S`` serves a 2024 document as it
  serves a 2026 one. The absence of a ``20% EU S`` is correct, not a gap.

Runs on install, on chart load and on upgrade; idempotent, and it adopts a
rate created by hand rather than duplicating it.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_cssk_vat_return_base", "l10n_sk", "l10n_sk_statutory"],
    "post_init_hook": "post_init_hook",
    "data": [
        "security/ir.model.access.csv",
        "report/l10n_sk_vat_return_templates.xml",
        "data/cssk_vat_return_version_data.xml",
        "data/cssk_vat_return_2024_version_data.xml",
        "data/cssk_vat_return_legacy_version_data.xml",
        "views/l10n_sk_par53b_views.xml",
    ],
    "installable": True,
}
