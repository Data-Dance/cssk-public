# -*- coding: utf-8 -*-
import base64

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..lib import eet2_client


class Eet2Certificate(models.Model):
    _name = "l10n.cz.eet2.certificate"
    _description = "EET 2.0 Cash-register Certificate (pokladní certifikát)"
    _order = "valid_to desc, id desc"

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company)
    environment = fields.Selection(
        [("playground", "Playground (non-production)"),
        ("production", "Production")],
        required=True, default="playground",
        help="Which EET 2.0 environment this certificate is valid for.")
    # The pokladní certifikát is delivered as a legacy PKCS#12 (.p12). Python's
    # `cryptography` loads its RC2-40/3DES bags fine; see EET2_CLAUDE.md §12.
    p12_file = fields.Binary(string="PKCS#12 (.p12)", required=True, attachment=True)
    p12_filename = fields.Char(string="Filename")
    password = fields.Char(
        required=True,
        help="Password protecting the .p12 file (shown in the DIS+ app).")

    # Read-only metadata, filled from the certificate on save.
    subject_cn = fields.Char(string="Subject CN (EIČ)", readonly=True)
    valid_from = fields.Datetime(readonly=True)
    valid_to = fields.Datetime(readonly=True)
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._load_metadata()
        return records

    def write(self, vals):
        res = super().write(vals)
        if {"p12_file", "password"} & set(vals):
            self._load_metadata()
        return res

    def _get_cert(self):
        """Return an ``eet2_client.Certificate`` for this record."""
        self.ensure_one()
        if not self.p12_file:
            raise UserError(_("No .p12 file uploaded on certificate %s.", self.name))
        try:
            return eet2_client.Certificate(
                base64.b64decode(self.p12_file), self.password or "")
        except Exception as exc:  # noqa: BLE001 - surface a readable error
            raise UserError(_(
                "Could not load the PKCS#12 certificate %(name)s: %(err)s",
                name=self.name, err=exc)) from exc

    def _load_metadata(self):
        for rec in self:
            if not rec.p12_file:
                continue
            cert = rec._get_cert().cert
            cn = [a.value for a in cert.subject
                if a.oid.dotted_string == "2.5.4.3"]
            rec.subject_cn = cn[0] if cn else False
            rec.valid_from = fields.Datetime.to_string(
                cert.not_valid_before_utc.replace(tzinfo=None))
            rec.valid_to = fields.Datetime.to_string(
                cert.not_valid_after_utc.replace(tzinfo=None))
