"""Abstract connector interface shared by all EDI provider modules.

Each provider (Editel, GRiT, ...) defines a concrete model that inherits
this mixin and overrides the four transport methods.
"""

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class EdiConnectorMixin(models.AbstractModel):
    _name = "edi.connector.mixin"
    _description = "EDI Connector (Abstract Mixin)"

    # ------------------------------------------------------------------
    # Transport methods — override in concrete connector
    # ------------------------------------------------------------------

    def _authenticate(self):
        _logger.warning(
            "%s: _authenticate() called but not implemented.", self._name
        )

    def _send_message(self, message_record):
        _logger.warning(
            "%s: _send_message() called but not implemented. "
            "Message %s will not be transmitted.",
            self._name,
            message_record.name,
        )
        return False

    def _poll_inbound(self):
        _logger.warning(
            "%s: _poll_inbound() called but not implemented.", self._name
        )
        return {"messages": [], "has_more": False}

    def _acknowledge_inbound(self, raw_id):
        _logger.warning(
            "%s: _acknowledge_inbound(%s) called but not implemented.",
            self._name,
            raw_id,
        )
