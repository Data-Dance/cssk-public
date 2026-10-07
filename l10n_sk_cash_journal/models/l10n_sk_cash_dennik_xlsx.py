# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

#: The money columns of the statutory grid, in the PDF's order:
#: (heading, príjem key, výdaj key).
_MONEY_GROUPS = (
    ("Pokladnica", "pokladnica_prijem", "pokladnica_vydaj"),
    ("Banka", "banka_prijem", "banka_vydaj"),
    ("Priebežné položky", "priebezne_prijem", "priebezne_vydaj"),
    ("DPH", "dph_prijem", "dph_vydaj"),
)


class CsskCashJournalXlsx(models.AbstractModel):
    """The peňažný denník as the first sheet of the spreadsheet.

    The same grid and the same figures as the PDF — read from
    ``_sk_dennik_values``, which the PDF renders, so the two cannot disagree:
    pokladnica, banka, priebežné položky and DPH each split into príjem and
    výdaj, the income and expense breakdown, and the running balances.

    Asked for by a customer's accountant after reviewing the PDF ("Zvlášť stĺpce
    pre príjem a výdaj v pokladni a zvlášť príjem a výdaj v banke. Tak ako je
    to v tom pdf."). The flat sheet stays after it: she pivots that one.
    Headings are the statute's own terms, in Slovak, as on the PDF.
    """

    _inherit = "report.l10n_cssk_cash_journal_base.dennik_xlsx"

    def _cssk_write_national(self, workbook, wizard, formats):
        super()._cssk_write_national(workbook, wizard, formats)
        if wizard.company_id.country_id.code != "SK":
            return
        values = self.env["report.l10n_sk_cash_journal.report_penazny_dennik"] \
            ._sk_dennik_values(wizard.company_id, wizard.date_from, wizard.date_to)
        bold, money, date_fmt = formats["bold"], formats["money"], formats["date"]
        bold_money = workbook.add_format({"bold": True, "num_format": "#,##0.00"})
        head = workbook.add_format({"bold": True, "align": "center",
                                    "valign": "vcenter", "text_wrap": True})
        sheet = workbook.add_worksheet("Peňažný denník")

        # Two header rows: a group over its príjem / výdaj pair, every other
        # heading spanning both rows.
        col = 0
        for heading in ("Dátum", "Číslo", "Doklad", "Text"):
            sheet.merge_range(0, col, 1, col, heading, head)
            col += 1
        money_cols = []
        for heading, key_in, key_out in _MONEY_GROUPS:
            sheet.merge_range(0, col, 0, col + 1, heading, head)
            sheet.write(1, col, "príjem", head)
            sheet.write(1, col + 1, "výdaj", head)
            money_cols += [(col, key_in), (col + 1, key_out)]
            col += 2
        breakdown_cols = []
        for key, heading, _codes in values["columns"]:
            sheet.merge_range(0, col, 1, col, heading, head)
            breakdown_cols.append((col, key))
            col += 1
        cash_col, bank_col = col, col + 1
        sheet.merge_range(0, cash_col, 1, cash_col, "Zostatok pokladnica", head)
        sheet.merge_range(0, bank_col, 1, bank_col, "Zostatok banka", head)
        sheet.set_row(0, 30)
        sheet.set_column(0, 0, 11)
        sheet.set_column(1, 2, 14)
        sheet.set_column(3, 3, 30)
        sheet.set_column(4, bank_col, 13)
        sheet.freeze_panes(2, 4)

        row = 2
        sheet.write(row, 3, "Počiatočný stav", bold)
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
        sheet.write(row, 3, "Spolu", bold)
        for column, key in money_cols + breakdown_cols:
            sheet.write_number(row, column, values["totals"][key], bold_money)
        sheet.write_number(row, cash_col, values["closing_cash"], bold_money)
        sheet.write_number(row, bank_col, values["closing_bank"], bold_money)
