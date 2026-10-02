{
    "name": "ePošťák EDI Connector: SAPI-SK 1.0",
    "summary": "Concrete REST connector for the ePošťák Peppol access point "
    "(SAPI-SK 1.0): send and receive UBL, acknowledge, track delivery",
    "author": "Data Dance s.r.o.",
    "version": "19.0.1.1.0",
    "depends": [
        "edi_epostak_base",
            ],
    "data": [
        "data/cron.xml",
        "views/res_config_settings.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "license": "AGPL-3",
}
