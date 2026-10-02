=================================================
SK OSS VAT Return — úprava pre Úniu (DPOSS_EUv01)
=================================================

Slovak layer of ``l10n_cssk_oss_base``: renders the quarterly OSS return as the
Finančná správa eForm **DPOSS_EUv01** — *Daňové priznanie k DPH - Úprava pre
Úniu* — and validates it against the official ``dposs_eu01.xsd``.

The XML is the EU-wide ``OSSVATReturnMSCON`` structure
(``urn:ec.europa.eu:taxud:frsr:vatunion:v1.0``), emitted with the ``vun:``
prefix because the eForm's XML loader looks elements up by qualified name:

* ``TraderID`` — IČ DPH with the ``SK`` prefix; ``Period`` — year, quarter and
  the partial-period dates; ``NilVatReturn`` 1/0;
* ``MSIDSupplies`` (supplied from Slovakia) and ``MSESTSupplies`` (from an
  establishment or dispatch state elsewhere; manual rows), each with supply
  type, member state (Greece as ``EL``), rate and its type, base and VAT;
* ``Corrections`` per earlier quarter × member state;
* the grand totals, per-member-state ``Balances`` including corrections, and
  ``TotalVATAmountDue`` = the positive balances only, as the eForm computes it.

The schema is pinned in ``data/SCHEMA_VERSION`` (size, md5, refresh
procedure); a test fails when a bundled schema is not pinned or does not match
its pin.

Not covered: the non-Union and import returns.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
