Changelog
=========

[Unreleased]
============

[19.0.1.1.0] — 2026-11-09
==========================

Added
~~~~~

- Use native fleet.vehicle as the technical source. Store documentary EU
  categories, first registration, capacity/mass/axles and taxpayer facts on
  the fleet record, with reviewed snapshots on the tax workpaper.
- Add all company vehicles including archived disposals, without a logbook
  dependency. Refreshing changed source facts requires a new review.
- Pin every bundled XSD with byte-level size/hash tests.

Fixed
~~~~~

- Normalize actual liability event dates to statutory month boundaries.
- Prevent duplicate filed regular returns in Python and with a database index.
- Preserve exact XML while allowing same-content storage migration and tokens.
- Restrict edition configuration to system administrators. Give accounting
  users and managers read access to fleet source records.
- Correct applicable XML rows and whole cm³; always state liability months.
- Expand coverage of mass/capacity bands, ecological rates, age steps,
  corrections, weekend deadlines, account-user access and monetary totals.

[19.0.1.0.0] — 2026-11-09
==========================

Added
~~~~~

- Calendar-year DMVv25 calculations, original official XSD and common filing
  workflow, including corrective/additional returns and retained XML.
