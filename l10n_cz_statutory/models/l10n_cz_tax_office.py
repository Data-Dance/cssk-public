# Copyright 2026 Data Dance s.r.o.
# Data Dance Proprietary License v1.0 — see the LICENSE file.

# Backport of the ``l10n_cz.tax_office`` codelist that Odoo core added to the
# ``l10n_cz`` module in 19.0 (finanční úřady / územní pracoviště, keyed by
# c_pracufo → c_ufo). Odoo 18.0 core has no such model, so the CZ statutory
# reports (DPPO / DPHDP3 / KH c_pracufo) and the tax-authority seed hook have
# nothing to build on. Vendored here — the single CZ module every statutory
# and VAT family depends on — with the same name/fields so the 19.0 code
# carries unchanged.
from odoo import fields, models


class L10nCzTaxOffice(models.Model):
    _name = "l10n_cz.tax_office"
    _description = "Tax office in Czech Republic"
    _order = "workplace_code ASC"
    _rec_names_search = ["workplace_code", "name"]

    workplace_code = fields.Integer(
        string="Territorial Office", required=True, group_operator=False
    )
    code = fields.Integer(string="Code", required=True, group_operator=False)
    name = fields.Char(string="Name", translate=True)
    region = fields.Char(string="Region", required=True, translate=True)

    _sql_constraints = [
        (
            "workplace_code_unique",
            "UNIQUE (workplace_code)",
            "The territorial workplace code must be unique",
        ),
    ]
