from odoo import api, fields, models


class CSSKTaxAuthority(models.Model):
    """A tax office used as the addressee of statutory filings.

    Delegates to ``res.partner`` (``_inherits``) so an office carries a full
    address book entry (name, address, contact). Country data modules
    (``l10n_sk_*`` / ``l10n_cz_*``) seed the offices; the ``submission_code`` is
    what goes into the FS SR / EPO XML, so it must be kept stable once a filing
    references it.
    """

    _name = "cssk.tax.authority"
    _description = "Tax Authority"
    _inherits = {"res.partner": "partner_id"}
    _order = "country_code, code"

    partner_id = fields.Many2one(
        "res.partner", string="Related Partner", required=True,
        ondelete="cascade", index=True,
        help="Address book entry holding this office's name and address.",
    )
    code = fields.Char(
        required=True,
        help="Stable technical code, e.g. SK-BA-1 / CZ-1. Referenced by country "
        "data and statements; do not change after a statement references it.",
    )
    country_code = fields.Selection(
        [("CZ", "Czech Republic"), ("SK", "Slovakia")],
        string="Country code",
        compute="_compute_country_code", store=True, index=True,
        help="CZ / SK code derived from the office's country (country_id). "
        "Drives the statutory routing and the per-country record rule.",
    )

    @api.depends("partner_id.country_id")
    def _compute_country_code(self):
        for rec in self:
            code = rec.partner_id.country_id.code
            rec.country_code = code if code in ("CZ", "SK") else False
    submission_code = fields.Char(
        help="Code emitted in the statutory XML submission (FS SR / Finanční "
        "správa EPO identifier of the office).",
    )
    parent_authority_id = fields.Many2one(
        "cssk.tax.authority", string="Regional office",
        ondelete="cascade", index=True,
        help="For a territorial workplace (územní pracoviště), the regional "
        "finanční úřad it belongs to. Empty for the regional offices "
        "themselves.",
    )
    child_authority_ids = fields.One2many(
        "cssk.tax.authority", "parent_authority_id", string="Workplaces",
    )
    child_authority_count = fields.Integer(
        compute="_compute_child_authority_count", string="# Workplaces",
    )

    @api.depends("child_authority_ids")
    def _compute_child_authority_count(self):
        for rec in self:
            rec.child_authority_count = len(rec.child_authority_ids)

    _uniq_code_per_country = models.Constraint(
        "UNIQUE(country_code, code)",
        "The tax-authority code must be unique per country.",
    )
