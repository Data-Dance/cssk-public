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
        # EXTENDS account_edi_ubl_cii — offer ISDOC for Czech companies.
        return {
            **super()._get_ubl_cii_formats_info(),
            'isdoc': {'countries': ['CZ'], 'on_peppol': False, 'sequence': 200},
        }

    @api.model
    def _get_edi_builder(self, invoice_edi_format):
        if invoice_edi_format == 'isdoc':
            return self.env['account.edi.xml.isdoc']
        return super()._get_edi_builder(invoice_edi_format)
