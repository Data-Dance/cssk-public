###################################################################################
#
#    Copyright (c) 2022 Data Dance s.r.o.
#
#    Data Dance Proprietary License v1.0
#
#    This software and associated files (the "Software") may only be used
#    (executed, modified, executed after modifications) if you have
#    purchased a valid license from Data Dance s.r.o.
#
#    The above permissions are granted for a single database per purchased
#    license. Furthermore, with a valid license it is permitted to use the
#    software on other databases as long as the usage is limited to a testing
#    or development environment.
#
#    You may develop modules based on the Software or that use the Software
#    as a library (typically by depending on it, importing it and using its
#    resources), but without copying any source code or material from the
#    Software. You may distribute those modules under the license of your
#    choice, provided that this license is compatible with the terms of the
#    Data Dance Proprietary License (For example: LGPL, MIT, or proprietary
#    licenses similar to this one).
#
#    It is forbidden to publish, distribute, sublicense, or sell copies of
#    the Software or modified copies of the Software.
#
#    The above copyright notice and this permission notice must be included
#    in all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###################################################################################


import re

from odoo import _, api, models
from odoo.tools.misc import file_path
from PIL import Image

# https://cbaonline.cz/upload/1645-standard-qr-v1-2-cerven-2021.pdf
# SPD*1.0*ACC:CZ8120100000002701987951*AM:1000*CC:EUR*DT:20221010*MSG:Message*X-KS:6666*X-VS:1234567890*X-SS:0987654321
# SPD*1.0*ACC:CZ8120100000002701987951*AM:2418.79*CC:CZK*MSG:210054*RF:210054*DT:20211230*X-VS:210054


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    def _get_qr_vals(
        self,
        qr_method,
        amount,
        currency,
        debtor_partner,
        free_communication,
        structured_communication,
    ):
        if qr_method == "czqrplatba_qr":
            # ``free_communication`` comes from ``payment_reference or name`` upstream
            # and is False when neither is set (e.g. a draft invoice whose number is
            # not assigned yet). Coerce to an empty string so the slicing and regex
            # below do not raise ``'bool' object is not subscriptable``.
            free_communication = free_communication or ""
            # VS/KS/SS provided by the invoice via context (see
            # l10n_cssk_payment_symbols); without it only the RF/MSG
            # digits-of-communication fallback below applies.
            symbols = self.env.context.get("cssk_payment_symbols") or {}
            variable_symbol = symbols.get("variable_symbol") or ""
            qr_code_vals = [
                "SPD",  # Header
                "1.0",  # Version
                "ACC:"
                + self.sanitized_acc_number,  # ..[46] ACC:<Account Number of the Beneficiary>
                # "ALT-ACC" + ..[93] <Alternative Account Numbers of the Beneficiary> ALTACC:CZ5855000000001265098001+RZBCCZPP,CZ5855000000001265098001*
                "AM:" + f"{amount:.2f}",  # ..[10] AM:<Amount of the Transfer>
                "CC:" + currency.name,  # CC:<Currency>
                "MSG:" + free_communication[:60],  # ..[60], # MSG:<VS> - check for "*"
                "RF:"
                + (variable_symbol or re.sub("\\D", "", free_communication))[
                    :16
                ],  # ..[16], # RF:<VS> - only \d*
                # TODO
                # "DT:" + .., # DT:<Date Due>
                "RN:"
                + (self.acc_holder_name or self.partner_id.name)[
                    :71
                ],  # ..[71], # RN:<Receiver Name>
                # "NT:" + ..[1], # NT:<Notification Channel> "P"=phone "E"=email
                # "NTA:" + ..[320], # NTA:<Notification Channel> for NT:P number[:12], for NT:E e-mailAddress[:64]@domainName[:255]
                # "X-ID:" + ..[20], # X-ID:<ID>
                # "X-URL": + ..[140], # X-URL:<URL>
            ]
            if variable_symbol:
                qr_code_vals.append("X-VS:" + variable_symbol[:10])
            if symbols.get("specific_symbol"):
                qr_code_vals.append("X-SS:" + symbols["specific_symbol"][:10])
            if symbols.get("constant_symbol"):
                qr_code_vals.append("X-KS:" + symbols["constant_symbol"][:10])
            return qr_code_vals
        return super()._get_qr_vals(
            qr_method,
            amount,
            currency,
            debtor_partner,
            free_communication,
            structured_communication,
        )

    def _get_qr_code_generation_params(
        self,
        qr_method,
        amount,
        currency,
        debtor_partner,
        free_communication,
        structured_communication,
    ):
        if qr_method == "czqrplatba_qr":
            return {
                "barcode_type": "QR",
                "width": 128,
                "height": 128,
                "humanreadable": 0,
                "value": "*".join(
                    self._get_qr_vals(
                        qr_method,
                        amount,
                        currency,
                        debtor_partner,
                        free_communication,
                        structured_communication,
                    )
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
        if qr_method == "czqrplatba_qr":
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
                (currency.name == "CZK" or debtor_partner.country_code == "CZ")
                and self.acc_type == "iban"
                and self.sanitized_acc_number[:2] in sepa_iban_codes
            )
            return (
                None
                if eligible
                else _(
                    "The account is not eligible for QR Platba. Please check the account type, number, and currency."
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
        if qr_method == "czqrplatba_qr":
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
        rslt.append(("czqrplatba_qr", _("QR Platba (Czech Republic)"), 20))
        return rslt

    def _get_qr_code_frame_generation_params(self, qr_method):
        if qr_method == "czqrplatba_qr":
            frame_path = file_path(
                "account_qr_code_qr_platba_cz/static/src/img/qr_cz_qrcode.png",
            )
            return {
                "frame_size": (200, 200),
                "box_size": 5,
                "border": 0,
                "frame": Image.open(frame_path),
                "x_y": (22, 14),
                "resize_values": (155, 155),
            }
        return super()._get_qr_code_frame_generation_params(qr_method)
