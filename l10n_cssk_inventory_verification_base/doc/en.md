---
title: CZ/SK Inventory Verification — Booking of Differences (Base)
summary: The shared code that books the differences found by a Slovak inventarizácia or a Czech inventarizace as a journal entry in the period verified.
verified: 19.0.1.0.0
family: l10n_sk_inventory_verification#differences
---

Holds the logic both inventory verification modules share: the settlement lines of a difference (shortage, loss within the norm, surplus, claim against the liable person), the check that they explain the whole difference of a count sheet, the draft journal entry dated in the period verified, and its deletion or reversal when the record is reopened. It also refuses to post such an entry into a locked period, where Odoo would otherwise move it to another accounting period.

It has no screens or settings of its own and installs automatically with [module:l10n_sk_inventory_verification](module:l10n_sk_inventory_verification) or [module:l10n_cz_inventory_verification](module:l10n_cz_inventory_verification). Which account answers which difference is decided by those two modules.
