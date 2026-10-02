{
    "name": "EDI Base: Peppol BIS 3.0",
    "summary": "Provider-neutral Peppol BIS Billing 3.0: send/receive invoices "
    "and credit notes, and business responses (MLR / Invoice Response), over "
    "any EDI transport provider",
    "author": "Data Dance s.r.o.",
    "version": "19.0.1.5.1",
    "depends": [
        "edi_base",
        "account_edi_ubl_cii",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/peppol_clarification_data.xml",
        "wizards/peppol_invoice_response_wizard_views.xml",
        "views/account_move_views.xml",
        "views/edi_message_views.xml",
        "views/res_config_settings_views.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "license": "AGPL-3",
}
