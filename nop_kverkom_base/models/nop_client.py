"""mTLS REST client for the NOP KVERKOM ERP API.

Endpoints used:

* ``POST /api/v1/generateNewTransactionId`` — mint a new ``QR-<uuid>`` id.
* ``GET  /api/v1/getAllTransactions/POKLADNICA-<id>?date_from=...&after_id=...``
  — paginated list of bank-pushed notifications (records expire 2 h after push).
* ``GET  /api/v1/getTransactionHistory/<QR-id>`` — single-record public lookup
  (served from a different host, without auth).

Authentication for the first two is mutual TLS using the merchant's eKasa cert.
All methods receive a ``pos.config`` record whose ``nop_*`` fields carry the
cert material, environment URLs, and sync bookkeeping.
"""

import logging
import uuid
from datetime import timedelta

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30  # seconds — matches NOP spec read/idle timeout
PAGE_LIMIT = 100


class NopClient(models.AbstractModel):
    _name = "nop.client"
    _description = "NOP KVERKOM REST Client"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def _generate_transaction_id(self, pos_config, comment=None):
        """POST /api/v1/generateNewTransactionId → ``QR-<32-hex-uuid>``."""
        cert_b64, _key, _ca = pos_config._get_active_nop_cert_material()
        if self.env.context.get("nop_offline") or not cert_b64:
            return "QR-" + uuid.uuid4().hex

        body = {}
        if comment:
            body["comment"] = comment[:256]

        resp_json = self._request(
            pos_config,
            "POST",
            "/api/v1/generateNewTransactionId",
            json=body or None,
        )
        tx_id = resp_json.get("transaction_id") or resp_json.get("id")
        if not tx_id or not tx_id.startswith("QR-"):
            raise UserError(
                _("Unexpected NOP response (no transaction_id): %s") % resp_json
            )
        return tx_id

    def _drain(self, pos_config, date_from=None, after_id=None):
        """Drain new NOP notifications into nop.transaction records.

        Returns the count of freshly-ingested notifications.
        """
        cert_b64, _key, _ca = pos_config._get_active_nop_cert_material()
        if self.env.context.get("nop_offline") or not cert_b64:
            return 0

        if date_from is None:
            last = pos_config.nop_last_sync_at
            if last:
                date_from = last - timedelta(minutes=10)
            else:
                date_from = fields.Datetime.now() - timedelta(hours=2)

        params = {"date_from": _fmt_iso(date_from), "limit": PAGE_LIMIT}
        if after_id:
            params["after_id"] = after_id

        path = f"/api/v1/getAllTransactions/POKLADNICA-{pos_config.nop_pokladnica_id_ext}"
        ingested = 0
        NopTx = self.env["nop.transaction"].sudo()

        while True:
            resp = self._request(pos_config, "GET", path, params=params, raw=True)
            payload = resp.json()
            rows = payload if isinstance(payload, list) else payload.get("transactions") or []
            for row in rows:
                tx_id = row.get("endToEndId")
                if not tx_id:
                    continue
                nop_tx = NopTx.search([("transaction_id", "=", tx_id)], limit=1)
                if not nop_tx:
                    nop_tx = NopTx.create({
                        "pos_config_id": pos_config.id,
                        "transaction_id": tx_id,
                        "state": "pending",
                        "expected_iban": (row.get("creditorAccount") or {}).get("iban") or "",
                        "expected_amount": float((row.get("transactionAmount") or {}).get("amount") or 0),
                        "currency_id": self.env.ref("base.EUR").id,
                    })
                if nop_tx._ingest_notification(row):
                    ingested += 1

            truncated = (resp.headers.get("x-result-truncated") or "").lower() == "true"
            if not truncated or not rows:
                break
            params["after_id"] = rows[-1].get("endToEndId") or rows[-1].get("transactionId")

        self.env.cr.execute(
            "UPDATE pos_config SET nop_last_sync_at = NOW() AT TIME ZONE 'UTC', nop_last_sync_error = NULL WHERE id = %s",
            (pos_config.id,),
        )
        pos_config.invalidate_recordset(["nop_last_sync_at", "nop_last_sync_error"])
        return ingested

    def _fetch_history(self, pos_config, transaction_id):
        """GET /api/v1/getTransactionHistory/<QR-id> on the public history host (no auth)."""
        url = f"{pos_config.nop_history_url}/api/v1/getTransactionHistory/{transaction_id}"
        try:
            import requests
        except ImportError as e:
            raise UserError(_("The 'requests' Python package is required.")) from e
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Low-level HTTP
    # ------------------------------------------------------------------

    def _request(self, pos_config, method, path, params=None, json=None, raw=False):
        """mTLS request with the pos_config's active cert."""
        try:
            import requests
        except ImportError as e:
            raise UserError(_("The 'requests' Python package is required.")) from e

        url = f"{pos_config.nop_erp_api_url}{path}"
        headers = {
            "Accept": "application/json",
            "X-Correlation-ID": uuid.uuid4().hex,
        }
        if json is not None:
            headers["Content-Type"] = "application/json"

        with pos_config._nop_mtls_material() as (cert_path, key_path, ca_path):
            resp = requests.request(
                method,
                url,
                params=params,
                json=json,
                cert=(cert_path, key_path),
                verify=ca_path,
                timeout=REQUEST_TIMEOUT,
                headers=headers,
            )

        if resp.status_code >= 400:
            _logger.warning(
                "NOP %s %s -> %s: %s",
                method, path, resp.status_code, resp.text[:500],
            )
            resp.raise_for_status()

        if raw:
            return resp
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()


def _fmt_iso(dt):
    """NOP expects ISO-8601 UTC, ``YYYY-MM-DDTHH:MM:SSZ``."""
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
