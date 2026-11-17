=========
Changelog
=========

All notable changes to **l10n_sk_vehicle_tax** are documented here.

[Unreleased]
------------

- Keep test-framework imports out of normal production startup; the native
  Odoo test loader continues to discover the vehicle-tax suite.
- Bežný štart nenačítava testovací framework; testy naďalej objavuje natívny
  testovací loader Odoo.

[19.0.1.0.0] — 2026-11-16
-------------------------

Added
~~~~~

- Calendar-year DMVv25 calculations, original official XSD and common filing
  workflow, including corrective/additional returns and retained XML.
- Use native fleet.vehicle as the technical source. Store documentary EU
  categories, first registration, capacity/mass/axles and taxpayer facts on
  the fleet record, with reviewed snapshots on the tax workpaper.
- Add all company vehicles including archived disposals, without a logbook
  dependency. Refreshing changed source facts requires a new review.
- Pin every bundled XSD with byte-level size/hash tests.
- Actual liability event dates normalized to statutory month boundaries.
- Duplicate filed regular returns refused in Python and by a database index.
- Exact XML preserved while allowing same-content storage migration and tokens.
- Edition configuration restricted to system administrators; accounting users
  and managers get read access to fleet source records.
- Applicable XML rows and whole cm³; liability months always stated.
- Coverage of mass/capacity bands, ecological rates, age steps, corrections,
  weekend deadlines, account-user access and monetary totals.
- An independently reviewed business use/holding start and evidence is
  required; liability is never derived from fleet's default registration date.
- Fleet import adds prepared vehicles and keeps every skipped plate with its
  reason (unassigned company, exempt, unsupported) as an escaped list in the
  chatter, then refreshes the return.
- LNG propulsion kept when a fleet model supplies its default fuel type.
- The year shows without a thousands separator (``enable_formatting``) and
  the record name shows the filing type in the user's language.
- Czech catalogue.

Contributed by votrelec (cssk-public#26).
