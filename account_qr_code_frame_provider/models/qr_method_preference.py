# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    def _get_qr_method_home_country(self):
        """Map a national QR method to the country whose scheme it is.

        Extended by each national module. A method absent from the map has no
        home and is never held back.
        """
        return {}

    def _qr_method_suits(self, qr_method, debtor_partner):
        """Whether the AUTOMATIC choice may pick ``qr_method``.

        Technical eligibility (``_get_error_messages_for_qr``) says only whether
        a code can be built. PAY by square, payme and core's SEPA QR all sit at
        sequence 20 and all accept any EUR SEPA IBAN, so without this the winner
        fell to module load order: a Czech company's EUR invoice to a German
        customer could print a Slovak PAY by square code.

        A national method is preferred only when the issuer (the account
        holder) and the debtor are both in its country; an unknown country
        does not count against it. This is the single place to change if the
        policy should key on the issuer alone.

        An explicit per-invoice ``qr_code_method`` does not pass through here,
        so a user who deliberately picks a national code still gets it.
        """
        home = self._get_qr_method_home_country().get(qr_method)
        if not home:
            return True
        issuer = self.partner_id.commercial_partner_id.country_code
        debtor = (debtor_partner.commercial_partner_id.country_code
                  if debtor_partner else False)
        return issuer in (home, False) and debtor in (home, False)

    def _build_qr_code_vals(
        self,
        amount,
        free_communication,
        structured_communication,
        currency,
        debtor_partner,
        qr_method=None,
        silent_errors=True,
    ):
        if qr_method or not self:
            return super()._build_qr_code_vals(
                amount, free_communication, structured_communication, currency,
                debtor_partner, qr_method, silent_errors)
        for candidate, _name in self.get_available_qr_methods_in_sequence():
            if not self._qr_method_suits(candidate, debtor_partner):
                continue
            vals = super()._build_qr_code_vals(
                amount, free_communication, structured_communication, currency,
                debtor_partner, candidate, silent_errors=True)
            if vals:
                return vals
        # Nothing preferred could be built: fall back to core's own choice,
        # which also raises the errors when the caller asked for them.
        return super()._build_qr_code_vals(
            amount, free_communication, structured_communication, currency,
            debtor_partner, None, silent_errors)


class AccountMove(models.Model):
    _inherit = "account.move"

    def _generate_qr_code(self, silent_errors=False):
        """Pre-select the preferred method so core's first-eligible loop is
        not the one deciding. See ``res.partner.bank._qr_method_suits``."""
        if self.display_qr_code and not self.qr_code_method and self.partner_bank_id:
            bank = self.partner_bank_id
            for candidate, _name in bank.get_available_qr_methods_in_sequence():
                if bank._get_error_messages_for_qr(
                    candidate, self.partner_id, self.currency_id
                ):
                    continue
                if bank._qr_method_suits(candidate, self.partner_id):
                    self.qr_code_method = candidate
                    break
        return super()._generate_qr_code(silent_errors=silent_errors)
