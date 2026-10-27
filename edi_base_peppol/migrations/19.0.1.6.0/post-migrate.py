"""Pin the Peppol transport a database with several of them has been using.

Until 1.6.0, with several Peppol transports installed and ``peppol.transport``
empty, the module that loaded last carried every document — and Editel ignored
the setting altogether. Now several transports and no choice means nothing is
sent until one is chosen. A database that was sending must not stop on an
upgrade, so the transport of its most recent outbound Peppol message becomes
the explicit choice. One that never sent is left to choose.
"""

import logging

_logger = logging.getLogger(__name__)

TRANSPORT_MODULES = {
    "edi_editel_peppol": "editel",
    "edi_grit_peppol": "grit",
    "edi_epostak_peppol": "epostak",
}


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        "SELECT value FROM ir_config_parameter WHERE key = 'peppol.transport'")
    row = cr.fetchone()
    if row and row[0]:
        return
    cr.execute(
        "SELECT name FROM ir_module_module WHERE name IN %s AND state IN "
        "('installed', 'to upgrade')",
        (tuple(TRANSPORT_MODULES),),
    )
    installed = {TRANSPORT_MODULES[name] for (name,) in cr.fetchall()}
    if len(installed) < 2:
        return
    cr.execute(
        "SELECT provider FROM edi_message WHERE direction = 'out' "
        "AND doc_family = 'peppol' AND provider IN %s ORDER BY id DESC LIMIT 1",
        (tuple(installed),),
    )
    row = cr.fetchone()
    if not row:
        _logger.warning(
            "edi_base_peppol: several Peppol transports installed (%s) and "
            "none chosen; nothing goes through Peppol until Peppol Transport "
            "is set in Settings > EDI.", ", ".join(sorted(installed)))
        return
    cr.execute(
        "UPDATE ir_config_parameter SET value = %s WHERE key = 'peppol.transport'",
        (row[0],),
    )
    if not cr.rowcount:
        cr.execute(
            "INSERT INTO ir_config_parameter (key, value, create_uid, "
            "write_uid, create_date, write_date) VALUES ('peppol.transport', "
            "%s, 1, 1, now() at time zone 'UTC', now() at time zone 'UTC')",
            (row[0],),
        )
    _logger.info(
        "edi_base_peppol: Peppol Transport set to %r, the transport of the "
        "last Peppol document sent.", row[0])
