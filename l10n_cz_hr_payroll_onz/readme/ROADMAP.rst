Verification status
-------------------

* The export is validated against the official ``ONZ2022_20230616.xsd`` (with ``baseTypes2.xsd``) shipped in ``data/``.
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

* Two akce only: nástup and skončení. Změna and oprava actions are not
  modelled, so corrections must be filed through the portal.
* The optional insurer, pension and unemployment blocks are omitted.
* Events derive from the ``hr.version`` lifecycle, so back-dated or rewritten
  versions can produce registrations that do not match what was really filed.
