"""NOP KVERKOM configuration on ``pos.config``.

A single POS-config ↔ single NOP pokladnica (1:1) mapping is a regulatory
requirement of the Slovak eKasa framework: one mTLS certificate identifies
one physical till. We model that identity directly on ``pos.config`` rather
than introducing a separate model — the schema enforces the relationship,
the configuration UI is single-place, and ``nop.transaction`` records point
at the POS config they belong to.

All NOP-specific fields are prefixed with ``nop_`` to keep the pos.config
namespace clean.
"""

import base64
import logging
import re
import tempfile
from contextlib import contextmanager
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# NOP KVERKOM environment endpoints — see https://www.info-qrplatby.sk/
NOP_ENVIRONMENTS = {
    "int": {
        "erp_api": "https://api-erp-i.kverkom.sk",
        "history": "https://kdejemojaplatba-i.kverkom.sk",
    },
    "prod": {
        "erp_api": "https://api-erp.kverkom.sk",
        "history": "https://kdejemojaplatba.kverkom.sk",
    },
}

VATSK_RE = re.compile(r"VATSK-(\d{10})")
POKLADNICA_RE = re.compile(r"POKLADNICA[- ](\d{17})")


class PosConfig(models.Model):
    _inherit = "pos.config"

    # --- Identity ---------------------------------------------------------
    nop_environment = fields.Selection(
        [("int", "Integration"), ("prod", "Production")],
        string="NOP environment",
        help="Which NOP KVERKOM environment this POS talks to. Leave empty if "
        "QR Platby is not enabled for this POS.",
    )
    nop_vatsk = fields.Char(
        string="VATSK",
        readonly=True,
        copy=False,
        help="10-digit Slovak tax ID parsed from the eKasa client certificate.",
    )
    nop_pokladnica_id_ext = fields.Char(
        string="Pokladnica ID",
        readonly=True,
        copy=False,
        help="17-digit cash register ID (eKasa), parsed from the client certificate.",
    )

    nop_iban_id = fields.Many2one(
        "res.partner.bank",
        string="NOP merchant IBAN",
        domain="[('partner_id', '=', company_id.partner_id.id)]",
        help="Account where QR Platba payments land. Used as the IBAN in the "
        "QR code and for integrity-hash verification.",
    )
    nop_merchant_name = fields.Char(
        string="NOP merchant name",
        help="Merchant name that appears in the QR payment URL (CN field, "
        "max 70 chars, no diacritics).",
    )

    # --- Certificates — separate slots for int and prod -------------------
    nop_int_client_cert_pem = fields.Binary(
        string="INT Client Certificate (PEM)", attachment=False,
        help="PEM-encoded INT-environment eKasa cert (Disig TEST CA).",
    )
    nop_int_client_cert_filename = fields.Char()
    nop_int_client_key_pem = fields.Binary(
        string="INT Client Private Key (PEM)", attachment=False,
        groups="point_of_sale.group_pos_manager",
    )
    nop_int_client_key_filename = fields.Char()
    nop_int_ca_bundle_pem = fields.Binary(
        string="INT CA Bundle (PEM)", attachment=False,
        help="kverkom-ca-bundle.pem from info-qrplatby.sk.",
    )
    nop_int_ca_bundle_filename = fields.Char()

    nop_prod_client_cert_pem = fields.Binary(
        string="PROD Client Certificate (PEM)", attachment=False,
        help="Production eKasa cert issued by Financná správa SR.",
    )
    nop_prod_client_cert_filename = fields.Char()
    nop_prod_client_key_pem = fields.Binary(
        string="PROD Client Private Key (PEM)", attachment=False,
        groups="point_of_sale.group_pos_manager",
    )
    nop_prod_client_key_filename = fields.Char()
    nop_prod_ca_bundle_pem = fields.Binary(
        string="PROD CA Bundle (PEM)", attachment=False,
        help="kverkom-prod-ca-bundle.pem from info-qrplatby.sk.",
    )
    nop_prod_ca_bundle_filename = fields.Char()

    nop_has_int_cert = fields.Boolean(compute="_compute_nop_cert_presence")
    nop_has_prod_cert = fields.Boolean(compute="_compute_nop_cert_presence")

    nop_erp_api_url = fields.Char(compute="_compute_nop_endpoints")
    nop_history_url = fields.Char(compute="_compute_nop_endpoints")

    nop_last_sync_at = fields.Datetime(
        readonly=True, copy=False,
        help="Last successful getAllTransactions poll for this POS.",
    )
    nop_last_sync_error = fields.Char(readonly=True, copy=False)

    nop_transaction_ids = fields.One2many("nop.transaction", "pos_config_id")

    _nop_vatsk_pokladnica_env_uniq = models.Constraint(
        "unique(nop_vatsk, nop_pokladnica_id_ext, nop_environment)",
        "Another POS config is already registered with this VATSK/POKLADNICA for this NOP environment.",
    )

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------

    @api.depends("nop_environment")
    def _compute_nop_endpoints(self):
        for cfg in self:
            urls = NOP_ENVIRONMENTS.get(cfg.nop_environment) or {}
            cfg.nop_erp_api_url = urls.get("erp_api") or False
            cfg.nop_history_url = urls.get("history") or False

    @api.depends(
        "nop_int_client_cert_pem", "nop_int_client_key_pem",
        "nop_prod_client_cert_pem", "nop_prod_client_key_pem",
    )
    def _compute_nop_cert_presence(self):
        for cfg in self:
            cfg.nop_has_int_cert = bool(
                cfg.nop_int_client_cert_pem and cfg.nop_int_client_key_pem
            )
            cfg.nop_has_prod_cert = bool(
                cfg.nop_prod_client_cert_pem and cfg.nop_prod_client_key_pem
            )

    # ------------------------------------------------------------------
    # Cert identity parsing
    # ------------------------------------------------------------------

    @api.constrains(
        "nop_int_client_cert_pem", "nop_int_client_key_pem",
        "nop_prod_client_cert_pem", "nop_prod_client_key_pem",
    )
    def _check_nop_certificate(self):
        for cfg in self:
            cfg._parse_nop_certificate_subject()

    def _parse_nop_certificate_subject(self):
        """Extract VATSK + POKLADNICA from whichever env's cert is present.

        INT and PROD certs (if both set) must carry the same identity; a
        mismatch raises ``ValidationError`` to prevent pointing one POS at
        two different physical tills.
        """
        self.ensure_one()

        parsed = []
        for env_key, cert_b64 in (
            ("int", self.nop_int_client_cert_pem),
            ("prod", self.nop_prod_client_cert_pem),
        ):
            if cert_b64:
                parsed.append((env_key, self._extract_nop_identity(cert_b64)))

        if not parsed:
            return

        identities = {ident for _env, ident in parsed}
        if len(identities) > 1:
            raise ValidationError(
                _(
                    "INT and PROD certificates identify different cash registers: %s. "
                    "Both certs must carry the same VATSK and POKLADNICA.",
                )
                % ", ".join(f"{e}={i}" for e, i in parsed)
            )

        preferred = next(
            (ident for env_key, ident in parsed if env_key == self.nop_environment),
            parsed[0][1],
        )
        self.nop_vatsk, self.nop_pokladnica_id_ext = preferred

    @staticmethod
    def _extract_nop_identity(cert_b64):
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend

        pem = base64.b64decode(cert_b64)
        try:
            cert = x509.load_pem_x509_certificate(pem, default_backend())
        except Exception as e:
            raise ValidationError(_("Invalid PEM certificate: %s") % e)
        subject_str = cert.subject.rfc4514_string()
        vatsk_m = VATSK_RE.search(subject_str)
        pokl_m = POKLADNICA_RE.search(subject_str)
        if not vatsk_m or not pokl_m:
            raise ValidationError(
                _("Could not extract VATSK/POKLADNICA from certificate subject: %s")
                % subject_str
            )
        return (vatsk_m.group(1), pokl_m.group(1))

    @api.onchange(
        "nop_int_client_cert_pem", "nop_prod_client_cert_pem", "nop_environment",
    )
    def _onchange_nop_client_cert_pem(self):
        try:
            self._parse_nop_certificate_subject()
        except Exception as e:
            return {
                "warning": {
                    "title": _("Certificate error"),
                    "message": str(e),
                }
            }

    # ------------------------------------------------------------------
    # Active-environment helpers
    # ------------------------------------------------------------------

    def _get_active_nop_cert_material(self):
        """Return (cert_pem, key_pem, ca_pem) for the currently-selected env."""
        self.ensure_one()
        if self.nop_environment == "prod":
            return (
                self.nop_prod_client_cert_pem,
                self.nop_prod_client_key_pem,
                self.nop_prod_ca_bundle_pem,
            )
        return (
            self.nop_int_client_cert_pem,
            self.nop_int_client_key_pem,
            self.nop_int_ca_bundle_pem,
        )

    @contextmanager
    def _nop_mtls_material(self):
        """Yield (cert_path, key_path, ca_path) temp files for ``requests``."""
        self.ensure_one()
        cert_b64, key_b64, ca_b64 = self._get_active_nop_cert_material()
        if not cert_b64 or not key_b64:
            raise UserError(
                _("POS %(name)s has no %(env)s client certificate/key configured.")
                % {
                    "name": self.display_name,
                    "env": (self.nop_environment or "int").upper(),
                }
            )
        cert_bytes = base64.b64decode(cert_b64)
        key_bytes = base64.b64decode(key_b64)
        ca_bytes = base64.b64decode(ca_b64) if ca_b64 else None

        tmp_cert = tempfile.NamedTemporaryFile(suffix=".pem", delete=False)
        tmp_key = tempfile.NamedTemporaryFile(suffix=".pem", delete=False)
        tmp_ca = (
            tempfile.NamedTemporaryFile(suffix=".pem", delete=False) if ca_bytes else None
        )
        try:
            tmp_cert.write(cert_bytes); tmp_cert.close()
            tmp_key.write(key_bytes); tmp_key.close()
            if tmp_ca:
                tmp_ca.write(ca_bytes); tmp_ca.close()
            yield tmp_cert.name, tmp_key.name, (tmp_ca.name if tmp_ca else True)
        finally:
            import os
            for path in (tmp_cert.name, tmp_key.name, tmp_ca.name if tmp_ca else None):
                if path and path is not True:
                    try:
                        os.unlink(path)
                    except OSError:
                        pass

    # ------------------------------------------------------------------
    # Polling
    # ------------------------------------------------------------------

    def _nop_poll_if_due(self, min_interval_seconds=2):
        """Call ``getAllTransactions`` at most once every ``min_interval_seconds``.

        Uses ``FOR UPDATE SKIP LOCKED`` so concurrent POS pollers don't
        stampede the NOP API. Returns the count of freshly-ingested
        notifications (0 if rate-limited or if NOP has nothing new).
        """
        self.ensure_one()
        now = fields.Datetime.now()
        cutoff = now - timedelta(seconds=min_interval_seconds)
        self.env.cr.execute(
            """
            SELECT id FROM pos_config
            WHERE id = %s
              AND (nop_last_sync_at IS NULL OR nop_last_sync_at < %s)
            FOR UPDATE SKIP LOCKED
            """,
            (self.id, cutoff),
        )
        if not self.env.cr.fetchone():
            return 0

        try:
            return self.env["nop.client"]._drain(self)
        except Exception as e:
            self.nop_last_sync_error = str(e)[:240]
            _logger.exception("NOP poll failed for %s", self.display_name)
            return 0

    @api.model
    def _cron_nop_poll_pending(self):
        """Safety-net poller — drains NOP for any POS that has tx awaiting a push."""
        window_floor = fields.Datetime.now() - timedelta(hours=2, minutes=5)
        candidates = self.env["nop.transaction"].search([
            "|",
            ("state", "=", "pending"),
            "&",
            ("state", "=", "unconfirmed_closed"),
            ("closed_unconfirmed_at", ">=", window_floor),
        ])
        for pos_config in candidates.pos_config_id:
            pos_config._nop_poll_if_due(min_interval_seconds=10)
