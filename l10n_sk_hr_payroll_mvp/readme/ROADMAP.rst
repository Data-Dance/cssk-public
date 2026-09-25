Verification status
-------------------

* The export is validated against the official ``MVPP-v2026.xsd`` shipped in ``data/``.
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

* Only the regular-employment variant. Dohody and other irregular income go on
  the VPP form — install ``l10n_sk_hr_payroll_vpp``.
* Corrections (opravný / doplňujúci výkaz) are not modelled; a correction is
  produced by editing and regenerating, which does not set the correction
  markers the form provides.
* The fund mapping is by salary-rule code (np↔SICK, sp↔PENSION, ip↔DISABILITY,
  pvn↔UNEMPLOYMENT, up↔ACCIDENT, gp↔GUARANTEE, rfs↔RESERVEFUND,
  pfp↔SHORTTIME). A site that renames or re-splits those rules must revisit it.
