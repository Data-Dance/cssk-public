import io

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestStatementXlsx(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.account_fiscal_country_id = cls.env.ref("base.sk")
        journal = cls.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", cls.company.id)],
            limit=1)
        asset = cls.env["account.account"].create({
            "name": "Stroje", "code": "022997",
            "account_type": "asset_non_current",
            "company_ids": [(6, 0, cls.company.ids)]})
        equity = cls.env["account.account"].create({
            "name": "Základné imanie", "code": "411997", "account_type": "equity",
            "company_ids": [(6, 0, cls.company.ids)]})
        move = cls.env["account.move"].create({
            "move_type": "entry", "journal_id": journal.id, "date": "2026-06-30",
            "line_ids": [(0, 0, {"account_id": asset.id, "debit": 900.0}),
                         (0, 0, {"account_id": equity.id, "credit": 900.0})]})
        move.action_post()
        template = cls.env["ir.ui.view"].create({
            "name": "xlsx test template", "type": "qweb",
            "arch": "<t t-name='cssk_fs_xlsx_test'><FS/></t>"})
        version = cls.env["cssk.fs.statement.version"].create({
            "name": "TST", "country_id": cls.env.ref("base.sk").id,
            "statement_kind": "balance_sheet", "valid_from": "2025-01-01",
            "xml_template_ref_id": template.id, "xml_root_element": "FS",
            "xml_schema_optional": True,
            "line_def_ids": [
                (0, 0, {"code": "tot", "name": "SPOLU", "kind": "aggregate",
                        "aggregate_formula": "dhm", "sequence": 5}),
                (0, 0, {"code": "dhm", "name": "Samostatné hnuteľné veci",
                        "kind": "accounts", "account_formula": "022",
                        "sequence": 10}),
            ]})
        cls.statement = cls.env["cssk.fs.statement"].create({
            "company_id": cls.company.id, "version_id": version.id,
            "date_from": "2026-01-01", "date_to": "2026-12-31"})
        cls.statement.action_compute_lines()

    def test_workbook_lists_rows_and_their_accounts(self):
        content, kind = self.env["ir.actions.report"]._render(
            "l10n_cssk_fs_xlsx.statement_xlsx", self.statement.ids)
        self.assertEqual(kind, "xlsx")
        try:
            import openpyxl
        except ImportError:
            self.skipTest("openpyxl is not installed")
        sheet = openpyxl.load_workbook(io.BytesIO(content)).worksheets[0]
        cells = [[c for c in row] for row in sheet.iter_rows(values_only=True)]
        row_dhm = next(r for r in cells if r[0] == "dhm")
        self.assertEqual(row_dhm[5], 900.0)
        account = next(r for r in cells if r[2] == "022997")
        self.assertIn("Stroje", account[1])
        self.assertEqual(account[5], 900.0)
