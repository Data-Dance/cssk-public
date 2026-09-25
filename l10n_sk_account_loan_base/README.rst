=======================
SK Lízing — účty (base)
=======================

Engine-neutral company defaults for Slovak *finančný prenájom* (leasing) and loans,
wired to the ``l10n_sk`` chart of accounts.

Account mapping:

* long-term liability → **474000** Záväzky z nájmu
* current portion     → **474100** Lízing (bežná časť)
* interest expense    → **562000** Úroky
* leased asset        → **022000** Samostatné hnuteľné veci a súbory hnuteľných vecí

New companies receive the mapping when the SK chart loads (via the chart template);
existing SK companies get it on install (post-init hook, which fills only empty
fields and so never overwrites a mapping the accountant has changed). The accounts
are editable in *Settings ▸ Accounting ▸ Slovak leasing*.

Why a separate base
===================

The two editions run **different, colliding engines**:

* **Community** — OCA ``account_loan`` + ``account_leasing``
* **Enterprise** — Odoo ``account_loans``

Both declare ``account.loan`` **and** ``account.loan.line``, with different field
names and different posting semantics, so exactly one may be installed — Odoo
refuses the combination outright (``account_loan`` carries an ``excludes``).

This module therefore holds everything that is *Slovak* rather than
*engine-specific*: the four account **roles** and their chart mapping. The two
bridges map the roles onto whichever engine is present:

============== ================================= ===========================
Role           Community (``…_oca``)             Enterprise (``…_ee``)
============== ================================= ===========================
long_term      ``long_term_loan_account_id``     ``long_term_account_id``
short_term     ``short_term_loan_account_id``    ``short_term_account_id``
interest       ``interest_expenses_account_id``  ``expense_account_id``
leased_asset   ``leased_asset_account_id``       — (uses ``asset_group_id``)
============== ================================= ===========================

It depends on ``l10n_sk`` only and declares no loan models, so it is safe on either
edition. Licensed **LGPL-3** so that both the AGPL Community bridge and the
proprietary Enterprise bridge can import it — the same arrangement as
``l10n_cssk_intrastat_base``.

The parity invariants (twin pairing, engine exclusivity, and that this base reaches
neither engine) are asserted by ``tools/check_module_parity.py``.

Honesty flag
============

The mapping follows the l10n_sk chart's own naming — the chart ships **474100
"Lízing (bežná časť)"** explicitly — but it wants **accountant sign-off** like every
other statutory mapping in this collection, in particular the long-term/current
split policy.

Note also that only *finančný prenájom* belongs here. **Operatívny prenájom is not a
loan**: it is a period expense, handled by časové rozlíšenie
(``l10n_sk_account_cutoff``).

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
