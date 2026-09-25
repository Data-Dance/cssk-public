import base64
import io

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class AccountAssetTaxReconciliation(models.TransientModel):
    """Accounting-vs-tax depreciation reconciliation for a fiscal period (DPPO).

    For each asset that tracks tax depreciation, compares the posted *accounting*
    depreciation (bridge-specific) with the *tax* board over the period, and
    classifies the difference:

    * accounting > tax  -> **add-back** (SK DPPO line 150 / CZ ř. 50)
    * tax > accounting  -> **deduction** (SK DPPO line 250)
    """

    _name = "account.asset.tax.reconciliation"
    _description = "Tax Depreciation Reconciliation (DPPO)"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    tax_rate = fields.Float(
        string="Income Tax Rate (%)", default=21.0,
        help="Corporate income-tax rate used for the deferred-tax computation "
        "from the cumulative accounting-vs-tax temporary difference (CZ/SK: 21%).",
    )
    line_ids = fields.One2many(
        "account.asset.tax.reconciliation.line", "wizard_id", readonly=True,
    )
    total_accounting = fields.Monetary(compute="_compute_totals")
    total_tax = fields.Monetary(compute="_compute_totals")
    total_addback = fields.Monetary(compute="_compute_totals")
    total_deduction = fields.Monetary(compute="_compute_totals")
    total_deferred_tax = fields.Monetary(
        compute="_compute_totals",
        help="Net deferred tax: positive = liability (DTL), negative = asset (DTA).",
    )
    post_deferred_immediately = fields.Boolean(
        string="Post Deferred Tax Immediately",
        help="Post the deferred-tax journal entry straight away instead of "
        "leaving it in draft for review.",
    )
    xlsx_file = fields.Binary(string="Export", readonly=True)
    xlsx_filename = fields.Char()

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # default to the current calendar year
        today = fields.Date.context_today(self)
        res.setdefault("date_from", today.replace(month=1, day=1))
        res.setdefault("date_to", today.replace(month=12, day=31))
        return res

    @api.depends("line_ids")
    def _compute_totals(self):
        for wiz in self:
            wiz.total_accounting = sum(wiz.line_ids.mapped("accounting_amount"))
            wiz.total_tax = sum(wiz.line_ids.mapped("tax_amount"))
            wiz.total_addback = sum(wiz.line_ids.mapped("addback"))
            wiz.total_deduction = sum(wiz.line_ids.mapped("deduction"))
            wiz.total_deferred_tax = sum(wiz.line_ids.mapped("deferred_tax"))

    def action_compute(self):
        self.ensure_one()
        Line = self.env["account.asset.tax.reconciliation.line"]
        self.line_ids.unlink()
        assets = self.env["account.asset"].search([
            ("tax_depreciation_enabled", "=", True),
            ("company_id", "=", self.company_id.id),
        ])
        rate = (self.tax_rate or 0.0) / 100.0
        vals = []
        for asset in assets:
            acc = asset._tax_accounting_depreciation_for_period(self.date_from, self.date_to)
            tax = asset._tax_depreciation_for_period(self.date_from, self.date_to)
            # cumulative (balance-sheet) view for deferred tax at period end
            acc_nbv = asset._tax_accounting_residual(self.date_to)
            tax_res = asset.tax_residual_at_year_end(self.date_to.year)
            temp_diff = acc_nbv - tax_res          # +: taxable (DTL); -: deductible (DTA)
            deferred = temp_diff * rate
            if not acc and not tax and not temp_diff:
                continue
            diff = acc - tax
            vals.append({
                "wizard_id": self.id,
                "asset_ref_id": asset.id,
                "asset_name": asset.display_name,
                "tax_class_name": asset.tax_class_id.display_name,
                "accounting_amount": acc,
                "tax_amount": tax,
                "difference": diff,
                "addback": max(diff, 0.0),
                "deduction": max(-diff, 0.0),
                "accounting_residual": acc_nbv,
                "tax_residual": tax_res,
                "temp_difference": temp_diff,
                "deferred_tax": deferred,
            })
        Line.create(vals)
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.asset.tax.reconciliation",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "name": _("Tax Depreciation Reconciliation"),
        }

    def action_print_pdf(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("Compute the reconciliation first."))
        return self.env.ref(
            "account_asset_tax.action_report_reconciliation").report_action(self)

    def action_export_xlsx(self):
        """Export the reconciliation as a DPPO Table-B style spreadsheet."""
        self.ensure_one()
        if xlsxwriter is None:
            raise UserError(_("The python 'xlsxwriter' library is not available."))
        if not self.line_ids:
            raise UserError(_("Compute the reconciliation first."))
        buf = io.BytesIO()
        wb = xlsxwriter.Workbook(buf, {"in_memory": True})
        ws = wb.add_worksheet("DPPO Table B")
        bold = wb.add_format({"bold": True})
        money = wb.add_format({"num_format": "#,##0.00"})
        money_b = wb.add_format({"bold": True, "num_format": "#,##0.00"})
        headers = [
            "Asset", "Tax group", "Accounting depreciation", "Tax depreciation",
            "Difference", "Add-back (150)", "Deduction (250)",
            "Accounting NBV", "Tax residual", "Temporary difference", "Deferred tax",
        ]
        for col, head in enumerate(headers):
            ws.write(0, col, head, bold)
        ws.set_column(0, 0, 32)
        ws.set_column(1, len(headers) - 1, 16)
        row = 1
        for ln in self.line_ids:
            ws.write(row, 0, ln.asset_name or "")
            ws.write(row, 1, ln.tax_class_name or "")
            for col, val in enumerate([
                ln.accounting_amount, ln.tax_amount, ln.difference, ln.addback,
                ln.deduction, ln.accounting_residual, ln.tax_residual,
                ln.temp_difference, ln.deferred_tax,
            ], start=2):
                ws.write_number(row, col, val or 0.0, money)
            row += 1
        ws.write(row, 0, "Total", bold)
        ws.write_number(row, 2, self.total_accounting or 0.0, money_b)
        ws.write_number(row, 3, self.total_tax or 0.0, money_b)
        ws.write_number(row, 5, self.total_addback or 0.0, money_b)
        ws.write_number(row, 6, self.total_deduction or 0.0, money_b)
        ws.write_number(row, 10, self.total_deferred_tax or 0.0, money_b)
        wb.close()
        self.xlsx_file = base64.b64encode(buf.getvalue())
        self.xlsx_filename = "dppo_table_b_%s.xlsx" % self.date_to
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/account.asset.tax.reconciliation/%d/xlsx_file/%s?download=true"
                   % (self.id, self.xlsx_filename),
            "target": "self",
        }

    def action_post_deferred_tax(self):
        """Create a DRAFT journal entry truing-up the deferred-tax balance (481)
        to the computed closing position. Left in draft for the accountant to
        review and post.

        Dr 592 / Cr 481 to increase a deferred-tax liability (or the reverse to
        reduce it / book a deferred-tax asset).
        """
        self.ensure_one()
        company = self.company_id
        journal = company.tax_deferred_journal_id
        acc_bs = company.account_deferred_tax_id
        acc_pl = company.account_deferred_tax_pl_id
        if not (journal and acc_bs and acc_pl):
            raise UserError(_(
                "Configure the deferred-tax journal and the 481 / 592 accounts on "
                "the company before posting deferred tax."))
        if not self.line_ids:
            raise UserError(_("Compute the reconciliation first."))
        ccy = company.currency_id
        closing_dtl = sum(self.line_ids.mapped("deferred_tax"))   # +DTL / -DTA
        # current DTL = credit balance on the 481 account
        bs_lines = self.env["account.move.line"].search([
            ("account_id", "=", acc_bs.id),
            ("parent_state", "=", "posted"),
            ("company_id", "=", company.id),
        ])
        current_dtl = -sum(bs_lines.mapped("balance"))
        delta = closing_dtl - current_dtl
        if ccy.is_zero(delta):
            return {
                "type": "ir.actions.client", "tag": "display_notification",
                "params": {"type": "info", "title": _("Nothing to post"),
                           "message": _("The deferred-tax balance already matches."),
                           "sticky": False},
            }
        # delta > 0: increase liability -> Dr 592, Cr 481
        bs_debit, bs_credit = (0.0, delta) if delta > 0 else (-delta, 0.0)
        pl_debit, pl_credit = (delta, 0.0) if delta > 0 else (0.0, -delta)
        move = self.env["account.move"].create({
            "journal_id": journal.id,
            "date": self.date_to,
            "ref": _("Deferred tax on depreciation difference %s") % self.date_to,
            "company_id": company.id,
            "line_ids": [
                Command.create({
                    "account_id": acc_bs.id, "name": _("Deferred tax (481)"),
                    "debit": bs_debit, "credit": bs_credit,
                }),
                Command.create({
                    "account_id": acc_pl.id, "name": _("Deferred tax (592)"),
                    "debit": pl_debit, "credit": pl_credit,
                }),
            ],
        })
        if self.post_deferred_immediately:
            move.action_post()
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": move.id,
            "view_mode": "form",
            "name": _("Deferred Tax Entry"),
        }


