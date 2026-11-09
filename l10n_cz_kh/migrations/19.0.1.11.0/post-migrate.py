# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Add section A.3 to a version loaded before it existed (noupdate data)."""

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    record = env.ref("l10n_cz_kh.cz_kh_version_2025", raise_if_not_found=False)
    if record and "A3" not in record.section_code_ids.mapped("code"):
        record.write({"section_code_ids": [(0, 0, {
            "code": "A3",
            "name": "A.3 — Investiční zlato",
            "sequence": 30,
            "aggregation": "detail",
            "section_model": "l10n.cz.kh.a3",
        })]})
