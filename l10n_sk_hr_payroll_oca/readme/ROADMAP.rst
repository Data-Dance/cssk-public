The following are not implemented yet (fields/parameters are present where
noted, but the payslip is computed as regular monthly employment):

* The seasonal-DoPČ OOP (762 €/mo) — the parameter is present but there is no
  field yet to flag a seasonal agreement, so the regular 200 € OOP is used.
* Case-specific dohodár exemptions for pensioners/students (e.g. health-insurance
  exemption, disability/unemployment exemption) beyond the modelled fund set.
* The sickness náhrada (SICK_COMP) now takes its sick days from the PN leave, but
  the denný vymeriavací základ (DVZ) is still supplied as the ``PN_DVZ`` input
  (it derives from the prior year's assessment base, not modelled here).

Deferred (out of scope for this pass):

* Monthly and quarterly statutory reports (výkazy) to the Sociálna poisťovňa and
  the health insurers. These require the official electronic formats
  (XML/e-podania) and are intentionally left out.
* The annual reconciliation of income tax (ročné zúčtovanie preddavkov na daň,
  §38) is implemented via the ``l10n.sk.tax.reconciliation`` model; the annual
  reconciliation of HEALTH insurance (ročné zúčtovanie poistného, §19 zák.
  580/2004) remains out of scope because it is performed by the health insurer,
  not the employer.

Known limitations / simplifications to verify against current law before
production use:

* Wage garnishment models a single claim per payslip; the pensioner variant
  (50% per dependant) and the ordering of several simultaneous claims of
  different priority are not modelled. The per-dependant amount (25% of the
  basic non-seizable amount) rounds to 99.44–99.45 € depending on the source.
* Sickness compensation (náhrada príjmu pri PN) is modelled as exempt from the
  odvody and, as a simplification, is NOT taxed on the payslip (in reality it is
  subject to income tax).
* Priemerný zárobok counts the GROSS line less the SK náhrada lines (rather than
  a from-scratch §118 wage classification), tests only the ≥168-hours branch (not
  the ≥21-days alternative), and drives the PN náhrada from the leave's WORKING
  days as a proxy for the statutory CALENDAR-day count of the first 10/14 days.

Verify the statutory figures against current law before production use.
