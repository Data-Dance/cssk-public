# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

ROW_HEADERS = (
    "Number", "Date", "Document", "Text", "Partner", "Category", "Type",
    "Money", "In", "Out", "VAT", "Storno", "Affects the tax base",
    "Non-cash", "Needs review", "Note",
)


class CsskCashJournalXlsx(models.AbstractModel):
    """The denník as a spreadsheet: the rows, then the totals per category.

    Two sheets on purpose. The first is every row as the book has it, so the
    accountant can filter and pivot it herself — which is what she was doing by
    hand in Excel before this module existed, and a better answer than
    reproducing one particular pivot. The second is the totals per category,
    which is the figure she checks against the tax return.

    The money columns follow ``money_direction`` and the amounts follow the
    classification, so a storno shows as money out with a negative amount in its
    own category — the same reading as the printed book.
    """

    _name = "report.l10n_cssk_cash_journal_base.dennik_xlsx"
    _description = "Cash Journal XLSX"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, wizards):
        wizard = wizards[:1]
        bold = workbook.add_format({"bold": True})
        money = workbook.add_format({"num_format": "#,##0.00"})
        date_fmt = workbook.add_format({"num_format": "yyyy-mm-dd"})
        rows = wizard._cssk_rows()

        self._cssk_write_rows(workbook, wizard, rows, bold, money, date_fmt)
        self._cssk_write_totals(workbook, wizard, rows, bold, money)

    def _cssk_write_rows(self, workbook, wizard, rows, bold, money, date_fmt):
        sheet = workbook.add_worksheet(self.env._("Cash journal"))
        sheet.set_column(0, 0, 12)
        sheet.set_column(1, 1, 11)
        sheet.set_column(2, 4, 24)
        sheet.set_column(5, 6, 22)
        sheet.set_column(7, 10, 13)
        sheet.set_column(11, 15, 14)
        sheet.freeze_panes(1, 0)
        for col, header in enumerate(ROW_HEADERS):
            sheet.write(0, col, self.env._(header), bold)

        for index, row in enumerate(rows, start=1):
            gross = row.amount + row.amount_tax
            sheet.write(index, 0, row.number or "")
            if row.date:
                sheet.write_datetime(index, 1, row.date, date_fmt)
            sheet.write(index, 2, row.ref or "")
            sheet.write(index, 3, row.label or "")
            sheet.write(index, 4, row.partner_id.display_name or "")
            sheet.write(index, 5, row.category_id.display_name or "")
            sheet.write(index, 6, self._cssk_label(row, "kind"))
            sheet.write(index, 7, self._cssk_label(row, "payment_kind"))
            sheet.write_number(
                index, 8, gross if row.money_direction == "in" else 0.0, money)
            sheet.write_number(
                index, 9, gross if row.money_direction == "out" else 0.0, money)
            sheet.write_number(index, 10, row.amount_tax, money)
            sheet.write(index, 11, self.env._("yes") if row.counter_entry else "")
            sheet.write(index, 12, self.env._("yes") if row.taxable else "")
            sheet.write(index, 13, self.env._("yes") if row.non_cash else "")
            sheet.write(index, 14, self.env._("yes") if row.needs_review else "")
            sheet.write(index, 15, row.review_reason or "")

    def _cssk_write_totals(self, workbook, wizard, rows, bold, money):
        sheet = workbook.add_worksheet(self.env._("Totals per category"))
        sheet.set_column(0, 0, 32)
        sheet.set_column(1, 4, 16)
        for col, header in enumerate(
            ("Category", "Type", "Amount", "VAT", "Affects the tax base")
        ):
            sheet.write(0, col, self.env._(header), bold)

        totals = {}
        for row in rows:
            key = row.category_id
            amount, tax, _taxable = totals.get(key, (0.0, 0.0, False))
            totals[key] = (
                amount + row.amount_classified,
                tax + row.amount_tax,
                row.taxable,
            )
        index = 0
        for category, (amount, tax, taxable) in sorted(
            totals.items(), key=lambda item: (
                item[0].sequence if item[0] else 0,
                item[0].code or "")
        ):
            index += 1
            sheet.write(index, 0, category.display_name
                        if category else self.env._("(no category)"))
            sheet.write(index, 1, dict(
                self.env["cssk.cash.category"]._fields["kind"].selection
            ).get(category.kind, "") if category else "")
            sheet.write_number(index, 2, amount, money)
            sheet.write_number(index, 3, tax, money)
            sheet.write(index, 4, self.env._("yes") if taxable else "")

    def _cssk_label(self, row, field):
        return dict(
            row._fields[field]._description_selection(row.env)
        ).get(row[field], "")
