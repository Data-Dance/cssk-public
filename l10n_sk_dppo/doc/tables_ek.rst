Tables E and K on the published paper form
========================================

The published MF/014309/2026-721 pattern applies when the last day of the
legal filing deadline falls after 31 December 2026, until replaced. This
includes the ordinary 2027 period filed in 2028 under the currently
published notice. It is not a claim that future replacement forms already
exist. The XML adapter for this pattern remains unavailable pending the
authority's publication; historical XML must not be relabelled.

An accountant enters reviewed supporting facts on the existing tax return,
then uses **Apply reviewed Tables E/K credits**. This atomically applies
rows 710 and 920 and recomputes the existing tax spine. Table E calculates
the official ordinary/hybrid ratios, limits and lower-of credit. Its
country breakdown appears in section IX. Non-EUR source taxes require an
evidenced section 31 conversion, printed as a separate annex. A lawful
section 45(2) estimate requires a different foreign tax period; a paid
source requires an actual payment date. Enter only tax permitted by the
applicable treaty and supported by income and payment/estimate evidence.

Table K records a positive original minimum-tax difference, original
minimum tax fully paid, prior usage, current usage and the reviewed first,
second or third subsequent tax period. Count tax periods, including short
periods, rather than calendar-year differences. In the first following
period there can be no prior-period usage. Source periods cannot overlap.
The total claim cannot exceed the native tax above the current minimum.
Unused credits expire after the third subsequent period, with an explicit
section IX explanation. K remains present when the current claim is zero
and an evidenced carry-forward exists. The official four source-period
rows are enforced; nothing is silently dropped.

The supporting facts do not determine treaty eligibility, establish that
a payment was actually made, or replace a filed original return. The
accountant retains those source documents, intervening-period evidence
and reviews section 46b(8) expiry events, including liquidation,
insolvency and legal succession. Existing declarations and ordinary
manual review of such legal facts remain required. There is no second
general ledger or tax register.

Edited inputs must be reapplied before PDF output or posting the native
591/341 provision. Inputs use the existing ordered parent locks,
state guard, accountant ACL and company rule. Exported historical PDF
attachments remain snapshots; recomputation/corrections create distinct
outputs. All 21 original form pages remain in every PDF, with clearly
marked continuations for country details or conversion evidence.

Primary sources and unmodified authority-asset hashes are recorded in
``static/forms/SOURCES.json``. The annex implementation is covered by
``tests/test_dppo_table_ek.py``.
