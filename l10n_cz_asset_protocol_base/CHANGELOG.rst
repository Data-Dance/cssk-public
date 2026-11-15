=========
Changelog
=========

All notable changes to **l10n_cz_asset_protocol_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-11-15
-------------------------

Added
~~~~~

- Czech asset protocols, engine-neutral part: the protokol o zařazení
  dlouhodobého majetku do užívání and the protokol o vyřazení dlouhodobého
  majetku as one set of QWeb templates, and the mixin
  ``l10n.cz.asset.protocol.mixin`` with the data they need (inventární číslo,
  místo umístění, odpovědná osoba, poznámka, důvod a způsob vyřazení, the two
  protocol dates). Both documents carry the particulars of § 11 odst. 1
  zákona č. 563/1991 Sb.: the designation ZP- or VP- with the inventory
  number, the date of making out, the date of the transaction, the amounts
  and signature lines for the person responsible for the transaction and
  the person responsible for posting it. The disposal methods follow Český
  účetní standard pro podnikatele č. 013, bod 5.4. Where ``account_asset_tax``
  is installed, the commissioning protocol also prints the odpisová skupina
  and the method of tax depreciation.
