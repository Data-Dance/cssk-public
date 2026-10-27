Slovak **RLFO** (Registračný list fyzickej osoby) — the social-insurance
registration of employees filed to the Sociálna poisťovňa. It produces the
modern employee-only *hromadný* batch (root ``spRegListZec``, ns
``http://socpoist.sk/xsd/rlzec2026``) validated against the shipped
``RLZEC-v2026.xsd``.

Unlike the monthly/annual contribution statements this report is **not**
payslip-derived: its data comes from the employee and the ``hr.version``
lifecycle. Each RLFO record holds a batch of registration **events**, one per
employee:

* **Prihláška (PA)** — registration, carrying the insurance start date
  (``datVznikPoist``);
* **Odhláška (OD)** — de-registration, carrying the insurance start + end dates
  (``zanik``).

The ``typZec`` relationship code defaults from the employee's agreement type
and income regularity (employment → ``ZEC``; DoVP → ``ZECD1`` / ``ZECD1N``;
DoPČ → ``ZECD2`` / ``ZECD2N``; DoBPŠ → ``ZECD3`` / ``ZECD3N``, the ``N``
variants for an irregular income) and selects the right odhláška branch
(``zecPPOdhl`` / ``zecNPOdhl`` / ``zecDOdhl``). The birth number (``rc``) is
read from the employee's Identification No., the surname is the last word of
the name (separate first/last name fields win when installed) and the birth
date comes from the employee. The Sociálna poisťovňa variable symbol is
edited on the RLFO form.

Change (``ZM``), interruption (``PE``) and cancellation (``ZP``) events are not
modelled yet.
