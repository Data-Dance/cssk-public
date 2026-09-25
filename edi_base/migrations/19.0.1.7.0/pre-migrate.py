"""Hand the GS1 party fields over to ``edi_base_gs1``.

``edi_communication_partner_id``, ``edi_desadv_sscc_mode`` and
``stock.warehouse.edi_gln`` left this module. Their COLUMNS are untouched —
nothing here moves data — but the ``ir.model.data`` rows that own them still
say ``edi_base``, and at the end of a load Odoo removes the rows a module no
longer declares. Reassigning them first is what keeps the fields (and the
GLNs configured on them) alive across the upgrade.

The module force-install matters just as much. If ``edi_base`` is updated
while ``edi_base_gs1`` is not installed, those fields exist in no installed
module at all and the cleanup takes them for real. On a database running
Editel or GRiT the new module arrives as a dependency anyway; this makes it
arrive even when somebody upgrades ``edi_base`` alone.
"""

import logging

_logger = logging.getLogger(__name__)

#: ``ir.model.data`` names of the fields that moved, as Odoo spells them.
MOVED_FIELDS = (
    "field_res_partner__edi_communication_partner_id",
    "field_res_partner__edi_desadv_sscc_mode",
    "field_stock_warehouse__edi_gln",
)

#: Any one of these installed means the GS1 layer is in use here.
GS1_CONSUMERS = ("edi_editel_base", "edi_grit_base", "edi_base_purchase")


def migrate(cr, version):
    if not version:
        return

    cr.execute(
        """
        SELECT 1 FROM ir_module_module
         WHERE name IN %s AND state IN ('installed', 'to upgrade', 'to install')
         LIMIT 1
        """,
        (GS1_CONSUMERS,),
    )
    if not cr.fetchone():
        _logger.info(
            "edi_base_gs1: no consumer installed, leaving the GS1 fields to "
            "be removed with the rest of the EDIFACT side"
        )
        return

    cr.execute(
        """
        UPDATE ir_module_module
           SET state = 'to install'
         WHERE name = 'edi_base_gs1'
           AND state IN ('uninstalled', 'to remove')
        """
    )
    if cr.rowcount:
        _logger.info("edi_base_gs1: scheduled for install, it now owns the GS1 fields")

    cr.execute(
        """
        UPDATE ir_model_data
           SET module = 'edi_base_gs1'
         WHERE module = 'edi_base'
           AND model = 'ir.model.fields'
           AND name IN %s
        """,
        (MOVED_FIELDS,),
    )
    _logger.info("edi_base_gs1: %s field definitions reassigned", cr.rowcount)
