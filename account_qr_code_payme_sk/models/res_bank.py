# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from urllib.parse import urlencode
from datetime import date
from typing import Optional

from odoo import _, api, models
from odoo.tools.misc import file_path
from PIL import Image


def generate(
    amount: float,
    iban: str,
    swift: str = "",
    date_due: Optional[date] = None,
    beneficiary_name: str = "",
    currency: str = "EUR",
    variable_symbol: str = "",
    constant_symbol: str = "",
    specific_symbol: str = "",
    originator_ref: str = "",
    note: str = "",
    beneficiary_address_1: str = "",
    beneficiary_address_2: str = "",
):
    """Generate payme code that can by used to create QR code for
        banking apps
        See https://www.sbaonline.sk/wp-content/uploads/2020/06/Payment_Link_standard_2_0.pdf
    """

    # Payment identification: with symbols the standard's structured form
    # "/VS…/SS…/KS…" (section 3.4), otherwise the free reference.
    if variable_symbol or constant_symbol or specific_symbol:
        payment_identification = (
            f"/VS{variable_symbol}/SS{specific_symbol}/KS{constant_symbol}"
        )
    else:
        payment_identification = originator_ref

    # See 3.4 Attributes specification in Query component
    params = {
        "IBAN": iban, # IBAN
        "AM": f"{amount:.2f}", # Amount
        "CC": "EUR", # Currency Code
        "PI": payment_identification[:35], # Payment identification
        "CN": beneficiary_name[:70], # Creditor's name
    }
    if note:
        params["MSG"] = note # Message


    # See 3.3 Path specification
    url = f"https://payme.sk/2/{'p' if originator_ref.startswith('QR-') else 'e'}/PME?{urlencode(params)}"

    return url

class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    # see account_move.generate_qr_code
    def _get_qr_code_generation_params(
        self,
        qr_method,
        amount,
        currency,
        debtor_partner,
        free_communication,
        structured_communication,
    ):
        if qr_method == "skpayme_qr":
            # VS/KS/SS provided by the invoice via context (see
            # l10n_cssk_payment_symbols).
            symbols = self.env.context.get("cssk_payment_symbols") or {}
            return {
                "barcode_type": "QR",
                "width": 128,
                "height": 128,
                "humanreadable": 0,
                "value": generate(
                    amount=amount,
                    iban=self.sanitized_acc_number,
                    swift=self.bank_bic or "",
                    # date_due: Optional[date] = None,
                    beneficiary_name=(self.acc_holder_name or self.partner_id.name),
                    currency=currency.name,
                    variable_symbol=symbols.get("variable_symbol", ""),
                    constant_symbol=symbols.get("constant_symbol", ""),
                    specific_symbol=symbols.get("specific_symbol", ""),
                    originator_ref=free_communication or structured_communication or "",
                    note=structured_communication or free_communication or "",
                    # beneficiary_address_1: str = '',
                    # beneficiary_address_2: str = '',
                ),
            }
        return super()._get_qr_code_generation_params(
            qr_method,
            amount,
            currency,
            debtor_partner,
            free_communication,
            structured_communication,
        )

    def _get_error_messages_for_qr(self, qr_method, debtor_partner, currency):
        if qr_method == "skpayme_qr":
            # Some countries share the same IBAN country code
            # (e.g. Åland Islands and Finland IBANs are 'FI', but Åland Islands' code is 'AX').
            sepa_country_codes = self.env.ref("base.sepa_zone").country_ids.mapped(
                "code"
            )
            non_iban_codes = {
                "AX",
                "NC",
                "YT",
                "TF",
                "BL",
                "RE",
                "MF",
                "GP",
                "PM",
                "PF",
                "GF",
                "MQ",
                "JE",
                "GG",
                "IM",
            }
            sepa_iban_codes = {
                code for code in sepa_country_codes if code not in non_iban_codes
            }
            eligible = (
                currency.name == "EUR"
                and self.acc_type == "iban"
                and self.sanitized_acc_number[:2] in sepa_iban_codes
            )
            return (
                None
                if eligible
                else _(
                    "The account is not eligible for PAY by square QR code. Please check the account type, number, and currency."
                )
            )

        return super()._get_error_messages_for_qr(qr_method, debtor_partner, currency)

    def _check_for_qr_code_errors(
        self,
        qr_method,
        amount,
        currency,
        debtor_partner,
        free_communication,
        structured_communication,
    ):
        if qr_method == "skpayme_qr":
            if not self.acc_holder_name and not self.partner_id.name:
                return _(
                    "The account receiving the payment must have an account holder name or partner name set."
                )

        return super()._check_for_qr_code_errors(
            qr_method,
            amount,
            currency,
            debtor_partner,
            free_communication,
            structured_communication,
        )

    @api.model
    def _get_available_qr_methods(self):
        rslt = super()._get_available_qr_methods()
        rslt.append(("skpayme_qr", _("payme (Slovakia)"), 20))
        return rslt

    def _get_qr_code_frame_generation_params(self, qr_method):
        if qr_method == "skpayme_qr":
            frame_path = file_path(
                "account_qr_code_payme_sk/static/src/img/payme.png",
            )
            return {
                "frame_size": (320, 354),
                "box_size": 1,
                "border": 1,
                "frame": Image.open(frame_path),
                "x_y": (25, 25),
                "resize_values": (270, 270),
            }
        return super()._get_qr_code_frame_generation_params(qr_method)
