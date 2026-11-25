# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

#: The money columns of the grid, in the PDF's order:
#: (heading, příjem key, výdej key).
_MONEY_GROUPS = (
    ("Pokladna", "pokladna_prijem", "pokladna_vydej"),
    ("Banka", "banka_prijem", "banka_vydej"),
    ("Průběžné položky", "prubezne_prijem", "prubezne_vydej"),
    ("DPH", "dph_prijem", "dph_vydej"),
)


class CsskCashJournalXlsx(models.AbstractModel):
    """The peněžní deník as the first sheet of the spreadsheet.

    The same grid and the same figures as the PDF, read from
    ``_cz_denik_values``, which the PDF renders, so the two cannot disagree:
    pokladna, banka, průběžné položky and DPH each split into příjem and
    výdej, the income and expense breakdown, and the running balances. The
    flat sheet stays after it, for pivoting. Headings are Czech, as on the
    PDF. The Slovak book has had this sheet since a customer's accountant
    asked for the layout of the PDF in the spreadsheet.
    """

    _inherit = "report.l10n_cssk_cash_journal_base.dennik_xlsx"

    def _cssk_write_national(self, workbook, wizard, formats):
        super()._cssk_write_national(workbook, wizard, formats)
        if wizard.company_id.country_id.code != "CZ":
            return
        values = self.env["report.l10n_cz_cash_journal.report_penezni_denik"] \
            ._cz_denik_values(wizard.company_id, wizard.date_from, wizard.date_to)
        bold, money, date_fmt = formats["bold"], formats["money"], formats["date"]
        bold_money = workbook.add_format({"bold": True, "num_format": "#,##0.00"})
        head = workbook.add_format({"bold": True, "align": "center",
                                    "valign": "vcenter", "text_wrap": True})
        sheet = workbook.add_worksheet("Peněžní deník")

        # Two header rows: a group over its příjem / výdej pair, every other
        # heading spanning both rows.
        col = 0
        for heading in ("Datum", "Číslo", "Doklad", "Text"):
            sheet.merge_range(0, col, 1, col, heading, head)
            col += 1
        money_cols = []
        for heading, key_in, key_out in _MONEY_GROUPS:
            sheet.merge_range(0, col, 0, col + 1, heading, head)
            sheet.write(1, col, "příjem", head)
            sheet.write(1, col + 1, "výdej", head)
            money_cols += [(col, key_in), (col + 1, key_out)]
            col += 2
        breakdown_cols = []
        for key, heading, _codes in values["columns"]:
            sheet.merge_range(0, col, 1, col, heading, head)
            breakdown_cols.append((col, key))
            col += 1
        cash_col, bank_col = col, col + 1
        sheet.merge_range(0, cash_col, 1, cash_col, "Zůstatek pokladna", head)
        sheet.merge_range(0, bank_col, 1, bank_col, "Zůstatek banka", head)
        sheet.set_row(0, 30)
        sheet.set_column(0, 0, 11)
        sheet.set_column(1, 2, 14)
        sheet.set_column(3, 3, 30)
        sheet.set_column(4, bank_col, 13)
        sheet.freeze_panes(2, 4)

        row = 2
        sheet.write(row, 3, "Počáteční stav", bold)
        sheet.write_number(row, cash_col, values["opening_cash"], bold_money)
        sheet.write_number(row, bank_col, values["opening_bank"], bold_money)

        for line in values["lines"]:
            row += 1
            record = line["row"]
            if record.date:
                sheet.write_datetime(row, 0, record.date, date_fmt)
            sheet.write(row, 1, record.number or "")
            sheet.write(row, 2, record.ref or "")
            sheet.write(row, 3, record.label or "")
            for column, key in money_cols + breakdown_cols:
                if line["cells"][key]:
                    sheet.write_number(row, column, line["cells"][key], money)
            sheet.write_number(row, cash_col, line["cash"], money)
            sheet.write_number(row, bank_col, line["bank"], money)

        row += 1
        sheet.write(row, 3, "Celkem", bold)
        for column, key in money_cols + breakdown_cols:
            sheet.write_number(row, column, values["totals"][key], bold_money)
        sheet.write_number(row, cash_col, values["closing_cash"], bold_money)
        sheet.write_number(row, bank_col, values["closing_bank"], bold_money)
