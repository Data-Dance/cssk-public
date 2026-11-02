=========================================
CZ/SK Bank File Formats — shared builders
=========================================

The single source of truth for the **Czech/Slovak bank payment-file formats**.
Both the Community (``account_payment_order``) and Enterprise
(``account_batch_payment``) variants of ``account_abo`` / ``account_multicash``
build on this module so the format logic lives in exactly one place.

There are **no Odoo models** here — only pure helpers, imported via
``odoo.addons.account_cz_bankfile_base.utils.*``. The builders take a list of
normalized ``BankPaymentItem`` records (plain values plus the bank records), so
the edition-specific shims can feed them from either ``account.payment.line``
(OCA payment order, CE) or ``account.payment`` (Enterprise batch payment, EE)
without duplicating any format logic.

Features
========

* ``utils.abo.build_abo_file`` — builds the ABO credit-transfer (úhrada) file.
* ``utils.multicash.build_multicash_file`` — builds MultiCash CFD / CFU / CFA /
  MT101 files.
* ``utils.common`` — Czech account-number parsing, the normalized
  ``BankPaymentItem`` passed to the builders, and the VS/KS/SS symbol resolver
  (``resolve_symbol``: explicit value, else a token parsed from the payment
  communication).

Usage
=====

This is a library dependency, not an end-user app. Install it as a dependency of
``account_abo`` / ``account_multicash`` (it is pulled in automatically). To reuse
the builders from your own shim, build a list of ``BankPaymentItem`` and call the
relevant ``build_*`` helper::

    from odoo.addons.account_cz_bankfile_base.utils.abo import build_abo_file
    from odoo.addons.account_cz_bankfile_base.utils.common import (
        BankPaymentItem, resolve_symbol,
    )

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
