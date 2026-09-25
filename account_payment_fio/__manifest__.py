# Copyright 2026 Data Dance s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
{
    "name": "Fio banka — payment orders",
    "summary": "Build Fio XML payment orders and send them to the bank from an "
               "OCA payment order.",
    "description": """
Fio banka — payment orders (Community)
======================================

Adds two things to the OCA ``account.payment.order``:

**A Fio XML exporter.** Payment method ``fio_xml`` produces the
``importIB.xsd`` file: domestic orders, Europlatba and foreign payments, each
with the KS/VS/SS carried as real elements rather than smuggled through the
message field. Fio's own XML is the only upload format that does that —
pain.001 is EUR-only and ABO is CZK-domestic-only.

**A Send to Fio button**, which uploads the generated file over the API and
records what the bank answered. It looks at the file to decide what to tell
Fio it is, so it also sends the ABO file ``account_abo`` builds and the
pain.001 that ``account_banking_sepa_credit_transfer`` builds — those exporters
become Fio-capable with no new format code.

What "sent" means
-----------------

Fio stores the uploaded orders as an **unauthorised batch**. Somebody with
signing rights still has to confirm it in internet banking with an SMS or a Fio
signature. Nothing in Odoo can move money on its own — which is the strongest
property of this API, and worth saying out loud to an auditor.

If an upload's answer is lost in transit the order goes to *Unknown*, not to
*Not sent*: the bank may be holding the batch, and a retry would create a
second one. Two buttons record what the operator actually found in internet
banking; only one of them re-enables sending.
    """,
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "category": "Accounting/Accounting",
    "version": "19.0.1.2.1",
    "license": "AGPL-3",
    "depends": ["account_payment_order", "account_fio", "account_fio_base"],
    "data": [
        "data/account_payment_method.xml",
        "views/account_payment_line_views.xml",
        "views/account_payment_order_views.xml",
    ],
    "installable": True,
}
