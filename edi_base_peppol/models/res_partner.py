"""The contact's invoice delivery channel, with the e-invoice as one option.

Odoo's ``invoice_sending_method`` is the channel the Send & Print wizard uses.
It gains ``edi_peppol``: an e-invoice through the Peppol access point of an
installed EDI provider (GRiT, Editel, ePošťák). The key is not ``peppol``,
which Odoo's own ``account_peppol`` (Peppol through Odoo's IAP service) adds to
the same field; the two must never be confused, or one invoice could leave
through two access points.

An explicit choice on the contact wins (``account.move._peppol_route``).
Choosing email for a business the Slovak mandate covers is allowed, since
there are exceptions, but the contact says what it means.
"""

from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    invoice_sending_method = fields.Selection(
        selection_add=[("edi_peppol", "by e-invoice (Peppol)")],
    )
    peppol_sending_warning = fields.Char(compute="_compute_peppol_sending_warning")

    def _peppol_is_sk_business(self):
        """Whether the Slovak mandate counts this contact as a business.

        § 85o ods. 3 of the VAT Act (from 1. 1. 2027): a *taxable person*
        established in Slovakia — any business, VAT-registered or not, a
        sole trader included — or a non-taxable legal person. Odoo has no
        field for "taxable person", so any business identifier stands for
        it: a company, a VAT number, an IČO (company ID) or a DIČ. Only a
        contact with none of them is taken for a consumer.
        """
        partner = self.commercial_partner_id
        return bool(
            partner.is_company
            or partner.vat
            or partner.company_registry
            or ("l10n_sk_dic" in partner._fields and partner.l10n_sk_dic)
        )

    @api.depends_context("company")
    @api.depends("invoice_sending_method", "country_id", "is_company", "vat",
                 "company_registry")
    def _compute_peppol_sending_warning(self):
        company = self.env.company.sudo()
        mandate = (company.peppol_send_enabled and company.peppol_scope == "sk_mandate"
                   and company.account_fiscal_country_id.code == "SK")
        for partner in self:
            commercial = partner.commercial_partner_id
            in_mandate = (mandate and commercial.country_id.code == "SK"
                          and commercial._peppol_is_sk_business())
            method = partner.invoice_sending_method
            partner.peppol_sending_warning = _(
                "This customer is a Slovak business: from 1. 1. 2027 its invoices "
                "must be e-invoices, so sending them by email does not meet the "
                "mandate."
            ) if in_mandate and method and method != "edi_peppol" else False
