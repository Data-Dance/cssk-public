# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import binascii
import lzma
from datetime import date, datetime
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
    """Generate pay-by-square code that can by used to create QR code for
    banking apps
    When date is not provided current date will be used.
    """

    if date_due is None:
        date_due = datetime.now()

    # 1) create the basic data structure
    """ See https://www.sbaonline.sk/wp-content/uploads/2020/03/pay-by-square-specifications-1_1_0.pdf
        Table 15 - PAY by square sequence data model
    """
    data = "\t".join(
        [
            "",  # InvoiceID
            "1",  # Payments (count)
            "1",  # PaymentOptions = simple payment
            f"{amount:.2f}",  # Amount
            currency,  # CurrencyCode
            date_due.strftime("%Y%m%d"),  # PaymentDueDate
            variable_symbol,  # VariableSymbol
            constant_symbol,  # ConstantSymbol
            specific_symbol,  # SpecificSymbol
            originator_ref,  # OriginatorsReferenceInformation - only if 3 above were not used
            note,  # PaymentNote
            "1",  # BankAccounts (count)
            iban,  # IBAN
            swift,  # BIC
            "0",  # StandingOrderExt = not recurring
            "0",  # DirectDebitExt = not 'inkaso'
            beneficiary_name,  # BeneficiaryName
            beneficiary_address_1,  # BeneficiaryAddressLine1
            beneficiary_address_2,  # BeneficiaryAddressLine2
        ]
    )

    # 2) Add a crc32 checksum
    checksum = binascii.crc32(data.encode()).to_bytes(4, "little")
    total = checksum + data.encode()

    # 3) Run through XZ
    compressed = lzma.compress(
        total,
        format=lzma.FORMAT_RAW,
        filters=[
            {
                "id": lzma.FILTER_LZMA1,
                "lc": 3,
                "lp": 0,
                "pb": 2,
                "dict_size": 128 * 1024,
            }
        ],
    )

    # 4) prepend length and convert to hex
    compressed_with_length = b"\x00\x00" + len(total).to_bytes(2, "little") + compressed

    # 5) Convert to padded binary string
    binary = "".join(
        [bin(single_byte)[2:].zfill(8) for single_byte in compressed_with_length]
    )

    # 6) Pad with zeros on the right up to a multiple of 5
    length = len(binary)
    remainder = length % 5
    if remainder:
        binary += "0" * (5 - remainder)
        length += 5 - remainder

    # 7) Substitute each quintet of bits with corresponding character
    subst = "0123456789ABCDEFGHIJKLMNOPQRSTUV"
    return "".join(
        [subst[int(binary[5 * i : 5 * i + 5], 2)] for i in range(length // 5)]
    )


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
        if qr_method == "skpaybysquare_qr":
            # VS/KS/SS provided by the invoice via context (see
            # l10n_cssk_payment_symbols). Per the PAY by square spec the
            # OriginatorsReferenceInformation is used only when the symbols
            # are not — so it is blanked when any symbol is present.
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
                    originator_ref=(
                        ""
                        if symbols
                        else free_communication or structured_communication or ""
                    ),
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
        if qr_method == "skpaybysquare_qr":
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
        if qr_method == "skpaybysquare_qr":
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
        rslt.append(("skpaybysquare_qr", _("PAY by square (Slovakia)"), 20))
        return rslt

    def _get_qr_code_frame_generation_params(self, qr_method):
        if qr_method == "skpaybysquare_qr":
            frame_path = file_path(
                "account_qr_code_pay_by_square_sk/static/src/img/pay-bottom-dark.png",
            )
            return {
                "frame_size": (210, 240),
                "box_size": 4,
                "border": 1,
                "frame": Image.open(frame_path),
                "x_y": (17, 17),
                "resize_values": (175, 175),
            }
        return super()._get_qr_code_frame_generation_params(qr_method)
