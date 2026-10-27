# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models

# Tax-reliability ratings, normalised across countries.
CSSK_RELIABILITY = [
    ("highly_reliable", "Highly reliable"),
    ("reliable", "Reliable"),
    ("less_reliable", "Less reliable"),
    ("unreliable", "Unreliable"),
    # The register answered, and the subject is not a VAT payer: the payer
    # liability rules (§ 69 ods. 13 SK / § 109 CZ) do not apply to it.
    ("not_vat_payer", "Not a VAT payer"),
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

    def _cssk_paid_account_key(self, bank_account):
        """``bank_account`` in the form the register publishes accounts in.

        The base compares sanitised account numbers, which for an IBAN is the
        IBAN. A country provider whose register publishes accounts in another
        form, or whose users type them in another form, overrides this.
        """
        return bank_account.sanitized_acc_number

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

        if reliability == "not_vat_payer":
            # Only a VAT payer must publish its accounts, and the liability
            # for its unpaid VAT is what this check is about.
            vals["cssk_bank_acc_status"] = "not_vat_payer"
            vals["cssk_registered_accounts"] = False
        elif accounts is None:
            vals["cssk_bank_acc_status"] = "unknown"
            vals["cssk_registered_accounts"] = False
        else:
            vals["cssk_registered_accounts"] = ", ".join(accounts) or False
            paid = self._cssk_paid_account_key(bank_account)
            if not paid:
                vals["cssk_bank_acc_status"] = "no_account"
            elif paid in accounts:
                vals["cssk_bank_acc_status"] = "registered"
            elif not accounts:
                # A VAT payer that published no account at all. The liability
                # test is still met — every account is "another account than
                # the published one" — but saying "this account is not among
                # them" sent people comparing numbers that were never there.
                # (A supplier the register does not hold as a VAT payer comes
                # back as "not_vat_payer" and is handled above.)
                vals["cssk_bank_acc_status"] = "not_registered"
                warnings.append(
                    _(
                        "The supplier has published no bank account with the "
                        "tax authority, so the account %s cannot be a "
                        "published one. Paying it can make you liable for the "
                        "supplier's unpaid VAT (§ 69 ods. 13 písm. c) SK / "
                        "§ 109 CZ); you may instead remit the VAT directly to "
                        "the tax office."
                    )
                    % paid
                )
            else:
                vals["cssk_bank_acc_status"] = "not_registered"
                warnings.append(
                    _(
                        "The bank account %s is NOT among the accounts the "
                        "supplier registered with the tax authority. Paying an "
                        "unregistered account can make you liable for the "
                        "supplier's unpaid VAT (§ 69 ods. 13 písm. c) SK / "
                        "§ 109 CZ); you may instead remit the VAT directly to "
                        "the tax office."
                    )
                    % paid
                )

        if reliability is not None:
            vals["cssk_supplier_reliability"] = reliability
            # Keep the contact's own rating current as well: the bill or
            # payment snapshot was the only place it ever reached, and the
            # field on the contact stayed empty for good.
            self.sudo().write({
                "cssk_tax_reliability": reliability,
                "cssk_reliability_checked_on": vals["cssk_reliability_checked_on"],
            })
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
        """Ask the register for the rating of each selected contact's company.

        Written on the commercial partner, the one the bill check reads; a
        contact person under it shows the company's rating.
        """
        checked = unavailable = 0
        for commercial in self.commercial_partner_id:
            rel = commercial._cssk_get_tax_reliability()
            if rel is None:
                unavailable += 1
                continue
            commercial.write({
                "cssk_tax_reliability": rel,
                "cssk_reliability_checked_on": fields.Datetime.now(),
            })
            checked += 1
        self.env.user._bus_send("simple_notification", {
            "type": "success" if checked and not unavailable else "warning",
            "title": _("Tax reliability"),
            "message": _(
                "%(checked)s checked, %(unavailable)s with no answer (no "
                "register for the country, no identifier, or the register "
                "did not answer).",
                checked=checked, unavailable=unavailable,
            ),
        })
        return True
