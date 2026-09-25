Verification status
-------------------

* The export is validated against the official ``VPP-v2026.xsd`` shipped in ``data/``.
  That checks the SHAPE of the file, not that the figures are the ones the Sociálna poisťovňa
  expects. No declaration produced here has been round-tripped through the
  real submission portal, so treat a passing export as necessary rather than
  sufficient, and reconcile the first live filing by hand.
* The test suite drives whichever payroll engine is installed in the database
  (OCA ``payroll`` or Enterprise ``hr_payroll``) and asserts against that one.
  There is no test asserting that the two engines produce IDENTICAL
  declarations from identical inputs — engine parity rests on the shared
  ``_collect_payslip_totals`` adapter rather than on evidence.
* A new form vintage means a new ``cssk.payroll.declaration.version`` record
  with its own QWeb template and XSD. Superseded vintages are not back-filled,
  so recomputing an old period needs the vintage that was in force then.

Not covered
-----------

* Scope is decided by ``l10n_sk_agreement_type`` being ``dovp`` or ``dopc``.
  An employer modelling agreements some other way gets an empty annex with no
  warning.
* ``typZec`` defaults to the irregular-income variant (ZECD1N / ZECD2N); the
  regular-income agreement variants are not selected automatically.
* Corrections are not modelled, as for the MVP form.
