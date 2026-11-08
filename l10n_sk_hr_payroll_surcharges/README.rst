===============================================
Slovakia — Wage Surcharges (príplatky) — Base
===============================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Engine-neutral statutory wage surcharges for night, Saturday, Sunday, public-holiday, overtime, difficult-conditions and standby work (§§ 121–123 Zákonníka práce), plus the six stupne náročnosti minimum wage claims and the top-up to them.**

Statutory Slovak wage surcharges (mzdové zvýhodnenia / príplatky) as an
engine-neutral base, shared by the OCA ``payroll`` and Odoo Enterprise
``hr_payroll`` bridges.

Covers every surcharge the Zákonník práce mandates:

* night work (§ 122a), Saturday (§ 122b) and Sunday (§ 122c) work,
* work on a public holiday (§ 122) and overtime (§ 121),
* difficult working conditions (§ 123) and inactive standby away from the
  workplace (§ 96 ods. 5),

together with the six *stupne náročnosti* minimum wage claims (§ 120) and the
top-up that brings a sub-minimum wage up to the claim for the job's level.

Every percentage and every amount is a dated data record, so a statutory
change is a data change rather than a code change.

.. rubric:: Configuration

Set the job's difficulty level and the surcharge flags on the employee's
contract (Slovak Wage Surcharges group on the contract form):

* **Stupeň náročnosti** — the § 120 level of the job, driving the minimum wage
  claim. Level 1 is the plain minimum wage.
* **Riziková práca** — raises the night surcharge to 50 % and overtime to 35 %,
  and rules out the reduced night rate.
* **Reduced night / Saturday / Sunday rate agreed** — tick where a collective
  agreement sets the lower statutory floor allowed by § 122a ods. 3,
  § 122b ods. 2 or § 122c ods. 2.

To pay more than the statutory minimum, create a new dated record under
*Employees → Configuration → Slovak Wage Surcharges → Surcharge Rates* rather
than editing the salary rules.

The hours themselves come from the payslip: a worked-days line carrying the
surcharge code where the work-entry stack is in use, otherwise a payslip input
of the same code whose amount is read as a number of hours.

.. rubric:: Known issues / Roadmap

* Base pay for hours worked on a public holiday is not added. Only the § 122
  uplift is computed, because whether those hours are already carried by BASIC
  depends on how the site models public holidays in the resource calendar.
  Overtime is the exception and does get an explicit base-pay line, since
  overtime hours always fall outside the scheduled time a monthly salary pays
  for.
* Overtime base pay is valued at average earnings. That is the usual Slovak
  practice for a monthly-salaried employee, but an employer whose contracts
  state an hourly rate should override the ``NADCAS_MZDA`` rule.
* Hours are taken from payslip inputs, not from work-entry types, and no
  work-entry types are shipped. Night, Saturday, Sunday and
  difficult-conditions hours OVERLAY ordinary working time — they are the same
  hours seen through a second lens — so a work-entry type carrying those codes
  would move them out of ``WORK100`` and prorate the basic wage down. A site
  that models them correctly (a work entry carrying the surcharge code IN
  ADDITION to the ordinary one) is supported: the payslip mixin prefers a
  worked-days line of that code over the input.
* The reduced night / Saturday / Sunday rates are contract-level flags. The
  statute ties them to a collective agreement, so there is no check that one
  exists.
* § 96 standby is modelled only as the inactive part performed away from the
  workplace. Inactive standby AT the workplace counts as working time and is
  paid as such, which this module does not attempt to detect.
* Surcharges for work in a "sťažené prostredie" (§ 123) are a single rate; the
  hazard-specific rates some collective agreements set are not modelled.
* Only the percentage regime in force from 1 June 2023 is shipped. Recomputing
  a period before that date needs a rate record expressing the old fixed euro
  amounts, which these percentage fields cannot hold.

.. rubric:: Module facts

- **Technical name:** ``l10n_sk_hr_payroll_surcharges``
- **Version:** 18.0.1.2.0
- **Licence:** AGPL-3
- **Requires:** ``hr_contract``, ``l10n_sk_hr_payroll_base``

Authors: Data Dance s.r.o.
