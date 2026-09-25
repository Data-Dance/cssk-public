from odoo import api, fields, models


class AccountAsset(models.Model):
    """Mix the tax-depreciation behaviour into the OCA asset model."""

    _name = "account.asset"
    _inherit = ["account.asset", "account.asset.tax.mixin"]

    @api.model_create_multi
    def create(self, vals_list):
        # Inherit the tax-depreciation defaults from the asset profile.
        for vals in vals_list:
            prof_id = vals.get("profile_id")
            if not prof_id or vals.get("tax_class_id"):
                continue
            prof = self.env["account.asset.profile"].browse(prof_id)
            if prof.tax_depreciation_enabled and prof.tax_class_id:
                vals.setdefault("tax_depreciation_enabled", True)
                vals.setdefault("tax_class_id", prof.tax_class_id.id)
                vals.setdefault("tax_method", prof.tax_method or "linear")
                vals.setdefault("tax_increased_first_year",
                                prof.tax_increased_first_year or "0")
        return super().create(vals_list)

    tax_line_ids = fields.One2many(
        "account.asset.tax.line", "asset_id", string="Tax Depreciation Board",
    )
    tax_event_ids = fields.One2many(
        "account.asset.tax.event", "asset_id", string="Tax Depreciation Events",
    )
    # Declared here (not on the abstract mixin) because they depend on
    # ``tax_line_ids``, which only exists on the concrete asset model.
    tax_value_residual = fields.Monetary(
        string="Tax Residual Value", currency_field="tax_currency_id",
        compute="_compute_tax_values", store=False,
    )
    tax_value_depreciated = fields.Monetary(
        string="Tax Depreciated", currency_field="tax_currency_id",
        compute="_compute_tax_values", store=False,
    )

    @api.depends("tax_line_ids.amount", "tax_line_ids.posted")
    def _compute_tax_values(self):
        # Derived from the board (not from tax_entry_value), so technical
        # improvements — which raise the board total without changing the entry
        # value — stay consistent. "Depreciated" = filed years; "residual" = the
        # remaining (still-claimable) tax depreciation = board total − filed.
        for asset in self:
            total = sum(asset.tax_line_ids.mapped("amount"))
            filed = sum(asset.tax_line_ids.filtered("posted").mapped("amount"))
            asset.tax_value_depreciated = filed
            asset.tax_value_residual = total - filed

    # ------------------------------------------------------------------
    # Bridge contract (see account.asset.tax.mixin)
    # ------------------------------------------------------------------
    def _tax_get_entry_value(self):
        """Tax entry price (vstupní / vstupná cena). OCA's ``purchase_value`` is
        the gross initial value before salvage — the correct tax base."""
        self.ensure_one()
        return self.purchase_value or 0.0

    def _tax_get_in_service_date(self):
        """OCA's ``date_start`` is the depreciation start / in-service date."""
        self.ensure_one()
        return self.date_start

    def _tax_accounting_depreciation_for_period(self, date_from, date_to):
        """Posted accounting depreciation (OCA depreciation lines) in the period."""
        self.ensure_one()
        lines = self.depreciation_line_ids.filtered(
            lambda l: l.type == "depreciate"
            and l.line_date and date_from <= l.line_date <= date_to
            and l.move_id
        )
        return sum(lines.mapped("amount"))

    def _tax_accounting_residual(self, on_date):
        """Accounting net book value at ``on_date`` = purchase value less the
        accounting depreciation posted through that date."""
        self.ensure_one()
        posted = self.depreciation_line_ids.filtered(
            lambda l: l.type == "depreciate" and l.move_id
            and l.line_date and l.line_date <= on_date
        )
        return (self.purchase_value or 0.0) - sum(posted.mapped("amount"))

    def _cssk_book_depreciation_by_year(self):
        """OCA book depreciation per year from the depreciation table (posted or
        planned), with the year-end book net value (``remaining_value``)."""
        self.ensure_one()
        lines = self.depreciation_line_ids.filtered(
            lambda l: l.type == "depreciate" and l.line_date
        )
        by_year = {}
        residual = {}
        for line in lines.sorted("line_date"):
            year = line.line_date.year
            by_year.setdefault(year, 0.0)
            by_year[year] += line.amount
            residual[year] = line.remaining_value
        return {y: {"amount": by_year[y], "residual": residual[y]} for y in by_year}

    def write(self, vals):
        """The OCA removal wizard sets ``state='removed'``; record the tax
        disposal event when it does."""
        res = super().write(vals)
        if vals.get("state") == "removed":
            for asset in self:
                asset._tax_register_disposal(asset.date_remove or fields.Date.context_today(asset))
        return res
