# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

# Tax-reliability ratings, normalised across countries.
CSSK_RELIABILITY = [
    ("highly_reliable", "Highly reliable"),
    ("reliable", "Reliable"),
    ("less_reliable", "Less reliable"),
    ("unreliable", "Unreliable"),
    ("unknown", "Unknown / not checked"),
]


class ResPartner(models.Model):
    _inherit = "res.partner"

    cssk_tax_reliability = fields.Selection(
        CSSK_RELIABILITY,
        string="Tax Reliability",
        copy=False,
        help="Supplier's tax-reliability rating from the tax authority "
        "register, as of the last check.",
    )
    cssk_reliability_checked_on = fields.Datetime(
        string="Reliability Checked On", copy=False
    )

    # ------------------------------------------------------------------
    # Provider hooks — overridden by the country modules. The base has no
    # data source, so it reports "nothing available".
    # ------------------------------------------------------------------
    def _cssk_get_registered_accounts(self):
        """Sanitised IBANs the supplier registered with the tax authority.

        Returns a ``list`` of sanitised account numbers, or ``None`` when no
        provider is installed / the register is unreachable.
        """
        self.ensure_one()
        return None

    def _cssk_get_tax_reliability(self):
        """One of ``CSSK_RELIABILITY`` keys, or ``None`` when unavailable."""
        self.ensure_one()
        return None

    def _cssk_get_reliability_data(self):
        """Both answers of one reliability check:
        ``(registered_accounts, reliability)``.

        Default implementation delegates to the two individual hooks.
        Providers whose register returns everything in a single response
        (e.g. CZ ADIS) override this to query once and derive both, so a
        bill check costs one roundtrip instead of two.
        """
        self.ensure_one()
        return (
            self._cssk_get_registered_accounts(),
            self._cssk_get_tax_reliability(),
        )

    def action_cssk_refresh_reliability(self):
        for partner in self:
            rel = partner.commercial_partner_id._cssk_get_tax_reliability()
            if rel is not None:
                partner.cssk_tax_reliability = rel
                partner.cssk_reliability_checked_on = fields.Datetime.now()
        return True
