# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Notes on breakdown columns.

A note is stored per period; a breakdown column is a period AND a value, so
the note carries the value too. A note on the total column has no value, and
matching always compares the value - empty included - so a note on a value
column never shows on the total, nor the other way round.
"""
from odoo import api, fields, models
from odoo.exceptions import AccessError

from odoo.addons.mis_builder.models.kpimatrix import KpiMatrix

from .mis_report_instance import SEP


def _split_cell_id(cell_id):
    """(kpi_id, period_id, breakdown_value or False, subkpi_id)."""
    kpi_id, _account_id, col_key, subkpi_id = cell_id.split("#")
    period_key, _sep, value = col_key.partition(SEP)
    return int(kpi_id), int(period_key), value if _sep else False, int(subkpi_id) if subkpi_id else None


class MisReportInstanceAnnotation(models.Model):
    _inherit = "mis.report.instance.annotation"

    breakdown_value = fields.Char(
        help="The value of the period's breakdown field the note belongs to; "
             "empty for a note on the period's own (total) column.")

    def _get_first_matching_annotation(self, cell_id, instance_id):
        kpi_id, period_id, value, subkpi_id = _split_cell_id(cell_id)
        context = self.env["mis.report.instance"].browse(instance_id)._get_annotation_context()
        annotations = self.search([
            ("period_id", "=", period_id), ("kpi_id", "=", kpi_id),
            ("subkpi_id", "=", subkpi_id), ("breakdown_value", "=", value),
        ]).filtered(lambda rec: rec.annotation_context == context)
        return annotations[:1]

    @api.model
    def set_annotation(self, cell_id, instance_id, note):
        kpi_id, period_id, value, subkpi_id = _split_cell_id(cell_id)
        if not value:
            return super().set_annotation(cell_id, instance_id, note)
        instance = self.env["mis.report.instance"].browse(instance_id)
        if not instance.user_can_edit_annotation:
            raise AccessError(self.env._("You do not have the rights to edit annotations"))
        annotation = self._get_first_matching_annotation(cell_id, instance_id)
        if annotation:
            annotation.note = note
        else:
            self.create({
                "period_id": period_id, "kpi_id": kpi_id, "subkpi_id": subkpi_id,
                "breakdown_value": value, "note": note,
                "annotation_context": instance._get_annotation_context(),
            })


class MisReportInstance(models.Model):
    _inherit = "mis.report.instance"

    def get_notes_by_cell_id(self):
        """The parent's note map keys every note by its period, so a note on
        a breakdown column and one on the total of the same period would
        collide; notes are keyed by their own column instead."""
        self.ensure_one()
        if not self.user_can_read_annotation:
            return {}
        context = self._get_annotation_context()
        annotations = self.env["mis.report.instance.annotation"].search(
            [("period_id", "in", self.period_ids.ids)]
        ).filtered(lambda rec: rec.annotation_context == context)
        annotations = annotations.sorted(
            lambda r: (r.kpi_id.sequence, r.period_id.sequence, r.subkpi_id.sequence))
        notes = {}
        for sequence, annotation in enumerate(annotations, 1):
            column = (f"{annotation.period_id.id}{SEP}{annotation.breakdown_value}"
                      if annotation.breakdown_value else annotation.period_id.id)
            notes[KpiMatrix._make_cell_id(
                annotation.kpi_id.id, False, column,
                annotation.subkpi_id and annotation.subkpi_id.id,
            )] = {"text": annotation.note, "sequence": sequence}
        return notes
