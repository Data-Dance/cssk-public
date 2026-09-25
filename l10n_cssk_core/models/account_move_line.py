from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _cssk_statutory_footprint(self):
        """Which statutory report rows this journal item feeds — the reverse of
        the per-row drill-down. Localization modules extend this (call ``super``,
        append their own matches). Each entry is a dict ``{form, code, name}``.

        Matches against the line *definitions* (not a computed statement), so the
        footprint is available even before a return for the period is generated.
        """
        self.ensure_one()
        return []

    def _cssk_footprint_country(self):
        self.ensure_one()
        company = self.company_id or self.move_id.company_id
        return company.account_fiscal_country_id or company.country_id

    def _cssk_footprint_version_domain(self):
        """Domain fragment that scopes statutory line definitions to *this
        document's localization*: the company's fiscal country and the report
        version in effect for the move's date. Every report version carries
        ``country_id`` + ``valid_from`` / ``valid_to``, so footprint matchers
        append this to keep the result to the localization that actually applies
        — not other countries' reports nor superseded year versions."""
        self.ensure_one()
        country = self._cssk_footprint_country()
        date = self.move_id.date or self.date or fields.Date.context_today(self)
        return [
            ("version_id.country_id", "=", country.id),
            ("version_id.valid_from", "<=", date),
            "|", ("version_id.valid_to", "=", False),
            ("version_id.valid_to", ">=", date),
        ]


class CSSKStatutoryFootprintWizard(models.TransientModel):
    _name = "cssk.statutory.footprint.wizard"
    _description = "Statutory Footprint of a Document"

    move_id = fields.Many2one("account.move", readonly=True)
    line_ids = fields.One2many(
        "cssk.statutory.footprint.line", "wizard_id")


class CSSKStatutoryFootprintLine(models.TransientModel):
    _name = "cssk.statutory.footprint.line"
    _description = "Statutory Footprint Row"
    _order = "form, code"

    wizard_id = fields.Many2one(
        "cssk.statutory.footprint.wizard", ondelete="cascade")
    form = fields.Char(string="Report")
    code = fields.Char(string="Line")
    name = fields.Char(string="Description")

    # Which FILING carries this row, where one exists. It often does not, and
    # that is by design rather than a gap: the footprint matches against the
    # line DEFINITIONS precisely so a document can be asked what it feeds
    # before any return for its period has been generated. So these stay empty
    # rather than the row being hidden — "no filing yet" is information.
    filing_res_model = fields.Char(readonly=True)
    filing_res_id = fields.Integer(readonly=True)
    filing_name = fields.Char(
        string="Filing", readonly=True,
        help="The filing that reports this row, once one exists for the "
             "document's period. Empty until then.")
    filing_count = fields.Integer(
        readonly=True,
        help="More than one filing can cover a period — an amendment, or a "
             "migrated filing beside a generated one. The link then opens the "
             "list rather than picking one.")

    def action_open_filing(self):
        self.ensure_one()
        if not self.filing_res_model:
            return False
        if self.filing_res_id:
            return {
                "type": "ir.actions.act_window",
                "res_model": self.filing_res_model,
                "res_id": self.filing_res_id,
                "view_mode": "form",
                "target": "current",
            }
        move = self.wizard_id.move_id
        return {
            "type": "ir.actions.act_window",
            "name": self.filing_name or self.form,
            "res_model": self.filing_res_model,
            "view_mode": "list,form",
            "domain": [("company_id", "=", move.company_id.id)],
            "target": "current",
        }
