# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The qualified certificate a company signs its EPO filings with.

EPO has no accounts and no API keys: the qualified electronic signature IS the
identity (ZAREP). So this record is, in effect, the power to file on the
company's behalf, and it is readable only by the group that may file.
"""

import base64

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..lib import epo

_MANAGER = "l10n_cssk_submission_base.group_cssk_submission_manager"


class L10nCzEpoCertificate(models.Model):
    _name = "l10n.cz.epo.certificate"
    _description = "Qualified certificate for EPO filing"
    _order = "valid_to desc, id desc"

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda s: s.env.company)
    active = fields.Boolean(default=True)
    p12_file = fields.Binary(
        string="Certificate (.p12 / .pfx)", required=True, attachment=True,
        groups=_MANAGER,
        help="The qualified certificate with its private key, as exported from "
        "the certification authority (I.CA, PostSignum, eIdentity).")
    p12_filename = fields.Char(groups=_MANAGER)
    password = fields.Char(
        groups=_MANAGER, help="Password protecting the .p12 / .pfx file.")

    subject = fields.Char(readonly=True)
    issuer = fields.Char(readonly=True)
    valid_from = fields.Datetime(readonly=True)
    valid_to = fields.Datetime(readonly=True)

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

    def _signing_material(self):
        """``(key, certificate, chain)``, read as superuser: the caller has
        already been authorised to file, which is what this protects."""
        self.ensure_one()
        rec = self.sudo()
        if not rec.p12_file:
            raise UserError(_("Certificate %s has no .p12 file.", self.name))
        try:
            return epo.load_p12(base64.b64decode(rec.p12_file), rec.password)
        except Exception as exc:  # noqa: BLE001 - a readable error for the user
            raise UserError(_(
                "Certificate %(name)s cannot be opened: %(error)s",
                name=self.name, error=exc)) from exc

    def _load_metadata(self):
        for rec in self:
            _key, cert, _chain = rec._signing_material()
            super(L10nCzEpoCertificate, rec).write({
                "subject": cert.subject.rfc4514_string(),
                "issuer": cert.issuer.rfc4514_string(),
                "valid_from": cert.not_valid_before_utc.replace(tzinfo=None),
                "valid_to": cert.not_valid_after_utc.replace(tzinfo=None),
            })

    def _check_usable(self):
        self.ensure_one()
        now = fields.Datetime.now()
        if self.valid_to and self.valid_to < now:
            raise UserError(_(
                "Certificate %(name)s expired on %(date)s.",
                name=self.name, date=self.valid_to))
        if self.valid_from and self.valid_from > now:
            raise UserError(_(
                "Certificate %(name)s is not valid until %(date)s.",
                name=self.name, date=self.valid_from))
