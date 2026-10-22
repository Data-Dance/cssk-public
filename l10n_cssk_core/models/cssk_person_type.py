from odoo import fields, models


class CSSKPersonType(models.Model):
    """Person / entity type catalogue (fyzická osoba, právnická osoba, …).

    Used by statutory reports that classify the counterparty (e.g. control
    statement section selection, financial-statement entity-size variants).
    Seeded per country by the country data modules.
    """

    _name = "cssk.person.type"
    _description = "Person / Entity Type"
    _order = "country_code, sequence, code"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(
        required=True,
        help="Stable technical code, e.g. SK-FO / SK-PO / CZ-FO.",
    )
    country_code = fields.Selection(
        [("CZ", "Czech Republic"), ("SK", "Slovakia")],
        string="Country",
        required=True,
        index=True,
    )
    is_legal_entity = fields.Boolean(
        help="True for a legal entity, False for a natural person.",
    )
    sequence = fields.Integer(default=10)
    description = fields.Text(translate=True)
    active = fields.Boolean(default=True)

    # 19.0 declares this as models.Constraint; 18.0 has only _sql_constraints.
    _sql_constraints = [
        ("uniq_code_per_country", "UNIQUE(country_code, code)",
         "The person-type code must be unique per country."),
    ]
