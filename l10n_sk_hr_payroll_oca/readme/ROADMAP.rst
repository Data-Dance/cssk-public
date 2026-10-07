The following are not implemented yet (fields/parameters are present where
noted, but the payslip is computed as regular monthly employment):

* The seasonal-DoPČ OOP (762 €/mo) — the parameter is present but there is no
  field yet to flag a seasonal agreement, so the regular 200 € OOP is used.
* Case-specific dohodár exemptions for pensioners/students (e.g. health-insurance
  exemption, disability/unemployment exemption) beyond the modelled fund set.
* The sickness náhrada (SICK_COMP) now takes its sick days from the PN leave, but
  the denný vymeriavací základ (DVZ) is still supplied as the ``PN_DVZ`` input
  (it derives from the prior year's assessment base, not modelled here).

Statutory reporting is NOT part of this module — it lives in a separate,
engine-neutral family built on ``l10n_cssk_payroll_declaration_base``, each
module shipping the official XSD and validating its export against it:

* ``l10n_sk_hr_payroll_mvp`` — monthly Mesačný výkaz poistného a príspevkov
  (Sociálna poisťovňa), and ``l10n_sk_hr_payroll_vpp`` for dohody.
* ``l10n_sk_hr_payroll_health`` — monthly Mesačný výkaz preddavkov na poistné
  (dávka 514) for the health insurers.
* ``l10n_sk_hr_payroll_monthly_tax_overview`` / ``l10n_sk_hr_payroll_annual_tax_report`` — the monthly
  Prehľad and the annual Hlásenie o vyúčtovaní dane (Finančná správa).
* ``l10n_sk_hr_payroll_rlfo`` — RLFO/RLZEC registration events.
* ``l10n_sk_hr_payroll_eldp`` — the annual ELDP pension record.

Wage surcharges (mzdové zvýhodnenia / príplatky) for night, Saturday, Sunday,
public-holiday, overtime, difficult-conditions and standby work, and the
minimum wage claims for the six stupne náročnosti, are likewise a separate
family: install ``l10n_sk_hr_payroll_surcharges_oca`` (it pulls in the
engine-neutral ``l10n_sk_hr_payroll_surcharges`` base and installs itself
automatically alongside this module).

Deferred (out of scope for this pass):

* The annual reconciliation of income tax (ročné zúčtovanie preddavkov na daň,
  §38) is implemented via the ``l10n.sk.tax.reconciliation`` model; the annual
  reconciliation of HEALTH insurance (§19 zák. 580/2004) remains out of scope
  because it is performed by the health insurer, not the employer.

Known limitations / simplifications to verify against current law before
production use:

* Wage garnishment: install ``l10n_cssk_hr_payroll_garnishment_base`` (plus the
  engine bridge) for the full multi-claim waterfall, the pensioner variant
  (50 % per dependant), the maintenance-of-a-minor and administrative-fine
  bases, an order register, balance tracking, remittance to the bailiff and the
  statutory employer notices. Without it the rule falls back to a single
  input-driven claim per payslip — priority claims are still computed on the
  correct 100 % ŽM base, but simultaneous claims are not ordered. The
  per-dependant amount (25 % of the basic non-seizable amount) rounds to
  99.44–99.45 € depending on the source.
* Sickness compensation (náhrada príjmu pri PN) is modelled as exempt from the
  odvody and, as a simplification, is NOT taxed on the payslip (in reality it is
  subject to income tax).
* Priemerný zárobok counts the GROSS line less the SK náhrada lines (rather than
  a from-scratch §118 wage classification), tests only the ≥168-hours branch (not
  the ≥21-days alternative), and drives the PN náhrada from the leave's WORKING
  days as a proxy for the statutory CALENDAR-day count of the first 10/14 days.

Verify the statutory figures against current law before production use.
