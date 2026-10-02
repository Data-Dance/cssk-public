# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import models

HEADERS = (
    "Scheme Country",
    "Collective Scheme",
    "Category",
    "Category Code",
    "Classification",
    "Classification Code",
    "Household / Professional",
    "Rate Basis",
    "Pieces",
    "Weight (kg)",
    "Fee",
    "Currency",
)


class RecyclingFeeXlsx(models.AbstractModel):
    """The selected report rows, summed per country and category.

    One row per (country, scheme, category, classification, currency): the
    granularity of a scheme's quarterly or annual declaration. A second sheet
    keeps the underlying invoice lines so every total can be traced back.
    """

    _name = "report.l10n_cssk_recycling_fee.recycling_fee_xlsx"
    _description = "Recycling Fee XLSX"
    _inherit = "report.report_xlsx.abstract"

    def _summary_rows(self, rows):
        totals = defaultdict(lambda: [0.0, 0.0, 0.0])
        for row in rows:
            key = (
                row.country_id,
                row.collector_id,
                row.categ_id,
                row.classification_id,
                row.product_status,
                row.ecotax_type,
                row.currency_id,
            )
            totals[key][0] += row.pieces
            totals[key][1] += row.weight_kg
            totals[key][2] += row.fee_amount
        return sorted(
            totals.items(),
            key=lambda item: (
                item[0][0].code or "",
                item[0][2].code or "",
                item[0][3].code or item[0][3].name or "",
            ),
        )

    def _selection_label(self, field_name, value):
        field = self.env["recycling.fee.report"]._fields[field_name]
        return dict(field._description_selection(self.env)).get(value, "")

    def generate_xlsx_report(self, workbook, data, rows):
        bold = workbook.add_format({"bold": True})
        qty = workbook.add_format({"num_format": "#,##0.###"})
        money = workbook.add_format({"num_format": "#,##0.00"})
        date_fmt = workbook.add_format({"num_format": "yyyy-mm-dd"})

        sheet = workbook.add_worksheet(self.env._("Summary"))
        dates = [d for d in rows.mapped("date") if d]
        sheet.write(0, 0, self.env._("Recycling fee report"), bold)
        if dates:
            sheet.write(1, 0, self.env._("Period"))
            sheet.write_datetime(1, 1, min(dates), date_fmt)
            sheet.write_datetime(1, 2, max(dates), date_fmt)
        sheet.write(2, 0, self.env._("Companies"))
        sheet.write(2, 1, ", ".join(rows.company_id.mapped("name")))
        header_row = 4
        for col, header in enumerate(HEADERS):
            sheet.write(header_row, col, header, bold)
        sheet.set_column(0, 7, 18)
        sheet.set_column(8, 11, 14)
        row_index = header_row
        for key, (pieces, weight, fee) in self._summary_rows(rows):
            country, collector, categ, classification, status, basis, currency = key
            row_index += 1
            sheet.write(row_index, 0, country.code or "")
            sheet.write(row_index, 1, collector.name or "")
            sheet.write(row_index, 2, categ.name or "")
            sheet.write(row_index, 3, categ.code or "")
            sheet.write(row_index, 4, classification.name or "")
            sheet.write(row_index, 5, classification.code or "")
            sheet.write(row_index, 6, self._selection_label("product_status", status))
            sheet.write(row_index, 7, self._selection_label("ecotax_type", basis))
            sheet.write_number(row_index, 8, pieces, qty)
            sheet.write_number(row_index, 9, weight, qty)
            sheet.write_number(row_index, 10, fee, money)
            sheet.write(row_index, 11, currency.name or "")

        detail = workbook.add_worksheet(self.env._("Lines"))
        detail_headers = (
            "Date", "Invoice", "Partner", "Product", "Scheme Country",
            "Classification", "Pieces", "Weight (kg)", "Fee", "Currency",
        )
        for col, header in enumerate(detail_headers):
            detail.write(0, col, header, bold)
        detail.set_column(0, 9, 16)
        for index, row in enumerate(rows.sorted(lambda r: (r.date, r.id)), start=1):
            if row.date:
                detail.write_datetime(index, 0, row.date, date_fmt)
            detail.write(index, 1, row.move_id.name or "")
            detail.write(index, 2, row.partner_id.display_name or "")
            detail.write(index, 3, row.product_id.display_name or "")
            detail.write(index, 4, row.country_id.code or "")
            detail.write(index, 5, row.classification_id.display_name or "")
            detail.write_number(index, 6, row.pieces, qty)
            detail.write_number(index, 7, row.weight_kg, qty)
            detail.write_number(index, 8, row.fee_amount, money)
            detail.write(index, 9, row.currency_id.name or "")
