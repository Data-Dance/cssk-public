import base64
import hashlib
import json
import logging
import time
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30
VRP2_APP_VERSION = "3.1.9"

VRP2_BASE_URL = "https://vcrp.financnasprava.sk/crp/api"
VRP2_BASE_URL_MRP = "https://mcrp.financnasprava.sk/crp/api"


def vrp2_round2(amount):
    """Round half up to 2 decimals, like the web app's ``zaokruhli2``."""
    return float(
        Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )


def vrp2_round4(amount):
    """Round half up to 4 decimals, like the web app's ``zaokruhli4``."""
    return float(
        Decimal(str(amount)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    )


def vrp2_round5(amount):
    """Round a CASH amount to 0.05 €, like the web app's ``zaokruhli5``.

    Faithful to app.js, including its edge case: a non-zero amount smaller
    than 5 cents rounds AWAY from zero to ±0.05 instead of to 0.
    """
    if not amount:
        return 0.0
    if 0 < amount < 0.05:
        return 0.05
    if -0.05 < amount < 0:
        return -0.05
    # Math.round(20 * e) / 20: JavaScript rounds a half towards +infinity,
    # so -0.025 goes to -0.00 where ROUND_HALF_UP would give -0.05.
    twentieths = (Decimal(str(amount)) * 20 + Decimal("0.5")).quantize(
        Decimal("1"), rounding=ROUND_FLOOR
    )
    return vrp2_round2(twentieths / 20)


def _compact_json(data):
    """Serialize ``data`` exactly like the VRP2 web client's ``JSON.stringify``.

    ``separators=(",", ":")`` drops all whitespace and ``ensure_ascii=False``
    keeps UTF-8 characters intact. The request body MUST be sent as these exact
    bytes, because ``crpChecksum`` is computed over them — any reserialization
    (e.g. requests' ``json=`` default, which inserts spaces) would break it.
    """
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


def _crp_checksum(body_str, token):
    """Compute the crpChecksum header value for an already-serialized body.

    Algorithm (deobfuscated from the VRP2 web client, verified byte-for-byte
    against captured traffic):
    1. Transform token: for each char take ``chr(ord(c) >> 4)``.
    2. SHA-256 of ``body_str + transformed_token`` (UTF-8).
    3. Base64 of the digest.

    ``body_str`` must be the compact JSON produced by :func:`_compact_json` and
    must be the exact string sent as the request body.
    """
    transformed = "".join(chr(ord(c) >> 4) for c in token)
    raw = (body_str + transformed).encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    return base64.b64encode(digest).decode("ascii")


class Vrp2Client(models.AbstractModel):
    _name = "vrp2.client"
    _description = "VRP2 REST API Client"

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def _login(self, holder):
        """Authenticate with VRP2 and store the session on holder.

        POST /v1/security/autentify/vrp -> full auth response dict.
        """
        # sudo: credentials/token are admin-only fields, but any user allowed
        # to trigger a fiscalization must be able to open the session.
        holder_sudo = holder.sudo()
        if not holder_sudo.vrp2_login or not holder_sudo.vrp2_password:
            raise UserError(
                _("VRP2 credentials are not configured on holder '%s'.")
                % holder.display_name
            )

        data = {
            "login": holder_sudo.vrp2_login.strip(),
            "password": holder_sudo.vrp2_password,
        }
        resp = self._request_raw(
            "POST",
            "/v1/security/autentify/vrp",
            json_data=data,
            token=None,
        )
        if resp.status_code != 200:
            body = resp.text[:500]
            _logger.warning("VRP2 login failed %s: %s", resp.status_code, body)
            error_desc = ""
            try:
                error_desc = resp.json().get("errorDescription", "")
            except Exception:
                pass
            raise UserError(
                _("VRP2 login failed: %s") % (error_desc or resp.reason)
            )

        auth = resp.json()
        token = auth.get("token")
        if not token:
            raise UserError(_("VRP2 login response missing token."))

        user_data = auth.get("user", {})
        roles = user_data.get("roles", [])
        role = "write" if "ROLE_02_05" in roles else "read"
        return_value = auth.get("returnValue", 0)

        holder.sudo().write({
            "vrp2_token": token,
            "vrp2_role": role,
            "vrp2_return_value": return_value,
            "vrp2_last_login": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

        _logger.info(
            "VRP2 login OK for holder %s, role=%s, returnValue=%s",
            holder.display_name,
            role,
            return_value,
        )
        return auth

    def _ensure_session(self, holder):
        """Ensure we have a valid VRP2 token. Login if needed."""
        if not holder.sudo().vrp2_token:
            self._login(holder)
        return holder.sudo().vrp2_token

    def _refresh_token(self, holder):
        """POST /v1/security/token/refresh to keep the session alive."""
        token = holder.sudo().vrp2_token
        if not token:
            return self._login(holder)

        try:
            self._request(
                holder, "POST", "/v1/security/token/refresh", json_data={}
            )
        except Exception:
            _logger.info("VRP2 token refresh failed, re-logging in.")
            return self._login(holder)

    def _logout(self, holder):
        """POST /v1/security/signout."""
        if not holder.sudo().vrp2_token:
            return
        try:
            self._request(
                holder, "POST", "/v1/security/signout", json_data={}
            )
        except Exception:
            _logger.debug("VRP2 logout error (ignored).", exc_info=True)
        holder.sudo().write({
            "vrp2_token": False,
            "vrp2_role": False,
        })

    # ------------------------------------------------------------------
    # High-level request helpers
    # ------------------------------------------------------------------

    def _request(
        self, holder, method, path, json_data=None, params=None, raw=False
    ):
        """Authenticated VRP2 API request. Re-logs in once on a 401."""
        token = self._ensure_session(holder)
        resp = self._request_raw(
            method, path, json_data=json_data, params=params, token=token
        )

        if resp.status_code == 401:
            _logger.info("VRP2 401 on %s %s — re-authenticating.", method, path)
            self._login(holder)
            token = holder.sudo().vrp2_token
            resp = self._request_raw(
                method, path, json_data=json_data, params=params, token=token
            )

        if resp.status_code >= 400:
            self._handle_error(resp, method, path)

        if raw:
            return resp
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    def _get(self, holder, path, params=None, raw=False):
        return self._request(holder, "GET", path, params=params, raw=raw)

    def _post(self, holder, path, json_data=None, raw=False):
        return self._request(
            holder, "POST", path, json_data=json_data, raw=raw
        )

    # ------------------------------------------------------------------
    # Low-level HTTP
    # ------------------------------------------------------------------

    def _request_raw(self, method, path, json_data=None, params=None, token=None):
        """Send a raw HTTP request to the VRP2 API. Returns requests.Response."""
        try:
            import requests
        except ImportError as exc:
            raise UserError(
                _("The 'requests' Python package is required for VRP2.")
            ) from exc
        import platform

        url = f"{VRP2_BASE_URL}{path}"
        headers = {
            "crpDate": str(int(time.time() * 1000)),
            "crpOs": f"vrp2 {VRP2_APP_VERSION.ljust(8)} {platform.system()}",
            "crpOsVersion": platform.release(),
            "crpBrowser": "OdooERP",
            "crpBrowserVersion": "19.0",
        }

        # Serialize the body ONCE, compact, and send those exact bytes. The
        # crpChecksum is computed over this same string, so we must not let
        # requests reserialize it (its json= default inserts spaces).
        body_bytes = None
        if json_data is not None:
            body_str = _compact_json(json_data)
            body_bytes = body_str.encode("utf-8")
            headers["Content-Type"] = "application/json"

        if token:
            headers["crpToken"] = token
            if method.upper() == "POST" and body_bytes is not None:
                headers["crpChecksum"] = _crp_checksum(body_str, token)

        resp = requests.request(
            method,
            url,
            data=body_bytes,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        return resp

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def _handle_error(self, resp, method, path):
        """Raise UserError with a meaningful message from a VRP2 error response."""
        body = resp.text[:500]
        _logger.warning(
            "VRP2 %s %s → %s: %s", method, path, resp.status_code, body
        )

        error_desc = ""
        error_code = ""
        try:
            data = resp.json()
            error_desc = data.get("errorDescription", "")
            error_code = data.get("errorCode", "")
        except Exception:
            pass

        msg = error_desc or resp.reason or f"HTTP {resp.status_code}"
        if error_code:
            msg = f"{msg} (Kód chyby: {error_code})"

        if resp.status_code == 800 and error_desc == "EErrorCode.SYNC_ERROR":
            raise UserError(
                _(
                    "VRP2: Unsynchronised receipt or location. "
                    "The system will attempt to re-sync automatically. "
                    "Error code: -100"
                )
            )

        raise UserError(_("VRP2 error: %s") % msg)

    # ------------------------------------------------------------------
    # Dashboard / system data
    # ------------------------------------------------------------------

    def _get_dashboard(self, holder):
        """GET /v2/user/getdashboard — cash register + business info."""
        return self._get(holder, "/v2/user/getdashboard")

    def _get_vat_list(self, holder):
        """GET /v1/vat/vatlist — available VAT rates."""
        return self._get(holder, "/v1/vat/vatlist")

    def _get_params(self, holder):
        """POST /v1/system/getparams — system parameters."""
        return self._post(
            holder,
            "/v1/system/getparams",
            json_data={
                "paramNames": [
                    "ALLOWED_CHARS_IN_SERVICE_NAME",
                    "DEFAULT_CURRENCY",
                    "DEFAULT_LANGUAGE_OVERRIDE",
                    "MAX_IMPORT_ITEMS",
                    "REPORTS_OVERVIEW_REFRESH_INTERVAL",
                    "SUPPORTED_LANGUAGES",
                ],
            },
        )

    def _get_exchange_rates(self, holder):
        """GET /v1/system/exchangerates — exchange rates."""
        return self._get(holder, "/v1/system/exchangerates")

    # ------------------------------------------------------------------
    # Service (Product) endpoints
    # ------------------------------------------------------------------

    def _get_service_list(self, holder):
        """GET /v1/service/getservicelist — all products/services."""
        return self._get(holder, "/v1/service/getservicelist")

    def _get_service_data(self, holder, service_code):
        """GET /v1/service/getservicedata/<code> — single product detail."""
        return self._get(
            holder, f"/v1/service/getservicedata/{service_code}"
        )

    def _add_service(self, holder, service_data):
        """POST /v1/service/addservice — create a new product/service."""
        return self._post(
            holder, "/v1/service/addservice", json_data=service_data
        )

    def _set_service_data(self, holder, service_data):
        """POST /v1/service/setservicedata — update existing product/service."""
        return self._post(
            holder, "/v1/service/setservicedata", json_data=service_data
        )

    def _set_services(self, holder, services_data):
        """POST /v1/service/setservices — bulk update services."""
        return self._post(
            holder, "/v1/service/setservices", json_data=services_data
        )

    def _add_service_correction(self, holder, correction_data):
        """POST /v1/service/addservicecorrection — deactivate/correct service."""
        return self._post(
            holder,
            "/v1/service/addservicecorrection",
            json_data=correction_data,
        )

    def _get_unique_service_list(self, holder):
        """GET /v1/service/getuniqueservicelist."""
        return self._get(holder, "/v1/service/getuniqueservicelist")

    def _import_services(self, holder, import_data):
        """POST /v1/service/importservices — bulk import."""
        return self._post(
            holder, "/v1/service/importservices", json_data=import_data
        )

    # ------------------------------------------------------------------
    # Service Category endpoints
    # ------------------------------------------------------------------

    def _get_category_list(self, holder):
        """GET /v1/service/category/list — all categories."""
        return self._get(holder, "/v1/service/category/list")

    def _set_category(self, holder, category_data):
        """POST /v1/service/category/set — create/update/delete categories."""
        return self._post(
            holder, "/v1/service/category/set", json_data=category_data
        )

    def _get_color_list(self, holder):
        """GET /v1/service/color/list — available category colors."""
        return self._get(holder, "/v1/service/color/list")

    # ------------------------------------------------------------------
    # Receipt endpoints
    # ------------------------------------------------------------------

    def _create_receipt_valid(self, holder, receipt_data):
        """POST /v5/receipt/create/valid."""
        return self._post(
            holder, "/v5/receipt/create/valid", json_data=receipt_data
        )

    def _create_receipt_invalid(self, holder, receipt_data):
        """POST /v5/receipt/create/invalid."""
        return self._post(
            holder, "/v5/receipt/create/invalid", json_data=receipt_data
        )

    def _create_deposit(self, holder, amount):
        """POST /v5/receipt/create/deposit."""
        return self._post(
            holder,
            "/v5/receipt/create/deposit",
            json_data={"priceWithVat": amount},
        )

    def _create_withdraw(self, holder, amount):
        """POST /v5/receipt/create/withdraw."""
        return self._post(
            holder,
            "/v5/receipt/create/withdraw",
            json_data={"priceWithVat": -abs(amount)},
        )

    def _create_invoice(self, holder, invoice_data):
        """POST /v5/receipt/create/invoice — fiscal receipt for an invoice payment.

        ``invoice_data`` is the full request body, e.g. ``{"dto": {...}}``.
        """
        return self._post(
            holder, "/v5/receipt/create/invoice", json_data=invoice_data
        )

    def _get_receipt_data(self, holder, server_id):
        """GET /v4/receipt/getdata?id=<id> — one receipt's full detail.

        Returns ``{"dto": {...}}`` with the items as VRP2 printed them
        (``service.name`` for catalogue items, ``itemName`` for refunds).
        """
        return self._get(
            holder, "/v4/receipt/getdata", params={"id": server_id}
        )

    def _get_receipt_list(self, holder, filter_criteria=None, start=0,
                          count=10):
        """POST /v4/receipt/receiptlist — paged receipt search.

        A POST with a paging/filter/ordering body (captured 2026-10-06); the
        GET this used to send is not what the web app does.
        """
        criteria = {
            "createDateFrom": None,
            "createDateTo": None,
            "issueDateFrom": None,
            "issueDateTo": None,
            "priceVatFrom": None,
            "priceVatTo": None,
            "receiptId": None,
            "receiptNumber": None,
            "receiptTypeName": None,
            "isChit": None,
        }
        criteria.update(filter_criteria or {})
        return self._post(holder, "/v4/receipt/receiptlist", json_data={
            "paging": {"resultSetStart": start, "resultSetCount": count},
            "filterCriteria": criteria,
            "ordering": {"orderColumn": "createDate", "orderDirection": "desc"},
        })

    def _send_receipt_email(self, holder, receipt_id, email):
        """POST /v5/receipt/send — email a receipt."""
        return self._post(
            holder,
            "/v5/receipt/send",
            json_data={"dto": {"id": receipt_id, "emailAddress": email}},
        )

    def _sync(self, holder):
        """GET /v5/receipt/sync — re-sync an unsynchronised receipt."""
        return self._get(holder, "/v5/receipt/sync")
