# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ResCompany(models.Model):
    """Mirror the register coordinates onto the company and feed ``l10n_sk``.

    ``l10n_sk`` renders ``res.company.trade_registry`` in the external layout,
    so that is where the § 3a sentence has to land for it to appear on a
    document. Keeping it in step with the coordinates is the whole point of the
    module — but the field stays writable, because a company that wants
    different wording is entitled to it.
    """

    _inherit = "res.company"

    l10n_sk_register_name = fields.Char(
        related="partner_id.l10n_sk_register_name", readonly=False
    )
    l10n_sk_register_office = fields.Char(
        related="partner_id.l10n_sk_register_office", readonly=False
    )
    l10n_sk_register_number = fields.Char(
        related="partner_id.l10n_sk_register_number", readonly=False
    )
    l10n_sk_trade_registry_statement = fields.Char(
        related="partner_id.l10n_sk_trade_registry_statement", readonly=False
    )

    l10n_sk_trade_registry_synced = fields.Char(
        string="Last synced § 3a statement",
        copy=False,
        help="The value this module last wrote into Trade Registry. It is how "
        "the module tells its own output apart from wording a person typed, "
        "so it never overwrites the second and never leaves the first stale.",
    )

    def _l10n_sk_sync_trade_registry(self):
        """Copy the composed sentence into the field ``l10n_sk`` prints.

        Ownership matters in both directions. Blindly writing would clobber
        wording somebody typed on purpose; only ever writing a non-empty value
        would leave the last sentence standing after the coordinates were
        cleared — stale statutory text on an invoice, which is the failure the
        module exists to prevent.
        """
        for company in self:
            statement = company.l10n_sk_trade_registry_statement or False
            current = company.trade_registry or False
            ours = current == (company.l10n_sk_trade_registry_synced or False)
            if not ours:
                # Somebody typed their own wording. Leave it alone.
                continue
            if current != statement:
                company.trade_registry = statement
            company.l10n_sk_trade_registry_synced = statement
        return True

    def action_l10n_sk_sync_trade_registry(self):
        return self._l10n_sk_sync_trade_registry()

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        companies._l10n_sk_sync_trade_registry()
        return companies

    def write(self, vals):
        res = super().write(vals)
        # Only chase the sentence when a coordinate moved. Writing
        # `trade_registry` by hand must not be undone on the same write.
        if "trade_registry" not in vals and (
            {
                "l10n_sk_register_name",
                "l10n_sk_register_office",
                "l10n_sk_register_number",
                "l10n_sk_trade_registry_statement",
            }
            & set(vals)
        ):
            self._l10n_sk_sync_trade_registry()
        return res
