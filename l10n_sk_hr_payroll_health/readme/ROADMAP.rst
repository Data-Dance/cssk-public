Verification status
-------------------

* The export is validated against the official ``514-2023.xsd`` shipped in ``data/``.
  That checks the SHAPE of the file, not that the figures are the ones the health insurer
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

Known limitation — the published schema is defective
----------------------------------------------------

``514-2023.xsd`` cannot validate any real instance: it carries single-character
``[0-9]`` patterns under multi-character ``minLength`` constraints and
impossible integer bounds. The XSD is shipped and loaded, but run as a
NON-FATAL check; the authoritative gate is well-formedness plus structural
conformance to the schema's element model. If the insurers publish a corrected
schema, tighten this back to a hard ``assertValid``.

Not covered
-----------

* Insurer selection (VšZP 25 / Dôvera 24 / Union 27) is company configuration
  or a per-declaration choice; there is no validation that the employees in
  the annex actually belong to the selected insurer.
* Corrections and annulment filings are not modelled.
