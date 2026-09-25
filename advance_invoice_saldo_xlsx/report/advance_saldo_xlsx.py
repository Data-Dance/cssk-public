# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).

from odoo import models

HEADERS = (
    "Number", "Partner", "Date", "Currency", "Total", "Paid", "Paid Date",
    "Tax Documented", "Deducted", "Open (Paid − Deducted)",
    "Payment Status", "Accounting Status",
)


class AdvanceSaldoXlsx(models.AbstractModel):
    _name = "report.advance_invoice_saldo_xlsx.saldo"
    _description = "Open Advances Saldo XLSX"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, wizards):
        wizard = wizards[:1]
        bold = workbook.add_format({"bold": True})
        money = workbook.add_format({"num_format": "#,##0.00"})
        date_fmt = workbook.add_format({"num_format": "yyyy-mm-dd"})
        for title, rows in (
            (self.env._("Issued advances"), self._sale_rows(wizard)),
            (self.env._("Received advances"), self._purchase_rows(wizard)),
        ):
            sheet = workbook.add_worksheet(title)
            sheet.set_column(0, 1, 24)
            sheet.set_column(2, 2, 12)
            sheet.set_column(3, 3, 9)
            sheet.set_column(4, 9, 15)
            sheet.set_column(10, 11, 16)
            for col, header in enumerate(HEADERS):
                sheet.write(0, col, header, bold)
            for row_index, row in enumerate(rows, start=1):
                for col, value in enumerate(row):
                    if col == 2 or col == 6:
                        if value:
                            sheet.write_datetime(
                                row_index, col, value, date_fmt
                            )
                    elif col in (4, 5, 7, 8, 9):
                        sheet.write_number(row_index, col, value, money)
                    else:
                        sheet.write(row_index, col, value or "")

    def _keep(self, wizard, order, paid, deducted, accounting_status,
              payment_status):
        if wizard.include_settled:
            return True
        if order.currency_id.compare_amounts(paid - deducted, 0.0) != 0:
            return True
        return (
            accounting_status == "waiting"
            or payment_status in ("none", "paid_partially")
        )

    def _selection_label(self, record, field_name):
        return dict(
            record._fields[field_name]._description_selection(self.env)
        ).get(record[field_name], record[field_name] or "")

    def _sale_rows(self, wizard):
        orders = self.env["sale.order"].search([
            ("company_id", "=", wizard.company_id.id),
            ("is_advance_invoice", "=", True),
            ("state", "!=", "cancel"),
        ], order="date_order, name")
        rows = []
        for order in orders:
            paid = order.amount_paid
            accounted = sum(
                invoice.amount_total
                for invoice in order.invoice_ids
                if invoice.move_type == "out_invoice"
                and invoice.state == "posted"
            )
            deducted = self._sale_deducted(order)
            if not self._keep(
                wizard, order, paid, deducted,
                order.advance_invoice_accounting_status,
                order.advance_invoice_payment_status,
            ):
                continue
            rows.append((
                order.name,
                order.partner_id.display_name,
                order.date_order and order.date_order.date(),
                order.currency_id.name,
                order.amount_total,
                paid,
                order.advance_invoice_paid_date,
                accounted,
                deducted,
                paid - deducted,
                self._selection_label(order, "advance_invoice_payment_status"),
                self._selection_label(
                    order, "advance_invoice_accounting_status"
                ),
            ))
        return rows

    def _sale_deducted(self, order):
        parent = order.advance_invoice_parent_order_id
        if not parent:
            return 0.0
        lines = parent.order_line.filtered(
            lambda line: line.is_advance_tracking
            and line.advance_source_order_id == order
        ).invoice_lines.filtered(
            lambda line: line.move_id.state == "posted"
            and line.move_id.move_type == "out_invoice"
        )
        return -sum(lines.mapped("price_total"))

    def _purchase_rows(self, wizard):
        orders = self.env["purchase.order"].search([
            ("company_id", "=", wizard.company_id.id),
            ("is_advance_invoice", "=", True),
            ("state", "!=", "cancel"),
        ], order="date_order, name")
        rows = []
        for order in orders:
            paid = order.amount_paid
            deducted = order._advance_deducted_amount_now()
            if not self._keep(
                wizard, order, paid, deducted,
                order.advance_invoice_accounting_status,
                order.advance_invoice_payment_status,
            ):
                continue
            rows.append((
                order.name,
                order.partner_id.display_name,
                order.date_order and order.date_order.date(),
                order.currency_id.name,
                order.amount_total,
                paid,
                order.advance_invoice_paid_date,
                order.advance_accounted_amount,
                deducted,
                paid - deducted,
                self._selection_label(order, "advance_invoice_payment_status"),
                self._selection_label(
                    order, "advance_invoice_accounting_status"
                ),
            ))
        return rows
