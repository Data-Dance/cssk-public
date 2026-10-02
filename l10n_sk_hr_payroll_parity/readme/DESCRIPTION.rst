Cross-engine parity harness for the Slovak payroll.

The localisation exists in two engine flavours — ``l10n_sk_hr_payroll_oca`` on
the OCA ``payroll`` engine and ``l10n_sk_hr_payroll_ee`` overlaying Enterprise
``hr_payroll`` — which are meant to be interchangeable. Each suite previously
asserted its own numbers in its own database, so nothing checked that the two
agreed.

This module holds one shared set of scenarios and expected figures
(``parity.py``) and one test that drives them through whichever engine is
installed. Installed in both databases, it turns engine parity from a
convention into a checked property.

``parity.py`` also carries ``CANONICAL_CODES``, the inventory of every concept
the two engines present under different rule codes — income tax split across
bands on one side, the health top-up spelled two ways, garnishment split in
two. Anything reading payslip lines by rule code across both engines needs it.

The CI contract
---------------

Installing this module in ONE database proves half the property and is not
evidence of parity. Both runs must be green::

    # OCA engine
    odoo-bin -d <db-oca> -i l10n_sk_hr_payroll_surcharges_oca,l10n_sk_hr_payroll_parity \
             --test-enable --test-tags=/l10n_sk_hr_payroll_parity --stop-after-init

    # Enterprise engine
    odoo-bin -d <db-ee>  -i l10n_sk_hr_payroll_surcharges_ee,l10n_sk_hr_payroll_parity \
             --test-enable --test-tags=/l10n_sk_hr_payroll_parity --stop-after-init

The static half of the same contract needs no database::

    python3 tools/check_module_parity.py --matrix

That checks the structural invariants: every engine-suffixed module has its
twin, an ``_oca`` module never reaches the Enterprise engine (nor an ``_dd``
module the OCA one) even transitively, and the engine-neutral bases reach
neither.
