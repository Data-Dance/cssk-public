"""ePošťák provider registration on ``edi.message``.

Registers the ``epostak`` provider key, points the base dispatcher at the
ePošťák connector and its poll cron, and stamps the environment on every
message at create time so a document sent from the sandbox is never later
chased for status against production (and vice versa).
"""

import logging

from odoo import api, models

from .epostak_connector import PRODUCTION, SANDBOX

_logger = logging.getLogger(__name__)


class EdiMessage(models.Model):
    _inherit = "edi.message"

    @api.model
    def _selection_provider(self):
        return super()._selection_provider() + [("epostak", "ePošťák")]

    def _register_hook(self):
        """Register ePošťák in the message class maps."""
        super()._register_hook()
        self.PROVIDER_CONNECTOR_MAP["epostak"] = "epostak.connector"
        self.PROVIDER_CRON_MAP["epostak"] = (
            "edi_epostak_base.cron_epostak_get_messages"
        )
        # No job runner: the broker dictates when to retry (kind +
        # retry_after), and what queue_job would otherwise be buying here —
        # orchestration and a backoff curve — is exactly what that replaces.
        # `queued` is picked up by edi_base's own cron instead.
        self.PROVIDER_DISPATCH_MAP["epostak"] = "cron"

    @api.model
    def _default_provider_mode_epostak(self):
        return self.env["epostak.connector"]._get_mode()

    def _compute_is_test_mode(self):
        """Mark sandbox traffic as test.

        The base compute knows only the Editel/GRiT mode vocabularies and
        falls through to False for anything else, which would badge live and
        sandbox ePošťák messages identically.
        """
        super()._compute_is_test_mode()
        for rec in self.filtered(lambda r: r.provider == "epostak"):
            rec.is_test_mode = rec.provider_mode == SANDBOX

    @api.model_create_multi
    def create(self, vals_list):
        """Stamp ``provider_mode`` on ePošťák messages at create time.

        Without it the connector would resolve the environment at *send* time
        from the current setting, so flipping the deployment to production
        would re-address messages that were prepared against the sandbox — to
        an endpoint whose credentials never saw them.
        """
        for vals in vals_list:
            if vals.get("provider") == "epostak" and not vals.get("provider_mode"):
                vals["provider_mode"] = self._default_provider_mode_epostak()
        return super().create(vals_list)

    def _epostak_mode(self):
        """The environment this message belongs to, with a safe fallback."""
        self.ensure_one()
        if self.provider_mode in (SANDBOX, PRODUCTION):
            return self.provider_mode
        return self.env["epostak.connector"]._get_mode()
