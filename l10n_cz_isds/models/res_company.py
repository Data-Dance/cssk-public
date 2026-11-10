# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The company's data box: which one, how to sign in, test or production.

The login opens the box for whoever holds it, so the password is readable only
by the group that may file (as the EPO certificate is).
"""

import base64

from odoo import fields, models
from odoo.exceptions import UserError

from ..lib import isds

_MANAGER = "l10n_cssk_submission_base.group_cssk_submission_manager"


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_cz_isds_environment = fields.Selection(
        [("test", "Test (datovka-test.gov.cz)"),
         ("production", "Production (datovka.gov.cz)")],
        string="Data box environment", default="test", required=True,
        groups=_MANAGER,
        help="Test: the operator's test environment, with test boxes and no "
        "legal effect; production boxes cannot be reached from it. "
        "Production: the company's real data box.")
    l10n_cz_isds_auth = fields.Selection(
        [("password", "Login and password"),
         ("password_cert", "Login, password and certificate"),
         ("system_cert", "System certificate (no password)")],
        string="Data box sign-in", default="password", required=True,
        groups=_MANAGER,
        help="Login and password: a data box user. Login, password and "
        "certificate: a data box user whose login also requires the "
        "commercial certificate below. System certificate: a commercial "
        "certificate the box's administrator registered on the box for an "
        "external application; no login or password, so nothing breaks when "
        "a person's password changes.")
    l10n_cz_isds_p12 = fields.Binary(
        string="Data box certificate (.p12 / .pfx)", attachment=True,
        groups=_MANAGER,
        help="A commercial certificate with its private key (PostSignum, "
        "I.CA, eIdentity), registered for the data box or its user.")
    l10n_cz_isds_p12_password = fields.Char(
        string="Certificate password", groups=_MANAGER)
    l10n_cz_isds_cert_subject = fields.Char(
        string="Certificate", readonly=True, groups=_MANAGER)
    l10n_cz_isds_cert_valid_to = fields.Datetime(
        string="Certificate valid to", readonly=True, groups=_MANAGER)
    l10n_cz_isds_login = fields.Char(
        string="Data box login", groups=_MANAGER,
        help="The login of a data box user allowed to send messages, "
        "preferably one created for this purpose.")
    l10n_cz_isds_password = fields.Char(
        string="Data box password", groups=_MANAGER)
    l10n_cz_isds_box_id = fields.Char(
        string="Data box ID", readonly=True, groups=_MANAGER,
        help="Filled in by Test Connection from what the login opens.")
    l10n_cz_isds_box_name = fields.Char(
        string="Data box owner", readonly=True, groups=_MANAGER)

    def write(self, vals):
        res = super().write(vals)
        if {"l10n_cz_isds_p12", "l10n_cz_isds_p12_password"} & set(vals):
            for company in self:
                company._l10n_cz_isds_load_certificate_info()
        return res

    def _l10n_cz_isds_certificate(self):
        """``(key, certificate, chain)`` of the company's data box
        certificate, read as superuser."""
        self.ensure_one()
        company = self.sudo()
        if not company.l10n_cz_isds_p12:
            raise UserError(self.env._(
                "%(company)s has no data box certificate: upload it on the "
                "company's Data box tab.", company=self.display_name))
        try:
            return isds.load_p12(base64.b64decode(company.l10n_cz_isds_p12),
                                 company.l10n_cz_isds_p12_password)
        except Exception as exc:  # noqa: BLE001 - a readable error
            raise UserError(self.env._(
                "The data box certificate cannot be opened: %(error)s",
                error=exc)) from exc

    def _l10n_cz_isds_load_certificate_info(self):
        company = self.sudo()
        if not company.l10n_cz_isds_p12:
            vals = {"l10n_cz_isds_cert_subject": False,
                    "l10n_cz_isds_cert_valid_to": False}
        else:
            _key, cert, _chain = self._l10n_cz_isds_certificate()
            vals = {"l10n_cz_isds_cert_subject": cert.subject.rfc4514_string(),
                    "l10n_cz_isds_cert_valid_to":
                        cert.not_valid_after_utc.replace(tzinfo=None)}
        super(ResCompany, company).write(vals)

    def _l10n_cz_isds_client(self):
        """A client for the company's data box. Read as superuser: the
        caller has been authorised to file, which is what this protects."""
        self.ensure_one()
        company = self.sudo()
        auth = company.l10n_cz_isds_auth or "password"
        if auth != "system_cert" and not (company.l10n_cz_isds_login
                                          and company.l10n_cz_isds_password):
            raise UserError(self.env._(
                "%(company)s has no data box login: fill it in on the "
                "company's Data box tab.", company=self.display_name))
        certificate = None
        if auth != "password":
            certificate = self._l10n_cz_isds_certificate()
            valid_to = certificate[1].not_valid_after_utc.replace(tzinfo=None)
            if valid_to < fields.Datetime.now():
                raise UserError(self.env._(
                    "The data box certificate expired on %(date)s.",
                    date=valid_to))
        return isds.Client(company.l10n_cz_isds_environment,
                           company.l10n_cz_isds_login,
                           company.l10n_cz_isds_password, auth=auth,
                           certificate=certificate)

    def action_l10n_cz_isds_test(self):
        """Sign in and record whose box the login opens."""
        self.ensure_one()
        try:
            owner = self._l10n_cz_isds_client().owner()
        except isds.IsdsError as exc:
            raise UserError(str(exc)) from exc
        self.sudo().write({"l10n_cz_isds_box_id": owner["box"],
                           "l10n_cz_isds_box_name": owner["name"]})
        return {"type": "ir.actions.client", "tag": "display_notification",
                "params": {"type": "success", "sticky": False,
                           "message": self.env._(
                               "Signed in to data box %(box)s (%(name)s).",
                               box=owner["box"], name=owner["name"])}}
