# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CSSKReceiptProvider(models.Model):
    """Registry row for one way of reading a fiscal receipt.

    A provider is two things: this record (so it can be enabled, ordered and
    pointed at from a receipt) and an ``AbstractModel`` named
    ``cssk.receipt.provider.<code>`` that does the work. The record alone is
    inert; the model alone is invisible.
    """

    _name = "cssk.receipt.provider"
    _description = "Fiscal Receipt Capture Provider"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(
        required=True,
        help="Technical code. The implementation is the AbstractModel named "
             "'cssk.receipt.provider.<code>'.")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    country_ids = fields.Many2many(
        "res.country", string="Countries",
        help="Restrict this provider to receipts issued in these countries. "
             "Empty means no restriction.")

    _code_uniq = models.Constraint(
        "unique(code)",
        "A capture provider with this code already exists.",
    )

    @property
    def _implementation_name(self):
        self.ensure_one()
        return "cssk.receipt.provider.%s" % (self.code or "")

    def _implementation(self):
        """The AbstractModel implementing this provider.

        Returns an empty recordset-like model handle; note that an AbstractModel
        instance is **falsy**, so callers must test ``is None`` / membership
        rather than truthiness.
        """
        self.ensure_one()
        name = self._implementation_name
        if name not in self.env:
            return None
        return self.env[name]

    def _get_implementation(self):
        impl = self._implementation()
        if impl is None:
            raise UserError(_(
                "Capture provider %(name)s declares the implementation "
                "%(model)s, which is not installed.",
                name=self.name, model=self._implementation_name,
            ))
        return impl


class CSSKReceiptProviderMixin(models.AbstractModel):
    """What a capture provider must implement.

    Subclass with ``_name = "cssk.receipt.provider.<code>"`` and override
    ``_capture``. Everything else has a workable default.
    """

    _name = "cssk.receipt.provider.mixin"
    _description = "Fiscal Receipt Capture Provider Mixin"

    @api.model
    def _can_capture(self, receipt):
        """True when this provider can read the given receipt.

        The default accepts any receipt that carries a QR payload or an
        attachment; providers narrow it.
        """
        return bool(receipt.qr_raw or receipt.attachment_id)

    @api.model
    def _capture(self, receipt):
        """Read the receipt and return a write-ready values dict.

        Must return a dict suitable for ``receipt.write()``, including
        ``line_ids`` / ``tax_ids`` commands where the provider has them, and
        ``payload_raw`` with whatever the source actually returned. Raise
        ``UserError`` with a message a bookkeeper can act on when the source
        says no.
        """
        raise NotImplementedError
