import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

# VRP2 rounds the cash share to 0.05 € half-up (zaokruhli5). Odoo's own cash
# rounding must do the same, or the drawer drifts from the register by the
# rounding difference on every cash sale (18.48 in Odoo, 18.50 in VRP2).
VRP2_CASH_ROUNDING = 0.05


class PosConfig(models.Model):
    # Each POS till is its own VRP2 cash register: it carries its own
    # credentials/session via the mixin and fiscalizes its sales on it.
    _name = "pos.config"
    _inherit = ["pos.config", "vrp2.credentials.mixin"]

    vrp2_enabled = fields.Boolean(
        string="Enable VRP2",
        help="Fiscalize this till's sales in the Slovak Virtual Cash "
        "Register. Set the till's own VRP2 credentials below.",
    )
    vrp2_auto_fiscalize = fields.Boolean(
        string="Fiscalize Automatically",
        default=True,
        help="Issue the VRP2 receipt as soon as the till syncs a paid order. "
        "A failure never blocks the sale: the order is marked 'VRP2 Error' "
        "and can be fiscalized again from its form.",
    )

    def _vrp2_odoo_rounds_like_vrp2(self):
        """Odoo's cash rounding is exactly VRP2's: 0.05, nearest, cash only."""
        self.ensure_one()
        method = self.rounding_method
        return bool(
            self.cash_rounding
            and self.only_round_cash_method
            and method
            and method.rounding_method == "HALF-UP"
            and not float_compare(method.rounding, VRP2_CASH_ROUNDING,
                                  precision_digits=6)
        )

    @api.model
    def _vrp2_find_cash_rounding(self):
        return self.env["account.cash.rounding"].search([
            ("rounding", "=", VRP2_CASH_ROUNDING),
            ("rounding_method", "=", "HALF-UP"),
            ("strategy", "=", "add_invoice_line"),
        ], limit=1)

    @api.onchange("vrp2_enabled", "vrp2_round_5c")
    def _onchange_vrp2_cash_rounding(self):
        """Set Odoo's cash rounding to match the register's."""
        for config in self.filtered("vrp2_enabled"):
            if config.vrp2_round_5c:
                config.cash_rounding = True
                config.only_round_cash_method = True
                if not config._vrp2_odoo_rounds_like_vrp2():
                    config.rounding_method = (
                        config._vrp2_find_cash_rounding()
                        or config.rounding_method
                    )
            else:
                config.cash_rounding = False

    @api.constrains(
        "vrp2_enabled", "vrp2_round_5c", "cash_rounding", "rounding_method",
        "only_round_cash_method",
    )
    def _check_vrp2_cash_rounding(self):
        """Odoo must round cash exactly when, and exactly as, VRP2 does.

        Rounding in VRP2 but not in Odoo leaves Odoo's drawer 2 cents short
        of the register on an 18.48 sale; rounding in Odoo but not in VRP2
        does the reverse. Neither raises anywhere else; the cash count just
        never agrees with the register's report.
        """
        for config in self.filtered("vrp2_enabled"):
            if config.vrp2_round_5c and not config._vrp2_odoo_rounds_like_vrp2():
                raise ValidationError(_(
                    "Point of Sale '%(pos)s' rounds cash to 0.05 € in VRP2, "
                    "so its Odoo cash rounding must do the same: enable Cash "
                    "Rounding with a 0.05 'Nearest' rounding method (Add a "
                    "rounding line) and 'Only apply rounding on cash'.",
                    pos=config.display_name,
                ))
            if not config.vrp2_round_5c and config.cash_rounding:
                raise ValidationError(_(
                    "Point of Sale '%(pos)s' does not round cash in VRP2, so "
                    "Odoo must not round it either: disable Cash Rounding or "
                    "enable 'Round to 0.05 €'.",
                    pos=config.display_name,
                ))

    def action_vrp2_login(self):
        """Authenticate this till and cache the (national) VAT list on the
        company for the tax mapping used by catalog sync / receipts."""
        res = super().action_vrp2_login()
        vat_resp = self.env["vrp2.client"]._get_vat_list(self)
        self.company_id.sudo().write({
            "vrp2_vatlist_json": json.dumps(vat_resp.get("results", [])),
        })
        return res

    @api.model
    def vrp2_company_credentials(self, company_id=False):
        """Return the company default register's VRP2 credentials.

        Used by the "Load Credentials from Company" form widget, which applies
        them to the record in memory (no save / no dialog reload).
        """
        company = (
            self.env["res.company"].browse(company_id)
            if company_id else self.env.company
        ).sudo()
        if not company.vrp2_login:
            raise UserError(_(
                "The company has no VRP2 credentials. Set them in "
                "Accounting ▸ Settings ▸ VRP2 first."
            ))
        return {
            "vrp2_login": company.vrp2_login,
            "vrp2_password": company.vrp2_password or "",
        }

    @api.constrains("vrp2_login")
    def _check_vrp2_login_unique(self):
        """A VRP2 login is one physical cash register — it can belong to only
        one POS."""
        for config in self:
            if not config.vrp2_login:
                continue
            duplicate = self.sudo().with_context(active_test=False).search([
                ("id", "!=", config.id),
                ("vrp2_login", "=", config.vrp2_login),
            ], limit=1)
            if duplicate:
                raise ValidationError(_(
                    "VRP2 login '%(login)s' is already used by Point of Sale "
                    "'%(pos)s'. Each VRP2 cash register can belong to only one "
                    "POS.",
                    login=config.vrp2_login,
                    pos=duplicate.display_name,
                ))

    def _vrp2_check_ready(self):
        self.ensure_one()
        if not self.vrp2_login:
            raise UserError(
                _("VRP2 credentials are not configured on till '%s'.")
                % self.display_name
            )
        self.env["vrp2.client"]._ensure_session(self)

    def action_vrp2_sync_to(self):
        """Push this till's catalog (categories + products) to its register."""
        self._vrp2_check_ready()
        cat_created, cat_updated, cat_deleted = (
            self.env["pos.category"]._vrp2_push(self)
        )
        prod_created, prod_updated, prod_deactivated = (
            self.env["product.template"]._vrp2_push(self)
        )
        msg = _(
            "Categories: %d created, %d updated, %d deleted.\n"
            "Products: %d created, %d updated, %d deactivated."
        ) % (
            cat_created, cat_updated, cat_deleted,
            prod_created, prod_updated, prod_deactivated,
        )
        return self._vrp2_notify(_("VRP2 Sync Complete"), msg, sticky=True)

    def action_vrp2_pull(self):
        """Pull this till's catalog from its register into Odoo."""
        self._vrp2_check_ready()
        cat_count = self.env["pos.category"]._vrp2_pull(self)
        prod_count = self.env["product.template"]._vrp2_pull(self)
        return self._vrp2_notify(
            _("VRP2 Pull Complete"),
            _("Pulled %d categories and %d products from VRP2.")
            % (cat_count, prod_count),
        )

    def _vrp2_notify(self, title, message, sticky=False):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": message,
                "type": "success",
                "sticky": sticky,
            },
        }
