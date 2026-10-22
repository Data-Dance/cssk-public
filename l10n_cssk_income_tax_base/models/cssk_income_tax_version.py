# Copyright 2026 Data Dance s.r.o.
# Data Dance Proprietary License v1.0 — see the LICENSE file.

from odoo import fields, models


class CSSKIncomeTaxVersion(models.Model):
    """A versioned corporate income-tax return template (DPPO / DPPO CZ)."""

    _name = "cssk.income.tax.version"
    _description = "Income Tax Return Version"
    _order = "country_id, valid_from desc"

    name = fields.Char(required=True)  # e.g. "SK DPPO 2025"
    country_id = fields.Many2one("res.country", required=True)
    active = fields.Boolean(default=True)
    valid_from = fields.Date(required=True)
    valid_to = fields.Date()

    line_def_ids = fields.One2many("cssk.income.tax.line.def", "version_id")
    statement_type_ids = fields.One2many("cssk.income.tax.type", "version_id")

    xml_template_ref_id = fields.Many2one(
        "ir.ui.view", string="XML template", required=True,
        domain="[('type', '=', 'qweb')]",
        help="QWeb template (ir.ui.view) that renders this version's "
        "statutory XML.",
    )
    xml_schema_data = fields.Binary(attachment=True)
    xml_schema_filename = fields.Char()
    xml_root_element = fields.Char(
        required=True, help="Expected root element, e.g. 'dokument'."
    )

    # Statutory rate / minimum-tax schedules — DATA, not code. Both are
    # ordered lists of ``[upper_bound, value]`` pairs keyed on the version's
    # revenue line (SK DPPO: r560 úhrn zdaniteľných príjmov); ``upper_bound``
    # is INCLUSIVE and ``null`` marks the top (unbounded) band, which must be
    # last. Country modules read them (e.g. l10n_sk_dppo's _dppo_rate /
    # _dppo_min_tax) and must fail loudly when a version lacks the bands —
    # never guess a statutory rate in code.
    rate_bands = fields.Json(
        string="Rate bands",
        help="Statutory income-tax rate schedule keyed on the revenue line "
             "(SK: § 15 by r560): ordered [upper_bound, rate_percent] pairs, "
             "upper_bound inclusive, null = top band (must be last). "
             "Example (SK 2025): [[100000.0, 10.0], [5000000.0, 21.0], "
             "[null, 24.0]].")
    min_tax_bands = fields.Json(
        string="Minimum-tax bands",
        help="Statutory minimum tax (SK: § 46b minimálna daň) keyed on the "
             "same revenue line: ordered [upper_bound, amount] pairs, "
             "upper_bound inclusive, null = top band (must be last). Leave "
             "empty for forms without a minimum tax.")

    # Year-end income-tax provision (MD splatná daň / D daňový záväzok).
    provision_line_code = fields.Char(
        help="Computed line whose value is the bookable current income tax "
             "posted as the year-end provision — e.g. 'r1050' (SK DPPO daňová "
             "povinnosť) / 'r340' (CZ DPPDP9 celková daňová povinnost).")
    provision_expense_code = fields.Char(
        default="591",
        help="Account-code prefix for the income-tax expense (MD) — 591 "
             "Splatná daň z príjmov / Daň z příjmů splatná.")
    provision_payable_code = fields.Char(
        default="341",
        help="Account-code prefix for the income-tax payable (D) — 341 Daň "
             "z príjmov / Daň z příjmů.")


class CSSKIncomeTaxLineDef(models.Model):
    """An income-tax return line definition.

    ``account``   → value = period balance of the P&L account-code prefixes in
                    ``account_formula`` (leading '-' negates); used for the
                    accounting result (výsledok hospodárenia) the return starts
                    from.
    ``aggregate`` → value = ``aggregate_formula`` over other line codes
                    (e.g. ``r100 + r110 - r130``) — the tax-computation spine.
    ``manual``    → entered by the accountant (the tax adjustments).
    """

    _name = "cssk.income.tax.line.def"
    _description = "Income Tax Return Line Definition"
    _order = "version_id, sequence, code"

    version_id = fields.Many2one(
        "cssk.income.tax.version", required=True, ondelete="cascade"
    )
    code = fields.Char(required=True, help="Stable line code, e.g. 'r100'.")
    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    kind = fields.Selection(
        [
            ("account", "Accounting result (P&L)"),
            ("aggregate", "Aggregate of other lines"),
            ("asset_diff", "Asset book-vs-tax depreciation difference"),
            ("manual", "Manual"),
        ],
        required=True,
        default="manual",
    )
    account_formula = fields.Char(
        help="Comma-separated P&L account-code prefixes for kind=account. Each "
        "prefix contributes −(its period balance) so revenues−expenses = "
        "profit; a leading '-' flips the sign (adds the component back). "
        "E.g. '5,6,-591,-592' = výsledok hospodárenia pred zdanením (profit "
        "before income tax, adding back income-tax accounts 591/592).",
    )
    aggregate_formula = fields.Char(
        help="Formula over line codes for kind=aggregate, e.g. 'r100 + r110'.",
    )
    in_xml = fields.Boolean(
        default=True,
        help="Whether this line maps to an element in the statutory XML.",
    )


class CSSKIncomeTaxType(models.Model):
    """Submission type (riadne / opravné / dodatočné)."""

    _name = "cssk.income.tax.type"
    _description = "Income Tax Return Submission Type"
    _order = "version_id, sequence"

    version_id = fields.Many2one(
        "cssk.income.tax.version", required=True, ondelete="cascade"
    )
    code = fields.Char(required=True)
    name = fields.Char(required=True)
    fa_xml_value = fields.Char(
        required=True, help="Value emitted in the statutory XML for this type."
    )
    sequence = fields.Integer(default=10)
