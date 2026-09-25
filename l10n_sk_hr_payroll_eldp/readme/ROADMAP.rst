Verification status
-------------------

* The export is validated against the official ``ELDP-v2015_1.3.xsd`` shipped in ``data/``.
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

* The pension assessment base ``vzDP`` is derived from the summed GROSS. It is
  NOT capped at the maximum assessment base and excluded periods are not
  deducted, so a high earner or an employee with unpaid/excluded time needs the
  figure checked by hand.
* One continuous insured period per employee per year. Employees with several
  spells, or with periods needing their own ELDP row, are not split.
* The 2015 schema vintage is the one in force; there is no back-catalogue for
  earlier years.
