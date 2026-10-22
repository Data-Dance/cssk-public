# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import logging

from odoo import SUPERUSER_ID, api
from odoo.tools.misc import file_open

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Load the official KV DPH schema onto version records that never got it.

    ``xml_schema_data`` is populated from the data file, and the record is
    ``noupdate="1"``. So on any database created before the field existed the
    upgrade adds the COLUMN and leaves it empty for ever: the record was written
    once, at install, and a ``noupdate`` record is never rewritten.

    The consequence is silent and it is the bad kind of silent — schema
    validation on export simply does not happen. Nothing errors, nothing warns,
    and a KV DPH that the FS SR would reject exports cleanly. Found by a test
    asserting the schema is present, on a database upgraded rather than
    installed; every deployment older than the field is in the same state.

    Only genuinely empty records are filled, so an accountant who has loaded a
    corrected or newer schema by hand keeps theirs.

    The same trap took a whole debugging pass in ``l10n_sk_vat_return`` and is
    worth stating once in general: **a ``noupdate="1"`` record does not pick up
    fields added after it was created.** Adding a field to such a record's data
    file only affects fresh installs unless a migration carries it over — and
    clearing ``ir_model_data.noupdate`` does NOT carry it over, because the gate
    in ``convert.py`` reads the FILE's attribute and returns before the database
    row is ever consulted.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    Version = env["cssk.control.statement.version"]

    stale = Version.search([("country_id.code", "=", "SK")]).filtered(
        lambda v: not v.xml_schema_data
    )
    if not stale:
        return

    try:
        with file_open("l10n_sk_kv_dph/data/kv_dph_2025.xsd", "rb") as handle:
            payload = handle.read()
    except (OSError, FileNotFoundError):
        _logger.warning(
            "l10n_sk_kv_dph: kv_dph_2025.xsd is not readable — %s version(s) "
            "keep exporting without schema validation", len(stale),
        )
        return

    stale.write({
        "xml_schema_data": base64.b64encode(payload),
        "xml_schema_filename": "kv_dph_2025.xsd",
    })
    _logger.info(
        "l10n_sk_kv_dph: loaded the official XSD onto %s KV version(s) that "
        "predate the field — schema validation on export was silently off",
        len(stale),
    )
