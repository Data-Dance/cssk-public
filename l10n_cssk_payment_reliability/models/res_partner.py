# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models

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

    def _cssk_get_vat_deregistration(self):
        """Whether the tax authority lists this VAT payer as having grounds
        for cancelling its registration.

        Returns ``None`` when unavailable (no provider, register down),
        ``False`` when not listed, or a short description of the listing.
        ``None`` and ``False`` must stay apart: a register that did not answer
        is not a clean record.
        """
        self.ensure_one()
        return None

    def _cssk_reliability_verdict(self, bank_account):
        """What the registers say about paying ``bank_account`` of this
        supplier: ``(vals, warnings)``.

        ``vals`` holds the snapshot fields shared by vendor bills and
        payments; ``warnings`` the human-readable risks. Shared so the bill
        check, the payment check and the scheduled re-check cannot drift.
        """
        self.ensure_one()
        # One provider query per check (CZ ADIS answers both in one response).
        accounts, reliability = self._cssk_get_reliability_data()

        vals = {"cssk_reliability_checked_on": fields.Datetime.now()}
        warnings = []

        if accounts is None:
            vals["cssk_bank_acc_status"] = "unknown"
            vals["cssk_registered_accounts"] = False
        else:
            vals["cssk_registered_accounts"] = ", ".join(accounts) or False
            paid = bank_account.sanitized_acc_number
            if not paid:
                vals["cssk_bank_acc_status"] = "no_account"
            elif paid in accounts:
                vals["cssk_bank_acc_status"] = "registered"
            else:
                vals["cssk_bank_acc_status"] = "not_registered"
                warnings.append(
                    _(
                        "The bank account %s is NOT among the accounts the "
                        "supplier registered with the tax authority. Paying an "
                        "unregistered account can make you liable for the "
                        "supplier's unpaid VAT (§69 ods. 14 SK / §109 CZ); you "
                        "may instead remit the VAT directly to the tax office."
                    )
                    % paid
                )

        if reliability is not None:
            vals["cssk_supplier_reliability"] = reliability
            if reliability in ("less_reliable", "unreliable"):
                label = dict(CSSK_RELIABILITY).get(reliability, reliability)
                warnings.append(
                    _("The supplier's tax-reliability rating is '%s'.") % label
                )

        deregistration = self._cssk_get_vat_deregistration()
        if deregistration is not None:
            vals["cssk_vat_deregistration"] = deregistration or False
            if deregistration:
                warnings.append(
                    _(
                        "The supplier is on the tax authority's list of VAT "
                        "payers with grounds for cancelling their registration "
                        "(%s)."
                    )
                    % deregistration
                )
        return vals, warnings

    def action_cssk_refresh_reliability(self):
        for partner in self:
            rel = partner.commercial_partner_id._cssk_get_tax_reliability()
            if rel is not None:
                partner.cssk_tax_reliability = rel
                partner.cssk_reliability_checked_on = fields.Datetime.now()
        return True
