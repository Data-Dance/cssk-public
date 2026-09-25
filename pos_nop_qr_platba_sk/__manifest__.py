{
    "name": "POS — QR Platba (SK) via NOP KVERKOM",
    "summary": "Accept Slovak QR Platba instant bank payments in Point of Sale",
    "description": """
Adds a new POS online payment method that mints a NOP KVERKOM transaction id,
shows a payme.sk QR code to the customer, and confirms the payment as soon as
the bank pushes the notification to NOP.

The cashier-facing flow reuses ``pos_online_payment``'s QR popup and its
``ONLINE_PAYMENTS_NOTIFICATION`` bus channel. The QR code content is the
Slovak SBA standard payment-link URL (payme.sk) with ``PI=QR-<uuid>`` bound to
the NOP transaction.
    """,
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.3",
    "category": "Sales/Point of Sale",
    "depends": [
        "nop_kverkom_base",
        "pos_online_payment",
        "account_qr_code_payme_sk",
        "payment",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/payment_method_data.xml",
        "data/payment_provider_data.xml",
        "views/pos_payment_method_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_nop_qr_platba_sk/static/src/**/*",
        ],
    },
    "installable": True,
    "license": "AGPL-3",
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
