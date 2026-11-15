# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ VAT Registration Category (plátce / identifikovaná osoba)",
    "summary": "Record whether a partner's DIČ belongs to a plátce, a skupina "
               "or an identifikovaná osoba, and warn when a § 92a reverse "
               "charge is aimed at a customer who is not a plátce.",
    "description": """
CZ VAT Registration Category
============================

A Czech DIČ does not mean the same thing for everyone holding one.

An **identifikovaná osoba** (§ 6g–6l zákona č. 235/2004 Sb.) is registered for
VAT, holds a DIČ that **VIES confirms** — and is **not a plátce**. It deducts
no input VAT, it charges no VAT on domestic supplies, and the **režim
přenesení daňové povinnosti** of § 92a cannot shift the tax to it, because
§ 92a odst. 1 makes "plátce, pro kterého bylo zdanitelné plnění uskutečněno"
the one who accounts for it.

VIES cannot tell you this: it answers *valid* or *not valid*. The Finanční
správa's register of VAT subjects can — it publishes the type of each subject.

This module adds to ``res.partner``:

* **Registrace k DPH** — plátce / skupina / identifikovaná osoba / neplátce
* **Registrace k DPH od**
* **Plátce DPH** — computed; true only for a plátce and a skupina

and warns on a customer invoice when a domestic reverse-charge tax is used for
a customer recorded as an identifikovaná osoba or a neplátce. The warning
**never blocks the posting** — the category is a copy of a register and
registrations change; it warns, posts the reason to the chatter, and leaves
the decision where it belongs.

The company's **own** status over time is a different matter and belongs to
``l10n_cz_vat_status``; this module is about counterparties.

Fill the category automatically by installing ``l10n_cz_payment_reliability``
(19.0.1.3.0 or later): *Check tax reliability* on a contact then also reads
the subject type from the Finanční správa register.

**Have an accountant confirm the mapping for your own tax setup.** A
reverse-charge supply is recognised by the tax: the row 25 tag of the Czech
VAT return (``VAT 25``, as on ``l10n_cz``'s own *0% RC* tax), or the § 92a
flag of ``l10n_cz_invoice``. A tax carrying neither gives no signal and the
check stays quiet.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["account", "base_vat", "l10n_cz"],
    "data": [
        "views/res_partner_views.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
}
