=========
Changelog
=========

Unreleased
==========

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

19.0.1.1.0 (2026-08-07)
=======================

* **Fixed: an irregular-income dohodár was registered with the wrong
  relationship code.** typ_zec keyed on the agreement type alone, so a DoVP
  or DoPČ paid irregularly was registered as ZECD1 / ZECD2 — the codes for
  regular monthly income. ZECD1N and ZECD2N were declared in the selection and
  reachable by hand, but nothing ever produced them.

  The Sociálna poisťovňa treats the two as different relationships: an
  irregular-income dohodár pays old-age and disability only, with no sickness,
  no unemployment and no short-time contribution. The payslip rules have keyed
  on that since 7533a7d; the registration did not, so the employee was given
  the wrong insurance scope from the day they were registered rather than on a
  single payslip. typ_zec now follows both the agreement type and
  l10n_sk_income_regular.

19.0.1.0.1 (2026-07-06)
~~~~~~~~~~~~~~~~~~~~~~~

* Normalized all user-facing strings to clean English (removed mixed-language
  parentheticals). Added a Slovak (``i18n/sk.po``) translation and the
  extraction template (``i18n/<module>.pot``).

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release: Slovak RLFO / RLZEC employee registration batch with
  prihláška (PA) and odhláška (OD) events built from the employee + hr.version
  lifecycle, validated against the official ``RLZEC-v2026.xsd``.
* ``typZec`` defaulted from the employee agreement type; odhláška branch
  (zecPPOdhl / zecNPOdhl / zecDOdhl) selected accordingly.

[19.0.1.1.1] — 2026-09-13
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

