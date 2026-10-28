# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "ISDOC — Local Reverse Charge (KH commodity codes)",
    "version": "19.0.1.0.0",
    "summary": "ISDOC export of a Czech domestic reverse-charge invoice "
               "(§ 92a ZDPH) with LocalReverseCharge and the KH commodity code.",
    "description": """
ISDOC — Local Reverse Charge
============================

Bridge between ``account_edi_isdoc`` and ``l10n_cz_kh``.

A Czech customer invoice in the domestic reverse-charge regime (tuzemský
režim přenesení daňové povinnosti, § 92a ZDPH) is exported with the elements
ISDOC 6.0.2 defines for it:

* every reverse-charge line carries ``ClassifiedTaxCategory/LocalReverseCharge``
  with ``LocalReverseChargeCode`` — the kód předmětu plnění the control
  statement reports in A.1 / B.1, taken from the product or the reverse-charge
  tax exactly as ``l10n_cz_kh`` resolves it;
* its VAT breakdown row is kept apart from any exempt 0 % supply and marked
  ``LocalReverseChargeFlag``;
* ``VATApplicable`` is true: the supply is taxable, the customer pays the tax.

A reverse-charge line without a commodity code is refused for ISDOC, as the
control statement refuses it.

Installs itself when both modules are present.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["account_edi_isdoc", "l10n_cz_kh"],
    "auto_install": True,
    "installable": True,
}
