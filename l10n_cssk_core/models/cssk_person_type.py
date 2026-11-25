from odoo import api, fields, models


class CSSKPersonType(models.Model):
    """Person / entity type catalogue (fyzická osoba, právnická osoba, …).

    Used by statutory reports that classify the counterparty (e.g. control
    statement section selection, financial-statement entity-size variants).
    Seeded here, one natural-person / legal-entity pair per country.
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

    _uniq_code_per_country = models.Constraint(
        "UNIQUE(country_code, code)",
        "The person-type code must be unique per country.",
    )

    @api.model
    def _cssk_for_subject(self, country_code, natural_person):
        """The type of a natural person, or of a legal entity, in a country.

        For a caller that knows the fact but not the catalogue: a register
        lookup learns "this IČO is a person in business", and what it has to
        write on the partner is one of these records. Empty outside CZ/SK or
        where the type was archived, and the caller then writes nothing.
        """
        return self.search(
            [
                ("country_code", "=", (country_code or "").upper()),
                ("is_legal_entity", "=", not natural_person),
            ],
            limit=1,
        )
