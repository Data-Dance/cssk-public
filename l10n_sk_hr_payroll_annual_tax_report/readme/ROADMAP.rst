Verification status
-------------------

* The export is validated against the official ``rh2023.xsd`` shipped in ``data/``.
  That checks the SHAPE of the file, not that the figures are the ones the Finančná správa
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

* The per-employee annex (Časť V) is generated for every employee with
  payslips in the year. Employees taxed only by withholding (zrážková daň),
  and non-resident specifics, are not separated out.
* Opravné / dodatočné hlásenie markers are not set.
