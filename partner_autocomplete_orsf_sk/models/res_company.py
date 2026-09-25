# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    """Per-company behaviour of the ORSF SK provider.

    These three live on res.company rather than in ir.config_parameter for two
    reasons. The provider itself is chosen per company (``partner_autocomplete_
    dispatcher`` puts ``partner_autocomplete_provider`` here), so its options
    belong at the same scope. And a ``config_parameter`` Boolean that defaults
    to True cannot be switched off at all: ``ir.config_parameter.set_param``
    *unlinks* the row for a falsy value, and ``res.config.settings`` then reads
    the absent key back through the field default — so the box ticks itself
    again on the next reload.
    """

    _inherit = "res.company"

    orsf_sk_set_company_registry = fields.Boolean(
        "ORSF: fill Company ID",
        default=True,
        help="Write the IČO into the standard Company ID field "
        "(company_registry) as well as into any mapped field.",
    )
    orsf_sk_set_company_type = fields.Boolean(
        "ORSF: set company type",
        default=True,
        help="Set the contact to Individual for a sole trader (živnostník) "
        "and to Company for everything else, following the register.",
    )
    orsf_sk_format_psc = fields.Boolean(
        "ORSF: format PSČ as 851 01",
        default=True,
        help="ORSF returns the postal code as five digits; Slovak documents "
        "write it grouped 3+2.",
    )
