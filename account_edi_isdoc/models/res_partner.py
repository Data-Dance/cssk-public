from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    invoice_edi_format = fields.Selection(
        selection_add=[
            ('isdoc', "Czech Republic (ISDOC)"),
        ],
    )

    @api.model
    def _get_ubl_cii_formats_info(self):
        # EXTENDS account_edi_ubl_cii — ISDOC is selectable for any partner.
        # 'countries' feeds the suggested format; the tie with ubl_bis3 at
        # sequence 200 is settled by _get_suggested_ubl_cii_edi_format below.
        return {
            **super()._get_ubl_cii_formats_info(),
            'isdoc': {'countries': ['CZ'], 'on_peppol': False, 'sequence': 200},
        }

    def _get_suggested_ubl_cii_edi_format(self):
        """ISDOC for a Czech customer, unless it is known to be on Peppol.

        ISDOC is what Czech accounting software imports from an e-mailed
        invoice; Peppol BIS 3 only helps a customer that receives through
        Peppol. "Known to be on Peppol" is what the installed Peppol modules
        can tell: Odoo's participant check (account_peppol) found the partner,
        or the partner's sending method is Peppol (account_peppol or
        edi_base_peppol). A format
        chosen on the partner always wins over the suggestion.
        """
        suggested = super()._get_suggested_ubl_cii_edi_format()
        partner = self.commercial_partner_id
        if (
            suggested == 'ubl_bis3'
            and partner._deduce_country_code() == 'CZ'
            and not partner._isdoc_partner_is_on_peppol()
        ):
            return 'isdoc'
        return suggested

    def _isdoc_partner_is_on_peppol(self):
        self.ensure_one()
        if (
            'peppol_verification_state' in self._fields
            and self.peppol_verification_state == 'valid'
        ):
            return True
        # 'peppol' is Odoo's own Peppol service, 'edi_peppol' ours.
        return (
            'invoice_sending_method' in self._fields
            and self.invoice_sending_method in ('peppol', 'edi_peppol')
        )

    @api.model
    def _get_edi_builder(self, invoice_edi_format):
        if invoice_edi_format == 'isdoc':
            return self.env['account.edi.xml.isdoc']
        return super()._get_edi_builder(invoice_edi_format)
