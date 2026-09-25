# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "SK VAT Registration Category (§ 4 / § 7 / § 7a)",
    "summary": "Record which paragraph of the SK VAT Act a partner's IČ DPH "
               "was issued under, and warn when a § 69/12 reverse charge is "
               "aimed at a § 7 / § 7a registrant, who is not a platiteľ.",
    "description": """
SK VAT Registration Category
============================

An IČ DPH does not mean the same thing for everyone holding one.

A subject registered under **§ 7** (nadobudnutie tovaru z iného členského
štátu) or **§ 7a** (dodanie / prijatie služby) receives a valid IČ DPH that
**VIES confirms** — and is **not a platiteľ dane**. They deduct no input VAT,
they charge no VAT on domestic supplies, and **§ 69 ods. 12 domestic reverse
charge cannot apply to them**, because that provision names a platiteľ on both
sides of the supply.

VIES cannot tell you this: it answers *valid* or *not valid*. The paragraph
lives in the Finančná správa registration record, which ORSF republishes as
``vatRegistration.druhReg``.

This module adds to ``res.partner``:

* **Druh registrácie DPH** — § 4 / § 4b / § 5 / § 6 / § 7 / § 7a
* **Platiteľ DPH od**
* **Platiteľ dane** — computed; true only for § 4 / § 4b / § 5 / § 6

and warns on a customer invoice when a domestic reverse-charge tax is used for
a § 7 / § 7a customer. The warning **never blocks the posting** — the register
is an aggregator's copy and the categories move; it warns, posts the reason to
the chatter, and leaves the decision where it belongs.

Fill the fields automatically by installing ``partner_autocomplete_orsf_sk``,
which maps them from the register on enrichment.

**Have an accountant confirm the mapping for your own tax setup.** The check
recognises a reverse-charge supply through ``l10n_sk_invoice``'s per-tax
``l10n_sk_reverse_charge`` flag; without that module installed there is no
reliable signal and the check stays quiet.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.1",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["account", "base_vat", "l10n_sk"],
    "data": [
        "views/res_partner_views.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
}
