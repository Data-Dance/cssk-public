==========================================
Slovakia — Financial Statements (Súvaha)
==========================================

Slovak balance sheet (Súvaha) on ``l10n_cssk_fs_base``. Account-code line
mapping + comparison period + XML export, computed CE-clean.

Status
======

**Functional skeleton.** A representative line set (asset side, equity &
liabilities side, totals) computes from SK account classes and exports to a
stand-in ``UZSUV`` XML (verified by a test: a balanced entry → assets 1000 =
equity 1000). To complete:

* The 3-column **Brutto / Korekcia / Netto** split, the full ~145-line Súvaha
  and **VZS** (P&L).
* Poznámky, mikro (UZMUJv14) variant.
* The official FS SR **UZPODv14** XSD + XML structure (the shipped XSD is a
  stand-in).
* **Accountant validation of the account→line mapping** (the current mapping is
  a draft starting subset).

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
