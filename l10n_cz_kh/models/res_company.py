# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

#: l10n_cz domestic § 92a reverse-charge (přenesení daňové povinnosti)
#: purchase taxes. Received § 92a supplies then land in oddíl B.1 (and
#: supplied in A.1) instead of falling through to the standard B.2 / A.4.
#: EU acquisitions are unaffected — the resolver checks intra-EU before the
#: reverse-charge flag.
CZ_REVERSE_CHARGE_TEMPLATES = (
    "l10n_cz_21_tax_reverse_charge_scheme",
    "l10n_cz_12_tax_reverse_charge_scheme",
)


class ResCompany(models.Model):
    _inherit = "res.company"

    def _cssk_reverse_charge_tax_templates(self):
        self.ensure_one()
        if self.chart_template == "cz":
            return CZ_REVERSE_CHARGE_TEMPLATES
        return super()._cssk_reverse_charge_tax_templates()
