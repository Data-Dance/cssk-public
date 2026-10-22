{
    "name": "EDI Base",
    "summary": "Shared infrastructure for EDI integrations (Editel, GRiT, ...)",
    "author": "Data Dance s.r.o.",
    "version": "18.0.1.5.0",
    "depends": [
        "account",
        "account_add_gln",
        "queue_job",
        "stock",
        "uom_unece",
    ],
    "data": [
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "views/edi_message_views.xml",
        "views/edi_message_send_wizard_views.xml",
        "views/res_partner_views.xml",
        "views/res_config_settings.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "license": "AGPL-3",
}
