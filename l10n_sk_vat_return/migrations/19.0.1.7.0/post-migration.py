# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Bind the DPHv21 template and schema to the pre-July version.

The record is `noupdate="1"`, so the data file reaches a fresh install and
nothing else — the lesson from 19.0.1.6.0, where exactly this edit tested green
on a clean database and left the shared one untouched.

Until now the pre-July version reused the 2025 template, which emits the
lettered elements the DPHv21 form does not have, and carried NO schema at all.
Since a missing schema now blocks the export outright, every pre-July period
was unfilable: 18 of the 24 periods of the reference agenda, which is three
quarters of the filed history.
"""
import base64
import logging

from odoo import SUPERUSER_ID, api
from odoo.tools.misc import file_open

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    version_rec = env.ref(
        "l10n_sk_vat_return.dph_version_2024", raise_if_not_found=False)
    template = env.ref("l10n_sk_vat_return.dph_2021", raise_if_not_found=False)
    if not version_rec or not template:
        return
    vals = {"xml_template_ref_id": template.id}
    if not version_rec.xml_schema_data:
        try:
            with file_open("l10n_sk_vat_return/data/dph2021.xsd", "rb") as fh:
                vals["xml_schema_data"] = base64.b64encode(fh.read())
                vals["xml_schema_filename"] = "dph2021.xsd"
        except (OSError, FileNotFoundError):
            _logger.warning(
                "l10n_sk_vat_return: dph2021.xsd is not readable — the "
                "pre-July version stays unfilable")
    version_rec.write(vals)
    _logger.info(
        "l10n_sk_vat_return: the pre-July version now renders DPHv21 and "
        "validates against dph2021.xsd — it reused the 2025 template and "
        "carried no schema")
