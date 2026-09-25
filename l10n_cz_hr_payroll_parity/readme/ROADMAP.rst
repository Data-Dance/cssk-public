* The scenarios cover the absence path and the employer-side obstacles. The
  income-tax bands, the slevy and the annual reconciliation are still asserted
  only inside each engine's own suite.
* Declaration parity covers the PVPOJ (monthly) and the ELDP (annual).
* The Vyúčtování is NOT asserted, and deliberately so: its Part I reports
  the tax advance BEFORE the sleva na poplatníka where the payslip
  withholds it after, and which of the two the form wants is question 6
  in docs/cz-otazky-pro-mzdoveho-odbornika.md. Asserting the current
  figure would bless a number nobody has checked.
* The ONZ is event-shaped (registration on hire) rather than
  payslip-derived, so it needs a different kind of assertion — the same
  situation as the Slovak RLFO.

Why the ONZ has no declaration-parity scenario
==============================================

The ONZ renders from the employee and the ``hr.version`` lifecycle — birth
number, contract start and end, the OSSZ identifiers — none of it
engine-specific, so both engines produce identical output by construction and
a cross-engine scenario would assert nothing.

Its own suite already covers the event shape properly: ``act`` 1 for nástup
and 2 for skončení, the employer and client identifiers, the job dates
(``fro`` set and ``to`` absent on a nástup, ``to`` set on a skončení), and an
XSD validation of the whole document.

Engine-seam audit, 2026-08-07
=============================

``tools/diff_engine_seam.py cz`` reported eleven shared methods diverging.
Read one by one, they resolve to:

* **One real bug, in the SLOVAK module.** Comparing the two countries showed
  the CZ average-earnings search filtering payslips on ``done`` where the SK
  one accepted ``verify`` — the OCA engine's Waiting state, computed but not
  confirmed. §134 counts the wage *zúčtovaná* in the determining period, so
  the Slovak side was letting a half-finished month move every náhrada in the
  next quarter. Fixed in 00dfaa7. The cross-ENGINE audit had already passed
  that method; it took comparing the two COUNTRIES to see it.
* **One tolerance gap, now closed.** ``_l10n_cz_probable_hourly`` fell back to
  the employee's own calendar on Enterprise but not on OCA, so a version
  without a calendar returned 0.0 there and floored every náhrada to the
  minimum wage. OCA now has the same fallback.
* **Nine differences that are the engines' own vocabulary** and are right as
  they stand: ``done`` against ``validated``/``paid`` for payslip states,
  ``_get_parameter_value`` against ``_get_parameter_from_code``, a free-form
  input ``code`` against an ``input_type_id``, ``contract`` against
  ``version``, and three cases of pure formatting.

The whitelisted contract-template fields are identical on both sides, unlike
the Slovak pair where three fields exist only on OCA.

Note the tool's reach: it diffs Python methods, so an XML rule body is invisible
to it. The ten-cent meal divergence fixed in d989909 was found by a different
check entirely (``tools/find_unproduced_selections.py``).
