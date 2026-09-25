{
    "name": "CZ Účetní závěrka — závěrkové účty 701/702/710",
    "version": "19.0.1.0.0",
    "summary": "Make the Czech year-end closing postable: retype 701/702/710 "
               "from off_balance, which Odoo refuses to mix with any other "
               "account in one entry.",
    "description": """
CZ Účetní závěrka — závěrkové účty
===================================

``l10n_cz`` ships **701000 / 702000 / 710000** with ``account_type =
off_balance``. Odoo's ``account_move_line._check_off_balance`` forbids mixing
an off-balance account with any other in a single journal entry — and that is
exactly what a Czech year-end closing is:

* třída 5 and 6 closed against **710** (účet zisků a ztrát),
* rozvahové účty closed against **702** (konečný účet rozvažný),
* and reopened from **701** (počáteční účet rozvažný).

So as shipped, the závěrka cannot be posted at all, and neither can an opening
balance. This module retypes the three to ``equity``.

Why ``equity`` is safe
----------------------

They are technical accounts carrying balance-sheet and result totals, and a
matched closing/opening pair nets them to zero. The CZ statutory statements map
their rows by account **code**, not by account type, so nothing filed changes.
What does change is that the three become visible to Odoo's own generic balance
sheet — the price of being able to post the závěrka at all.

Measured
--------

On a seven-year Czech import before this module existed: **82 documents failed**
outright, and because the result accounts were then never closed, the trial
balance was out by **698 169 015** on accounts that net to zero in the source.
Retyping took the failures to 1 and the difference to 2 407 136.

The mirror of ``l10n_sk_zavierka``, which fixes the identical defect in
``l10n_sk``. This is **not** import-specific: every Czech company with an
opening balance hits it, migration or not.

Deliberately out of scope
-------------------------

``l10n_sk_zavierka`` also ships an ``account_fiscal_year_closing`` template.
This module does not, because the CZ closing template is a separate piece of
domain work and the retype is what unblocks posting. Adding one later needs no
change here.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_cz"],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
