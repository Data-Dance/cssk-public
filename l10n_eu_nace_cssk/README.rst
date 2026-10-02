==========================================
EU NACE: Rev. 2.1 and the Czech subclasses
==========================================

OCA's ``l10n_eu_nace`` imports EU NACE **Rev. 2** as partner industries. Czech and
Slovak registers moved to **Rev. 2.1** for 2025/2026, and Rev. 2 and Rev. 2.1 reuse
codes with different meanings (programming is ``62.01`` in Rev. 2, ``62.10`` in
Rev. 2.1). This module:

* lets the import wizard fetch **NACE Rev. 2.1** from the same EU vocabulary
  service (default) or Rev. 2;
* keeps the versions apart: each industry carries its NACE version and its code
  as data, not only as the prefix of its name. Industries imported before this
  module are tagged Rev. 2 on install. The other version can be archived at import;
* adds the **716 CZ-NACE 2025 subclasses** (the fifth, national digit) under
  their Rev. 2.1 classes, in Czech and English. Slovakia has no national level
  under Rev. 2.1, so nothing is added for it;
* links the partner's NACE code (``partner_nace``) to its industry: a code sets
  the industry (the subclass, else its class) unless a non-NACE industry was
  chosen, and picking a NACE industry fills the code.

The CZ subclasses come from the Czech Statistical Office's codelist CZ-NACE 2025
(``kodcis`` 80143, open data), exported 2026-09-29 to
``data/cz_nace_2025_subclasses.csv`` (716 rows, md5
``f1263818cdc809fee6a0228b580eae7d``). Refresh: download levels 5 of
``https://apl2.czso.cz/iSMS/do_cis_export?kodcis=80143&typdat=0&cisjaz=203&format=2&separator=%2C``
(Czech) and ``cisjaz=8260`` (English).
