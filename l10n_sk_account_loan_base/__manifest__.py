# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "SK Lízing — účty (base)",
    "summary": "Engine-neutral Slovak leasing/loan account defaults on the "
               "l10n_sk chart, shared by the Community and Enterprise bridges.",
    "description": """
SK Lízing — účty (base)
=======================

Engine-neutral company defaults for Slovak *finančný prenájom* (leasing) and
loans, wired to the ``l10n_sk`` chart:

* long-term liability   → **474000** Záväzky z nájmu
* current portion       → **474100** Lízing (bežná časť)
* interest expense      → **562000** Úroky
* leased asset          → **022000** Samostatné hnuteľné veci a súbory hnuteľných vecí

Why a separate base
-------------------

The two editions run **different, colliding engines**: Community uses OCA
``account_loan`` + ``account_leasing``, Enterprise uses Odoo's ``account_loans``.
Both declare ``account.loan`` and ``account.loan.line`` with different field
names and different posting semantics, so exactly one may be installed. This
module holds everything that is *Slovak* rather than *engine-specific* — the
account roles and their chart mapping — and the two bridges
(``l10n_sk_account_loan_oca`` / ``l10n_sk_account_loan_ee``) map the roles onto
whichever engine is present.

It depends on ``l10n_sk`` only and declares no loan models of its own, so it is
safe on either edition. **LGPL-3**, so that both the AGPL Community bridge and
the proprietary Enterprise bridge can import it — the same arrangement as
``l10n_cssk_intrastat_base``.

Honesty flag
------------

The account mapping follows the l10n_sk chart's own naming (the chart ships
**474100 "Lízing (bežná časť)"** explicitly), but it wants **accountant
sign-off** like every other statutory mapping in this collection — in
particular the long-term/current split policy and whether a given contract is a
*finančný* or *operatívny prenájom* at all. Operatívny prenájom is not a loan:
it is a period expense, handled by časové rozlíšenie
(``l10n_sk_account_cutoff``).
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.2",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_sk"],
    "data": ["views/res_config_settings_views.xml"],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