class AccountAssetTaxReconciliationLine(models.TransientModel):
    _name = "account.asset.tax.reconciliation.line"
    _description = "Tax Depreciation Reconciliation Line"
    _order = "asset_name"

    wizard_id = fields.Many2one(
        "account.asset.tax.reconciliation", required=True, ondelete="cascade",
    )
    currency_id = fields.Many2one(related="wizard_id.currency_id")
    # asset stored as a plain id (no FK) so this stays in the asset-agnostic core
    asset_ref_id = fields.Integer(string="Asset ID")
    asset_name = fields.Char(string="Asset")
    tax_class_name = fields.Char(string="Tax Group")
    accounting_amount = fields.Monetary(string="Accounting Depreciation")
    tax_amount = fields.Monetary(string="Tax Depreciation")
    difference = fields.Monetary(string="Difference (Acc − Tax)")
    addback = fields.Monetary(string="Add-back (line 150)")
    deduction = fields.Monetary(string="Deduction (line 250)")
    # cumulative temporary difference + deferred tax (balance-sheet view)
    accounting_residual = fields.Monetary(string="Accounting NBV")
    tax_residual = fields.Monetary(string="Tax Residual")
    temp_difference = fields.Monetary(string="Temporary Difference")
    deferred_tax = fields.Monetary(
        string="Deferred Tax",
        help="Positive = deferred tax liability (DTL); negative = deferred tax asset (DTA).",
    )

    def action_open_asset(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.asset",
            "res_id": self.asset_ref_id,
            "view_mode": "form",
        }
