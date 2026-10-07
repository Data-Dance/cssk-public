# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json
import logging

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_cssk_receipt_capture.tools.amounts import flatten_label

from ..tools.ekasa import (
    BROWSER_HEADERS, ENDPOINT, EkasaQrError, map_receipt, parse_qr,
)

_logger = logging.getLogger(__name__)


class CSSKReceiptProviderSkEkasa(models.AbstractModel):
    """Fetches a registered receipt from Finančná správa.

    The service is reached over plain HTTPS with no authentication; what makes
    a company entitled to use it is the notification under § 18 ods. 11, not a
    credential, which is why the gate is a declaration rather than a key.
    """

    _name = "cssk.receipt.provider.sk_ekasa"
    _inherit = "cssk.receipt.provider.mixin"
    _description = "Slovak eKasa Receipt Lookup"

    @api.model
    def _can_capture(self, receipt):
        """Only a receipt whose QR payload the service can be asked about."""
        if not receipt.qr_raw:
            return False
        try:
            parse_qr(receipt.qr_raw)
        except EkasaQrError:
            return False
        return True

    @api.model
    def _capture(self, receipt):
        company = receipt.company_id
        company._l10n_sk_ekasa_check_ready()
        try:
            request = parse_qr(receipt.qr_raw)
        except EkasaQrError as err:
            raise UserError(str(err)) from err

        self.env["sk.ekasa.call"]._check_budget(company)
        payload, call_vals = self._fetch(company, request)
        call_vals.update({
            "company_id": company.id,
            "receipt_id": receipt.id,
            "request_key": self._request_key(request),
        })
        self.env["sk.ekasa.call"].create(call_vals)

        if call_vals["outcome"] != "found":
            raise UserError(call_vals["message"])

        mapped = map_receipt(payload, flatten=flatten_label)
        if not mapped:
            raise UserError(_(
                "The service answered but returned no receipt body. Nothing "
                "was changed."))
        if mapped.get("warning"):
            receipt.message_post(body=mapped["warning"])

        vals = {
            "receipt_uid": mapped["receipt_uid"],
            "issue_date": mapped["issue_date"],
            "amount_total": mapped["amount_total"],
            "seller_name": mapped["seller_name"],
            "seller_vat": mapped["seller_vat"],
            "seller_tax_id": mapped["seller_tax_id"],
            "seller_reg_id": mapped["seller_reg_id"],
            "seller_vat_payer": mapped["seller_vat_payer"],
            "premises_note": mapped["premises_note"],
            "l10n_sk_ekasa_okp": mapped["okp"],
            "l10n_sk_ekasa_is_paragon": mapped["is_paragon"],
            "payload_raw": receipt._store_payload(payload),
            "line_ids": [fields.Command.create(line) for line in mapped["lines"]],
            "tax_summary_ids": [
                fields.Command.create(tax) for tax in mapped["taxes"]],
        }
        # An off-line receipt is printed without an identifier, so the QR is the
        # only key we had; the service hands back the real one once the till has
        # caught up. Keep theirs: it is what a second capture would collide on.
        if not vals["receipt_uid"]:
            vals.pop("receipt_uid")
        return vals

    # ------------------------------------------------------------------
    @api.model
    def _request_key(self, request):
        if "receiptId" in request:
            return request["receiptId"]
        return "%s:%s:%s:%s:%s" % (
            request["okp"], request["cashRegisterCode"],
            request["issueDateFormatted"], request["receiptNumber"],
            request["totalAmount"])

    @api.model
    def _fetch(self, company, request):
        """POST the request and classify the answer.

        Returns ``(payload, call_vals)``; ``call_vals`` is always recorded, so a
        refused or failed lookup still counts against the budget and still
        leaves a trace.
        """
        timeout = company.l10n_sk_ekasa_timeout or 30
        try:
            response = requests.post(
                ENDPOINT, data=json.dumps(request).encode(),
                headers=BROWSER_HEADERS, timeout=timeout)
        except requests.RequestException as err:
            _logger.warning("eKasa lookup failed: %s", err)
            return None, {
                "outcome": "transport",
                "message": _(
                    "Could not reach Finančná správa's verification service "
                    "(%s). The receipt was left untouched; try again.", err),
            }

        status = response.status_code
        if status != 200:
            # The service's firewall answers a request it does not like with
            # 499 and an HTML page rather than JSON.
            return None, {
                "outcome": "refused",
                "http_status": status,
                "message": _(
                    "The verification service refused the request (HTTP "
                    "%(status)s). This is usually the service's firewall "
                    "rather than the receipt.", status=status),
            }
        try:
            payload = response.json()
        except ValueError:
            return None, {
                "outcome": "refused",
                "http_status": status,
                "message": _(
                    "The verification service answered with something that is "
                    "not JSON."),
            }

        return_value = payload.get("returnValue")
        if return_value not in (0, None):
            return payload, {
                "outcome": "refused",
                "http_status": status,
                "return_value": return_value,
                "message": _(
                    "The verification service returned code %s.", return_value),
            }
        if not payload.get("receipt"):
            # A receipt that is not in the system comes back as HTTP 200 with a
            # null body, never as an error, so this must be tested for
            # explicitly or a miss reads as a success with empty values.
            return payload, {
                "outcome": "not_found",
                "http_status": status,
                "return_value": return_value or 0,
                "message": _(
                    "Finančná správa holds no receipt for this code. Either "
                    "the seller never registered it — which is worth "
                    "reporting — or the code was misread."),
            }
        return payload, {
            "outcome": "found",
            "http_status": status,
            "return_value": return_value or 0,
        }
