# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ/SK Inventory Verification — Booking of Differences (base)",
    "summary": "Country-neutral engine that turns the differences found by an "
               "inventarizácia / inventarizace into a journal entry dated in "
               "the period verified, and takes it back when the record is "
               "reopened.",
    "description": """
CZ/SK Inventory Verification — Booking of Differences (base)
============================================================

The shared half of ``l10n_sk_inventory_verification`` and
``l10n_cz_inventory_verification``. It has no screens and no models of its
own: three abstract models the two country modules build their records on.

* **The settlement of a difference** — a line saying what part of a count
  sheet's difference is a shortage, a loss within the norm or a surplus, on
  which account it sits and against which account it is booked, plus the
  claim raised against the person liable.
* **The count sheet's side** — how much of its difference the lines explain,
  what remains, and the statement that a difference is deliberately not
  booked from here (with the reason).
* **The exercise's side** — proposing the lines, creating the journal entry
  **in draft**, dated in the period being verified (SK § 30 ods. 7 zákona
  431/2002, CZ § 30 odst. 11 zákona č. 563/1991 Sb.), and deleting or
  reversing it when the exercise is reopened.

Which account answers which difference is the country module's business; the
engine only asks it.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["account"],
    "data": [],
    "installable": True,
}
