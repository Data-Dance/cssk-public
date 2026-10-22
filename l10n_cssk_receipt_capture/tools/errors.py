# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""How a capture provider says no — in the two ways the capture loop acts on.

A provider used to raise a bare ``UserError`` for everything, and the loop could
only stop. That made two different situations indistinguishable:

* the provider **cannot run here right now** — switched off, not configured, its
  quota spent. The right move is the next provider: a receipt whose QR we read
  but whose eKasa lookup is disabled should still be read off the photograph;
* the provider **ran and failed** — the receipt is not registered, the model
  declined. Stop, and say why.

Both are ``UserError`` subclasses so a provider that still raises a plain
``UserError`` keeps working, as a hard failure.
"""
from odoo.exceptions import UserError


class ProviderUnavailable(UserError):
    """This provider cannot serve this receipt now; try the next one."""


class CaptureFailed(UserError):
    """The provider ran and the capture failed.

    ``usage`` is what it spent anyway — tokens, cost, the model — so the attempt
    log records real spend for a failed call. ``transient`` means the same
    request is worth repeating unchanged later (a busy model, a network
    failure); a refusal or an unregistered receipt is not, and retrying it on a
    timer would only spend money again.
    """

    def __init__(self, message, usage=None, transient=False, retry_after=None):
        super().__init__(message)
        self.usage = usage or {}
        self.transient = transient
        self.retry_after = retry_after
