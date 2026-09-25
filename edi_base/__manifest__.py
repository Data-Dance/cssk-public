{
    "name": "EDI Base",
    "summary": "Shared infrastructure for EDI integrations (Editel, GRiT, ...)",
    "author": "Data Dance s.r.o.",
    "version": "19.0.1.7.0",
    # queue_job is deliberately NOT here. Dispatch goes through
    # ``_dispatch_send`` / ``_dispatch_ack``, which do nothing on their own;
    # ``edi_base_queue_job`` overrides them with ``with_delay``, and a provider
    # that wants no job runner registers "cron" in ``PROVIDER_DISPATCH_MAP``
    # instead. A Peppol invoice client should not have to install a job runner
    # to send an invoice.
    # ``stock`` and ``uom_unece`` are deliberately NOT here either. They were
    # only ever used by the EDIFACT side — inbound DESADV pickings, warehouse
    # delivery-point GLNs, UNECE unit codes — and they now live with it in
    # ``edi_base_gs1`` and ``edi_base_purchase``. What is left is transport:
    # an envelope, a state machine, dispatch and storage.
    "depends": [
        "account",
        "account_add_gln",
    ],
    "data": [
        "security/res_groups.xml",
        "data/ir_cron.xml",
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
