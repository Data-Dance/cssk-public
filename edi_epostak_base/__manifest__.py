{
    "name": "ePošťák EDI Base",
    "summary": "Base module for the ePošťák (epostak.sk) Peppol access point: "
    "provider registration, environment/mode configuration and the Peppol "
    "addressing metadata every ePošťák wire protocol needs",
    "author": "Data Dance s.r.o.",
    "version": "19.0.1.0.0",
    "depends": [
        "edi_base",
        "account_edi_ubl_cii",
    ],
    "data": [
        "data/cron.xml",
        "views/res_config_settings.xml",
    ],
    "installable": True,
    "license": "AGPL-3",
}
