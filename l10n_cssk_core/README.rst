==================================
CZ/SK Localization — Shared Core
==================================

Country-neutral foundation for the Czech & Slovak statutory localization
(``l10n_cssk_*`` / ``l10n_sk_*`` / ``l10n_cz_*``).

Depends on **Odoo core only** (``account`` + ``mail``) — no ``account_reports``,
no OCA report engine — so it installs on Community and Enterprise, 18.0 and 19.0.

Provides
========

* ``cssk.tax.authority`` — tax-office registry (submission code for XML).
* ``cssk.person.type`` — person / entity-type catalogue.
* ``res.company`` / ``res.partner`` field extensions.
* Security + menu scaffolding.

Status
======

**Skeleton.** Models, fields, views and security are in place. To do:

* Seed country tax-authority and person-type data (in the country modules).
* Wire a Settings block (see ``views/res_config_settings_views.xml``).
* Add hook-point glue for the customer's own components (PAY by Square, ARES).

Pending validation by CZ/SK accountants.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
