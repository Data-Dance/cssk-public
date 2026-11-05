# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Translate the line labels of the core reconciliation models in existing
companies ("Bank Fees", "Internal Transfers"); see
``account.chart.template._cssk_translate_reco_line_labels``."""

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["account.chart.template"]._cssk_translate_reco_line_labels()
