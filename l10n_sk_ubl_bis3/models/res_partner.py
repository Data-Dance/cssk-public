# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    invoice_edi_format = fields.Selection(
        selection_add=[('ubl_bis3_sk', "Slovakia (Peppol BIS 3.0)")],
    )

    def _get_edi_builder(self, invoice_edi_format):
        # EXTENDS 'account_edi_ubl_cii'
        if invoice_edi_format == 'ubl_bis3_sk':
            return self.env['account.edi.xml.ubl_sk']
        return super()._get_edi_builder(invoice_edi_format)

    def _get_ubl_cii_formats_info(self):
        # EXTENDS 'account_edi_ubl_cii'
        # SK is intentionally absent from Odoo core's PEPPOL_DEFAULT_COUNTRIES,
        # so the generic 'ubl_bis3' is not offered for Slovak partners. Register
        # our SK entry as the single format for SK -> it becomes the auto-suggested
        # one (see account_edi_ubl_cii res.partner._get_suggested_ubl_cii_edi_format).
        formats_info = super()._get_ubl_cii_formats_info()
        formats_info['ubl_bis3_sk'] = {
            'countries': ['SK'],
            'on_peppol': True,
            'sequence': 200,
            'embed_attachments': True,
        }
        return formats_info

    def _get_suggested_invoice_edi_format(self):
        # EXTENDS 'account' - auto-default the stored field for Slovak partners.
        if self.country_code == 'SK':
            return 'ubl_bis3_sk'
        return super()._get_suggested_invoice_edi_format()
