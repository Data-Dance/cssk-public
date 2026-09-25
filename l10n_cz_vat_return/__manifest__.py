{
    "name": "CZ VAT Return (DPHDP3)",
    "summary": "Czech VAT return (přiznání k DPH / DPHDP3) on the shared VAT-"
               "return framework: line set mapped to the l10n_cz tax tags + "
               "the EPO Pisemnost/DPHDP3 XML export.",
    "description": """
CZ VAT Return (DPHDP3)
======================

The Czech country layer for the shared VAT-return framework
(``l10n_cssk_vat_return_base``). CE-clean — computes from the **core l10n_cz tax
tags** (no Enterprise ``account_reports`` dependency).

* Line set = the DPHDP3 attributes (obrat23/dan23/…), mapped to the l10n_cz tax
  tags (``VAT n Base`` / ``VAT n Tax``); the 48 tag-based lines auto-compute from
  the move-line tags.
* EPO **Pisemnost / DPHDP3** XML export (VetaD / VetaP / Veta1–Veta6), mirroring
  the Odoo EE export structure.

**Scope note (v1):** the 48 base/tax lines auto-compute; the deduction-claim
lines (krácení coefficient) and the totals are entered/reviewed by the accountant
(manual) — the inter-line totals can be auto-wired after accountant validation.
The official EPO XSD is not yet wired (export validates root element + is
well-formed); add it for submission-grade validation.

Historical VAT rates (for history imports)
------------------------------------------

Generates the Czech rates no longer in force — 20, 19, 15, 14, 10, 9 and 5 %,
back to 2004-05-01 when the current VAT Act took effect — by cloning the whole
current-rate family, so every variant gets a twin: reverse charge, EU
acquisition, export, non-deductible and the sale-side members. Each rate is
cloned from the family it belonged to, because DPHDP3 separates the standard
rate (lines 01/02, input 40) from the reduced one (03/04, input 41): cloning
15 % from the 21 % family would file a decade of reduced supplies as standard.
Mapping a 2023 document onto today's 12 % is not a mapping decision but a
restatement, and a silent one: the base is the line amount, so only the tax
figure moves.

They are created **archived**, deliberately, so they cannot be picked when
raising today's invoice. Two consequences worth knowing:

* **They do not appear in a tax list, or in ``search()``, without
  ``active_test=False``.** The failure presents as "the migration did not run"
  rather than "you are not looking at them". They post, compute and carry
  their tags perfectly well — only *lookup* is affected.
* No historical twin is generated for a rate that has not changed. An
  intra-EU **supply**, for instance, is exempt with deduction under § 64 and
  has always been zero-rated, so ``0% EU S`` serves a 2024 document as it
  serves a 2026 one. The absence of a ``20% EU S`` is correct, not a gap.

Runs on install, on chart load and on upgrade; idempotent, and it adopts a
rate created by hand rather than duplicating it.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.6.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_cssk_vat_return_base", "l10n_cz", "l10n_cz_statutory"],
    "post_init_hook": "post_init_hook",
    "data": [
        "report/dphdp3_report.xml",
        "data/dphdp3_version_data.xml",
    ],
    "installable": True,
}
