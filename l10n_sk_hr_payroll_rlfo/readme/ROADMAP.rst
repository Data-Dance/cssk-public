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

* Prihláška (PA), odhláška (OD) and one kind of zmena (ZM): the agreement OOP
  under § 227a zákona 461/2003 Z. z. Any other change and a storno
  (cancellation) are not modelled, and both are ordinary in practice — a
  corrected registration has to be filed through the portal.
* The OOP elements follow the schema and the act. The Sociálna poisťovňa had
  published no filling instructions for the two RLZEC 2027 elements when
  they were built (2026-11-20), and no file has been through its validator.
* ``typZec`` is defaulted from the employee's agreement type and income
  regularity when the employee is chosen, and not re-validated later. A
  pracovný pomer is always proposed as ``ZEC``; ``ZECN`` (irregular income in
  employment) has to be chosen by hand.
* Events are derived from the ``hr.version`` lifecycle, so a site that back-dates
  or rewrites versions can produce registrations that do not match what was
  really filed.
