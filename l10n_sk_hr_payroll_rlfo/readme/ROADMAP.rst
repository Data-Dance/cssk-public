Verification status
-------------------

* The export is validated against the official ``RLZEC-v2026.xsd`` shipped in ``data/``.
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

* Two event kinds only: prihláška (PA) and odhláška (OD). Zmena (change) and
  storno (cancellation) registrations are not modelled, and both are ordinary
  in practice — a corrected registration has to be filed through the portal.
* ``typZec`` is defaulted from the employee's agreement type and not validated
  against the actual insurance obligation.
* Events are derived from the ``hr.version`` lifecycle, so a site that back-dates
  or rewrites versions can produce registrations that do not match what was
  really filed.
