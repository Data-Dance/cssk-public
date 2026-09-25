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
