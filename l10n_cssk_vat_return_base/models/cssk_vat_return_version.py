from odoo import fields, models


class CSSKVatReturnVersion(models.Model):
    """A versioned VAT-return template (DPH priznanie / DPHDP3)."""

    _name = "cssk.vat.return.version"
    _description = "VAT Return Version"
    _order = "country_id, valid_from desc"

    name = fields.Char(required=True)  # e.g. "SK DPH 2025"
    country_id = fields.Many2one("res.country", required=True)
    active = fields.Boolean(default=True)
    valid_from = fields.Date(required=True)
    valid_to = fields.Date()

    line_def_ids = fields.One2many(
        "cssk.vat.return.line.def", "version_id"
    )
    statement_type_ids = fields.One2many(
        "cssk.vat.return.type", "version_id"
    )

    xml_template_ref_id = fields.Many2one(
        "ir.ui.view", string="XML template", required=True,
        domain="[('type', '=', 'qweb')]",
        help="QWeb template (ir.ui.view) that renders this version's "
        "statutory XML.",
    )
    xml_schema_data = fields.Binary(attachment=True)
    xml_schema_filename = fields.Char()
    xml_root_element = fields.Char(
        required=True, help="Expected root element, e.g. 'DPH' / 'DPHDP3'."
    )

    allow_monthly = fields.Boolean(default=True)
    allow_quarterly = fields.Boolean(default=True)

    # --- form-specific line codes / constants (version DATA, not code) -----
    # The shared base must not hardcode any country's form lines; the country
    # modules set these on their version records instead.
    own_tax_line_code = fields.Char(
        string="Own-tax line code",
        help="Line code of the period's own tax liability (vlastná daňová "
             "povinnosť / vlastní daň), e.g. 'r32' on the SK DPHv25 form. "
             "Drives the § 79-style settlement (To pay / (refund)); leave "
             "empty if the form has no such settlement.")
    excess_line_code = fields.Char(
        string="Excess-deduction line code",
        help="Line code of the period's excess deduction (nadmerný odpočet "
             "/ nadměrný odpočet), e.g. 'r33' on the SK DPHv25 form. Drives "
             "the settlement and the carry-forward cap check; leave empty if "
             "the form has no such settlement.")
    diff_line_code = fields.Char(
        string="Amendment-difference line code",
        help="Line code of the 'difference vs the last known tax' row an "
             "amended (dodatočné) return reports, e.g. 'r36' on the SK "
             "DPHv25 form. Auto-filled from the original return on "
             "recompute; leave empty if the form has no such row.")
    rate_pairs = fields.Json(
        string="Rate pairs",
        help="Statutory base/tax rate pairing for the kontrolné pravidlá, "
             "as a list of [base_line_code, tax_line_code, rate] items "
             "(rate may itself be a list when several rates share the "
             "rows), e.g. [['r03', 'r04', 23.0]] — the implied rate "
             "|tax|/|base|×100 must match. Version DATA, not code: the "
             "pairing follows the form vintage (DPHv25: 19/5/23; older "
             "forms: 10/20).")


class CSSKVatReturnLineDef(models.Model):
    """A VAT-return line definition.

    ``tags``      → value = signed sum of move-line balances carrying the tax
                    tag named by ``tag_formula`` (the leading '-' is the sign).
    ``aggregate`` → value = ``aggregate_formula`` evaluated over other line
                    codes (e.g. ``r04 + r06``).
    ``manual``    → entered by the user.
    """

    _name = "cssk.vat.return.line.def"
    _description = "VAT Return Line Definition"
    _order = "version_id, sequence, code"

    version_id = fields.Many2one(
        "cssk.vat.return.version", required=True, ondelete="cascade"
    )
    code = fields.Char(required=True, help="Stable line code, e.g. 'r03'.")
    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    kind = fields.Selection(
        [
            ("tags", "Tax tags"),
            ("aggregate", "Aggregate of other lines"),
            ("manual", "Manual"),
        ],
        required=True,
        default="tags",
    )
    tag_formula = fields.Char(
        help="Tax-tag formula for kind=tags, e.g. '-03' (tag '03', sign −1).",
    )
    line_filter = fields.Char(
        help="Optional extra restriction on the move lines a kind=tags line "
        "collects, named by a country module and resolved in "
        "``_cssk_tag_line_filter``.\n\n"
        "It exists for a split that no TAG can express, because the chart has "
        "one tax where an older form had two rows. The Slovak § 69 ods. 3 is "
        "the case: the current tlačivo merges it into r09/r10, so l10n_sk "
        "carries a single reverse-charge family, and the pre-2021 vzory need "
        "it separated again.\n\n"
        "Left empty — which every line of every current form is — the line "
        "collects its tags exactly as before.",
    )
    aggregate_formula = fields.Char(
        help="Formula over line codes for kind=aggregate, e.g. 'r04 + r06'.",
    )


class CSSKVatReturnType(models.Model):
    """Submission type (riadne / opravné / dodatočné)."""

    _name = "cssk.vat.return.type"
    _description = "VAT Return Submission Type"
    _order = "version_id, sequence"

    version_id = fields.Many2one(
        "cssk.vat.return.version", required=True, ondelete="cascade"
    )
    code = fields.Char(required=True)
    name = fields.Char(required=True)
    fa_xml_value = fields.Char(
        required=True, help="Value emitted in the statutory XML for this type."
    )
    sequence = fields.Integer(default=10)
