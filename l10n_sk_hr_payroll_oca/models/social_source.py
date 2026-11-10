# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Coordinate monthly assessment with dated HR-version changes under RR."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class Employee(models.Model):
    _inherit = "hr.employee"

    l10n_sk_social_source_epoch = fields.Integer(default=0, readonly=True, copy=False)

    @api.model_create_multi
    def create(self, values_list):
        if "default_l10n_sk_social_source_epoch" in self.env.context or any(
            "l10n_sk_social_source_epoch" in values for values in values_list
        ):
            raise UserError(_("Social-insurance source coordination is internal."))
        return super().create(values_list)

    def write(self, values):
        if "l10n_sk_social_source_epoch" in values:
            raise UserError(_("Social-insurance source coordination is internal."))
        return super().write(values)

    def _l10n_sk_lock_social_source(self):
        self.check_access("read")
        if not self:
            return
        self.flush_recordset(["l10n_sk_social_source_epoch"])
        self.env.cr.execute(
            "SELECT id FROM hr_employee WHERE id IN %s ORDER BY id FOR NO KEY UPDATE",
            [tuple(sorted(self.ids))],
        )
        self.env.cr.execute(
            "UPDATE hr_employee SET l10n_sk_social_source_epoch="
            "COALESCE(l10n_sk_social_source_epoch,0)+1 WHERE id IN %s",
            [tuple(sorted(self.ids))],
        )
        self.invalidate_recordset(["l10n_sk_social_source_epoch"])


class Version(models.Model):
    _inherit = "hr.version"

    @api.model_create_multi
    def create(self, values_list):
        self.check_access("create")
        ids = {
            values.get("employee_id", self.env.context.get("default_employee_id"))
            for values in values_list
        }
        self.env["hr.employee"].browse(
            sorted(identifier for identifier in ids if identifier)
        )._l10n_sk_lock_social_source()
        return super().create(values_list)

    def write(self, values):
        self.check_access("write")
        employees = self.employee_id | self.env["hr.employee"].browse(
            values.get("employee_id")
        )
        employees._l10n_sk_lock_social_source()
        return super().write(values)

    def unlink(self):
        self.check_access("unlink")
        self.employee_id._l10n_sk_lock_social_source()
        return super().unlink()
