Verification status
-------------------

* The export is validated against the official ``PVPOJ25.xsd`` (with ``baseTypes2.xsd``) shipped in ``data/``.
  That checks the SHAPE of the file, not that the figures are the ones the ČSSZ
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

* The part-time premium-discount annex (``slevaZamestnanci``, § 7a) is omitted.
  The CZ payroll modules do compute the discount, but wiring the per-employee
  annex rows into this form is not done — an employer claiming the discount
  must complete that part manually.
* Opravný přehled markers are not set.
