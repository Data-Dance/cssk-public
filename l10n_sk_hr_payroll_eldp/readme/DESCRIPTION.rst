Slovak **ELDP** (Evidenčný list dôchodkového poistenia) — the annual
per-employee pension record filed to the Sociálna poisťovňa as the *hromadný*
batch (root ``spELDPZec``, ns ``http://socpoist.sk/xsd/eldpzec``).

For each employee it aggregates the calendar year's pension assessment base
(vymeriavací základ dôchodkového poistenia) and the insured period, producing
one ``eldpZec`` element per employee. The reporting period spans the whole year
(1 Jan – 31 Dec of the selected year); every payslip of the year is collected
through the shared ``l10n_cssk_payroll_declaration_base`` adapter, and the
annual pension base ``vzDP`` is taken from the summed GROSS. The exported XML is
validated against the shipped ``ELDP-v2015_1.3.xsd``.

Engine-neutral: it works on both the ``payroll`` engine and the
``hr_payroll`` engine.

The employer identifier ``icz`` reuses the company's ``Sociálna poisťovňa VS``,
the surname/first-name are split from the employee name, and the insured period
(``datVzniku`` / ``datZaniku`` / ``trva``) is derived from the employee's hire
and departure dates — review these against your master data before filing.
