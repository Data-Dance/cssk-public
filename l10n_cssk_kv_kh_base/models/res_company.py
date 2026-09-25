# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    """Flag the chart's reverse-charge taxes so self-assessment is recognised.

    The control statement decides between its sections on
    ``cssk_control_is_reverse_charge``. A company whose taxes are unflagged
    therefore reports **no B.1 rows at all**: every § 69 service received and
    every intra-EU acquisition falls through to the ordinary received-invoice
    section or out of the statement entirely. Nothing errors, the statement
    computes, validates and files — and it is wrong.

    Country modules supply the template list; this holds the mechanism, which
    is identical for both.
    """

    _inherit = "res.company"

    def _cssk_reverse_charge_tax_templates(self):
        """Chart-template xmlid suffixes of the self-assessment taxes.

        Empty here. Country modules override and return their own.
        """
        self.ensure_one()
        return ()

    def _cssk_flag_reverse_charge_taxes(self):
        """Set the flag on this company's self-assessment taxes. Idempotent."""
        flagged = 0
        for company in self:
            for template in company._cssk_reverse_charge_tax_templates():
                tax = self.env.ref(
                    "account.%s_%s" % (company.id, template),
                    raise_if_not_found=False,
                )
                if not tax:
                    continue
                if not tax.cssk_control_is_reverse_charge:
                    tax.cssk_control_is_reverse_charge = True
                    flagged += 1
                    _logger.info(
                        "reverse-charge tax flagged: %s (%s)",
                        tax.name, company.display_name,
                    )
                flagged += self._cssk_flag_historic_clones(tax)
        return flagged

    def _cssk_flag_historic_clones(self, tax):
        """Carry the flag onto historical-rate copies of a flagged tax.

        A historical rate is cloned from a current one, so it inherits the flag
        — but only if the source carried it **at the moment of cloning**. Where
        the rates were generated before the flag existed, the copies are
        unflagged, and an unflagged historical reverse charge is precisely the
        silent B.1 omission this method exists to prevent, for exactly the
        years a history import is about.

        Guarded on the field rather than declared as a dependency: the
        historical-rate module sits in the VAT-return family, and the control
        statement should not require it to be installed.
        """
        Tax = self.env["account.tax"]
        if "cssk_historic_source_tax_id" not in Tax._fields:
            return 0
        clones = Tax.with_context(active_test=False).search([
            ("cssk_historic_source_tax_id", "=", tax.id),
            ("cssk_control_is_reverse_charge", "=", False),
        ])
        if not clones:
            return 0
        clones.cssk_control_is_reverse_charge = True
        _logger.info(
            "reverse-charge flag carried onto %s historical rate(s) of %s",
            len(clones), tax.name,
        )
        return len(clones)
