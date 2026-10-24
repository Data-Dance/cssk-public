from odoo import models


class StatementXlsx(models.AbstractModel):
    _name = "report.l10n_cssk_fs_xlsx.statement_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Financial statement with accounts (XLSX)"

    def _get_report_name(self, report, data=False):
        return self.env._("Financial statement")

    def generate_xlsx_report(self, workbook, data, statements):
        fmt = {
            "title": workbook.add_format({"bold": True, "font_size": 13}),
            "head": workbook.add_format({"bold": True, "bottom": 1,
                                         "text_wrap": True, "valign": "top"}),
            "total": workbook.add_format({"bold": True}),
            "total_num": workbook.add_format({"bold": True,
                                              "num_format": "#,##0.00"}),
            "num": workbook.add_format({"num_format": "#,##0.00"}),
            "acc": workbook.add_format({"italic": True, "font_color": "#555555"}),
            "acc_num": workbook.add_format({"italic": True, "font_color": "#555555",
                                            "num_format": "#,##0.00"}),
        }
        for statement in statements:
            for title, lines in self._sections(statement):
                self._write_sheet(workbook, fmt, statement, title, lines)

    def _sections(self, statement):
        """One sheet per part of the document: a combined Úč POD is a súvaha
        and a výkaz ziskov a strát (``in_movement_section``)."""
        lines = statement.line_ids.sorted("sequence")
        if "in_movement_section" in lines._fields:
            balance = lines.filtered(lambda line: not line.in_movement_section)
            movement = lines - balance
            if balance and movement:
                return [(self.env._("Balance sheet"), balance),
                        (self.env._("Income statement"), movement)]
        return [(statement.display_name, lines)]

    def _write_sheet(self, workbook, fmt, statement, title, lines):
        _ = self.env._
        name = "".join(ch for ch in title if ch not in "[]:*?/\\")[:31]
        sheet = workbook.add_worksheet(name or "Sheet")
        sheet.write(0, 0, "%s — %s" % (statement.company_id.name, title),
                    fmt["title"])
        prior_from, prior_to = statement._prior_dates()
        sheet.write(1, 0, _("Period: %(from)s – %(to)s; prior period: "
                            "%(pfrom)s – %(pto)s",
                            **{"from": statement.date_from,
                               "to": statement.date_to,
                               "pfrom": prior_from, "pto": prior_to}))
        headers = [_("Row"), _("Line / account"), _("Account"),
                   _("Gross"), _("Correction"), _("Net"),
                   _("Net (prior period)")]
        for col, header in enumerate(headers):
            sheet.write(3, col, header, fmt["head"])
        sheet.set_column(0, 0, 8)
        sheet.set_column(1, 1, 60)
        sheet.set_column(2, 2, 10)
        sheet.set_column(3, 6, 16)
        sheet.freeze_panes(4, 2)

        defs = {ldef.code: ldef for ldef in statement.version_id.line_def_ids}
        cache_cur, cache_prior = {}, {}
        row = 4
        for line in lines:
            bold = not line.is_leaf
            label = "    " * max(line.level or 0, 0) + (line.name or "")
            sheet.write(row, 0, line.code or "", fmt["total"] if bold else None)
            sheet.write(row, 1, label, fmt["total"] if bold else None)
            number = fmt["total_num"] if bold else fmt["num"]
            sheet.write_number(row, 3, line.gross_value or 0.0, number)
            sheet.write_number(row, 4, line.correction_value or 0.0, number)
            sheet.write_number(row, 5, line.current_value or 0.0, number)
            sheet.write_number(row, 6, line.prior_value or 0.0, number)
            row += 1
            ldef = defs.get(line.code)
            if not ldef or not line.is_leaf:
                continue
            for acc in self._accounts(statement, ldef, cache_cur, cache_prior):
                sheet.write(row, 1, "        " + (acc["name"] or ""), fmt["acc"])
                sheet.write(row, 2, acc["code"], fmt["acc"])
                sheet.write_number(row, 3, acc["base"], fmt["acc_num"])
                sheet.write_number(row, 4, acc["correction"], fmt["acc_num"])
                sheet.write_number(row, 5, acc["value"], fmt["acc_num"])
                sheet.write_number(row, 6, acc["prior"], fmt["acc_num"])
                row += 1

    def _accounts(self, statement, ldef, cache_cur, cache_prior):
        """The row's accounts, current and prior period side by side."""
        current = statement._fs_row_accounts(
            ldef, statement.date_from, statement.date_to, cache=cache_cur)
        prior_from, prior_to = statement._prior_dates()
        prior = statement._fs_row_accounts(
            ldef, prior_from, prior_to, cache=cache_prior)
        merged = {}
        for entry in current:
            merged[entry["account"].id] = {
                "code": entry["account"].code, "name": entry["account"].name,
                "base": entry["base"], "correction": entry["correction"],
                "value": entry["value"], "prior": 0.0}
        for entry in prior:
            item = merged.setdefault(entry["account"].id, {
                "code": entry["account"].code, "name": entry["account"].name,
                "base": 0.0, "correction": 0.0, "value": 0.0, "prior": 0.0})
            item["prior"] = entry["value"]
        return sorted(merged.values(), key=lambda item: item["code"] or "")
