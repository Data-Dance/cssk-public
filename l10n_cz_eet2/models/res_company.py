# -*- coding: utf-8 -*-
import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

EIC_RE = re.compile(r"^CZ[0-9]{8,10}$")
# § 19 odst. 2 ZoET: the taxpayer sets the response-time limit, at least 2 seconds.
MIN_RESPONSE_TIMEOUT = 2.0
DEFAULT_RESPONSE_TIMEOUT = 5.0


def check_id_jednotky(value, label):
    """Validate an evidence-unit number against the DIS+ shape.

    The XSD allows 1..999999999; the permissive check in the interface
    description (§ 2.2.4 item 5) additionally wants at least two decimal digits
    with the last one in {1, 2, 3, 4} — anything else is accepted by the
    gateway with warning 6 on every single message.  Zero/empty means "not
    set" and is left to the caller.
    """
    if not value:
        return
    if not (1 <= value <= 999999999) or value < 10 or value % 10 not in (1, 2, 3, 4):
        raise ValidationError(_(
            "%(label)s %(value)s is not a valid EET 2.0 evidence-unit number: "
            "DIS+ assigns numbers of 2 to 9 digits ending in 1, 2, 3 or 4.",
            label=label, value=value))


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_cz_eet2_enabled = fields.Boolean(string="EET 2.0 Enabled")
    l10n_cz_eet2_environment = fields.Selection(
        [("playground", "Playground (non-production)"),
        ("production", "Production")],
        string="EET 2.0 Environment", default="playground")
    l10n_cz_eet2_eic_popl = fields.Char(
        string="EET 2.0 Taxpayer EIC",
        compute="_compute_l10n_cz_eet2_eic_popl", store=True, readonly=False,
        help="Registration identification number (EIČ), format CZ + 8-10 digits. "
            "§ 18 ZoET: the EIČ is the taxpayer's DIČ, so it is pre-filled from "
            "the company VAT number when that already has the right shape.")
    l10n_cz_eet2_id_jednotky = fields.Integer(
        string="EET 2.0 Default Unit ID (id_jednotky)",
        help="Registrating-unit id from the MOJE daně / DIS+ portal.")
    l10n_cz_eet2_certificate_id = fields.Many2one(
        "l10n.cz.eet2.certificate", string="EET 2.0 Certificate",
        domain="[('company_id', '=', id)]")
    l10n_cz_eet2_max_attempts = fields.Integer(
        string="EET 2.0 Warn After Attempts", default=12,
        help="After this many failed send attempts the scheduled job logs a "
            "warning. It never stops retrying: § 20 ZoET keeps the duty to send "
            "alive until the message is accepted.")
    l10n_cz_eet2_response_timeout = fields.Float(
        string="EET 2.0 Response Time Limit (s)", default=DEFAULT_RESPONSE_TIMEOUT,
        help="Mezní doba odezvy (§ 19 ZoET): how long the till waits for the POK "
            "before letting the sale through and leaving the message to the "
            "scheduled retry. At least 2 seconds.")
    l10n_cz_eet2_renew_days_before = fields.Integer(
        string="EET 2.0 Renew Certificate (days before expiry)", default=30,
        help="The scheduled job asks CA EET 2.0 for a follow-up certificate this "
            "many days before the company's certificate expires, verifies the "
            "new one against the gateway and switches to it. 0 switches "
            "automatic renewal off.")

    @api.depends("vat")
    def _compute_l10n_cz_eet2_eic_popl(self):
        for company in self:
            if company.l10n_cz_eet2_eic_popl:
                continue
            vat = (company.vat or "").replace(" ", "").upper()
            company.l10n_cz_eet2_eic_popl = vat if EIC_RE.match(vat) else False

    @api.constrains("l10n_cz_eet2_eic_popl")
    def _check_l10n_cz_eet2_eic_popl(self):
        for company in self:
            eic = company.l10n_cz_eet2_eic_popl
            if eic and not EIC_RE.match(eic):
                raise ValidationError(_(
                    "EET 2.0 Taxpayer EIC %s must be 'CZ' followed by 8 to 10 digits "
                    "(the gateway rejects every message with error 6 otherwise).", eic))

    @api.constrains("l10n_cz_eet2_id_jednotky")
    def _check_l10n_cz_eet2_id_jednotky(self):
        for company in self:
            check_id_jednotky(company.l10n_cz_eet2_id_jednotky,
                            _("EET 2.0 Default Unit ID"))

    @api.constrains("l10n_cz_eet2_renew_days_before")
    def _check_l10n_cz_eet2_renew_days_before(self):
        for company in self:
            if company.l10n_cz_eet2_renew_days_before < 0:
                raise ValidationError(_(
                    "The number of days before expiry at which EET 2.0 certificates "
                    "are renewed cannot be negative (0 disables automatic renewal)."))

    @api.constrains("l10n_cz_eet2_response_timeout")
    def _check_l10n_cz_eet2_response_timeout(self):
        for company in self:
            if company.l10n_cz_eet2_response_timeout < MIN_RESPONSE_TIMEOUT:
                raise ValidationError(_(
                    "The EET 2.0 response time limit must be at least %s seconds "
                    "(§ 19 ZoET).", MIN_RESPONSE_TIMEOUT))

    def write(self, vals):
        res = super().write(vals)
        if vals.get("l10n_cz_eet2_certificate_id"):
            # A new certificate is the usual cure for messages that could not be
            # built or were rejected for a bad signature: give them another go.
            self.env["l10n.cz.eet2.transaction"].sudo().search([
                ("company_id", "in", self.ids),
                ("state", "in", ("error", "rejected")),
            ]).action_requeue()
        return res
