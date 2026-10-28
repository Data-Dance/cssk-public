=========
Changelog
=========

Unreleased
~~~~~~~~~~

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.1.1] — 2026-10-27
~~~~~~~~~~~~~~~~~~~~~~~~~

**Changed**

- **Slovak translation.** The correction and submission fields every declaration shares (*Correction Type*, *Correction Reference*, *Delivery*, *Submissions*) showed in English; they are translated now.

[19.0.1.1.0] — 2026-10-27
~~~~~~~~~~~~~~~~~~~~~~~~~

**Fixed**

- **Employee names.** The middle of a three-word name was dropped. The surname is now the last word and the first name everything before it; separate first/last name fields win when a module provides them.

**Added**

- The *Sociálna poisťovňa variable symbol* can be filled in on the ELDP form. Generation requires it, but it was on no form anywhere.
- ``data/SCHEMA_VERSION`` pins the bundled ``ELDP-v2015_1.3.xsd``, with a test that the bytes still match.


[19.0.1.0.3] — 2026-10-27
~~~~~~~~~~~~~~~~~~~~~~~~~

**Fixed**

- **datVzniku** and **datOd** carry the real start of employment (the start of the current uninterrupted run of contracts). The module read a field that does not exist in Odoo 19 and reported every employee as insured since 1 January.

19.0.1.0.1 (2026-07-06)
~~~~~~~~~~~~~~~~~~~~~~~

* Normalized all user-facing strings to clean English (removed mixed-language
  parentheticals). Added a Slovak (``i18n/sk.po``) translation and the
  extraction template (``i18n/<module>.pot``).

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release: annual Slovak ELDP (Evidenčný list dôchodkového poistenia),
  one ``eldpZec`` per employee with the year's pension assessment base and
  insured period, validated against the official ``ELDP-v2015_1.3.xsd``.
* Reuses the engine-neutral payslip adapter over a whole-year period; the
  pension base ``vzDP`` is derived from the summed GROSS.

[19.0.1.0.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Terms the translation catalogue never carried.** Strings that reach the
  user were absent from the template — a field with no ``string=``, a mixin
  field addressed to the abstract model's ``ir.model.fields`` row rather
  than each concrete one, or a whole category the offline exporter never
  emitted. An absent term cannot be translated and shows English in an
  otherwise Slovak screen. The template and the catalogues now carry them,
  and the Slovak is written.

