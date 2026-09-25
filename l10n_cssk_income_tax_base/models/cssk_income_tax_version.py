# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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
        help="Statutory minimum tax (SK: § 46b minimálna daň / daňová "
             "licencia) keyed on the same revenue line: ordered "
             "[upper_bound, amount] pairs, upper_bound inclusive, null = top "
             "band (must be last).\n\n"
             "A band may carry a third element naming a condition that "
             "turnover cannot express — the SK daňová licencia puts 480 € and "
             "960 € at the SAME bound and tells them apart by whether the "
             "taxpayer was a platiteľ DPH on the last day of the period: "
             "[[500000.0, 480.0, 'not_vat_payer'], "
             "[500000.0, 960.0, 'vat_payer'], [null, 2880.0]]. Bands are "
             "tried in order and one whose condition does not hold is "
             "skipped.\n\n"
             "Leave empty for forms without a minimum tax.")

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

    # ------------------------------------------------------------------
    # Which rows the country layer DERIVES
    # ------------------------------------------------------------------
    def _cssk_derived_codes(self):
        """Line codes this version's country layer computes arithmetically.

        A return has three kinds of row, and ``kind`` only separates two of
        them. ``kind`` names where a row's INPUT comes from — the P&L
        (``account``), the asset register (``asset_diff``), or the
        accountant (``manual``). It says nothing about whether the country
        layer then OVERWRITES the row from a formula, and on the Slovak DPPO
        it does exactly that for nineteen rows that are all ``kind='manual'``:
        the tax spine derives r310 and r400 from r100 plus the adjustments,
        while the adjustments themselves are the accountant's and are the same
        kind.

        So a consumer asking "can I check this row?" cannot answer it from
        ``kind``, and the answer used to live only inside the country module's
        Python. This hook is where it lives now.

        **Three states, not two**, and a comparator against a filed return
        wants all three:

        * ``account`` / ``asset_diff`` — we hold the input, so the row is
          checkable outright;
        * derived (this hook) — checkable ARITHMETICALLY, but only where every
          input is held; where an adjustment we never had is non-zero, the
          honest report is *uncompared*, not *differing*;
        * everything else — the accountant's judgment, never checkable.

        Reporting the second group as differences is how a comparison produces
        confident wrong answers that point at this engine.

        On the version rather than the return, for the usual reason: it
        answers a question about the DEFINITIONS, and the reverse direction —
        a bridge or a comparator holding no computed record — has to be able
        to reach it. Returns a set of codes; the base derives none.
        """
        return set()


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
