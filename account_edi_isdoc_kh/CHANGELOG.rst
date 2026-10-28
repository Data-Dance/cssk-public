=========
Changelog
=========

All notable changes to **account_edi_isdoc_kh** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.1.0.0] — 2026-10-27
-------------------------

Added
~~~~~

- Initial release. A Czech customer invoice or credit note in the domestic
  reverse charge (§ 92a ZDPH) is exported to ISDOC with
  ``LocalReverseCharge`` and the control statement's commodity code on each
  reverse-charge line, ``VATApplicable`` true, and its own VAT breakdown row
  marked ``LocalReverseChargeFlag``, apart from exempt supplies at 0 %. A
  reverse-charge line without a commodity code is refused for ISDOC.
