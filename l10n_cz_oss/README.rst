=============================================
CZ OSS VAT Return — DAP OSS režim EU (OSSEI1)
=============================================

Czech layer of ``l10n_cssk_oss_base``: renders the quarterly OSS return as the
EPO form **OSSEI1** — *DAP OSS - režim EU - Přiznání k DPH platné od
1.7.2021*, structure 01.01.04 of 13. 12. 2021 — and validates it against the
official ``ossei1_epo2.xsd``.

* ``VetaD`` — quarter, year, DIČ (without ``CZ``), company name, ``trans`` A/N
  (nil return), and the partial-period dates when the registration began or
  ended during the quarter;
* ``VetaP`` — DIČ;
* ``VetaR`` — one row per member state × rate × goods (G) / services (S), rate
  type Z (standard) / S (reduced), base and VAT in EUR; Greece as ``EL``;
* ``VetaO`` — one correction per earlier quarter × member state (VAT, EUR,
  signed).

The schema is pinned in ``data/SCHEMA_VERSION`` (size, md5, structure version,
refresh procedure); a test fails when a bundled schema is not pinned or does
not match its pin.

Not covered: the non-Union (OSSNI1) and import (OSSII1) returns, and the MOSS
return for quarters before Q3 2021 (OSSDI1).

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
