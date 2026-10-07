# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Point the 2025 DPPO at the revision FS SR published beside it.

`dppo2025_v2.xsd` sits next to an UNCHANGED `dppo2025.xsd` and differs by one
element: a repeatable `dalsiaTransakcia` (further controlled transactions).
Being a superset it accepts every document the original did, so filing against
it is strictly safer — and a digest check on the pinned name could never have
found it, which is why the refresh procedure now probes for a `_v2` suffix too.

The version record lives in a ``noupdate="1"`` file, so an upgrade alone would
leave an installed database filing against the superseded schema. The NINE new
vintages need no help: noupdate blocks updates, not creations.
"""

import logging
import os

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

SCHEMA = "dppo2025_v2.xsd"
PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", SCHEMA,
)


def migrate(cr, version):
    if not version:
        return
    if not os.path.exists(PATH):
        _logger.warning("l10n_sk_dppo: %s is missing; 2025 left as it is", PATH)
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    record = env.ref("l10n_sk_dppo.dppo_version_2025", raise_if_not_found=False)
    if not record or record.xml_schema_filename == SCHEMA:
        return

    # Written through the ORM, not SQL: xml_schema_data is attachment=True,
    # so its bytes live in the filestore and there is no column to update.
    import base64

    with open(PATH, "rb") as handle:
        record.write({
            "xml_schema_filename": SCHEMA,
            "xml_schema_data": base64.b64encode(handle.read()),
        })
    _logger.info("l10n_sk_dppo: 2025 now files against %s", SCHEMA)
