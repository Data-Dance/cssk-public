# -*- coding: utf-8 -*-
import re

from odoo import models


class AccountEdiXmlUbl_Sk(models.AbstractModel):
    """Slovak flavour of Peppol BIS Billing 3.0.

    Slovakia has no national billing CIUS, so this builder is a near-empty
    subclass of the generic Peppol builder: the emitted XML (CustomizationID,
    ProfileID, party identification via EAS_MAPPING['SK'], VAT, IBAN, reverse
    charge) is already conformant. This class exists as a stable extension
    point and adds only the Slovak *variabilný symbol* convention.
    """
    _name = 'account.edi.xml.ubl_sk'
    _inherit = 'account.edi.xml.ubl_bis3'
    _description = "SK Peppol BIS Billing 3.0"

    def _export_invoice_filename(self, invoice):
        # OVERRIDE 'account.edi.xml.ubl_bis3'
        return f"{invoice.name.replace('/', '_')}_ubl_bis3_sk.xml"

    # NOTE: We deliberately do NOT override _get_customization_id /
    # _ubl_add_customization_id_node: Slovakia uses the plain Peppol BIS
    # Billing 3.0 CustomizationID, with no national CIUS deviation.

    # -------------------------------------------------------------------------
    # Slovak variabilný symbol (VS) -> cbc:PaymentID (BT-83)
    # -------------------------------------------------------------------------

    def _l10n_sk_get_variable_symbol(self, invoice):
        """Slovak VS: up to 10 digits used by banks to match incoming payments.

        A VS is numeric only, so normalise the source (the canonical
        l10n_cssk_payment_symbols field when installed, else an explicit
        payment_reference, otherwise the invoice number) to digits and
        keep the last 10. Falls back to the raw source if it has no digits.
        """
        source = ''
        if 'l10n_cssk_variable_symbol' in invoice._fields:
            source = invoice.l10n_cssk_variable_symbol or ''
        source = source or invoice.payment_reference or invoice.name or ''
        digits = re.sub(r'\D', '', source)
        return digits[-10:] if digits else source

    def _ubl_add_payment_means_nodes(self, vals):
        # EXTENDS 'account.edi.xml.ubl_bis3'
        super()._ubl_add_payment_means_nodes(vals)
        invoice = vals.get('invoice')
        if not invoice:
            return
        variable_symbol = self._l10n_sk_get_variable_symbol(invoice)
        for node in vals['document_node']['cac:PaymentMeans']:
            payment_id = node.get('cbc:PaymentID')
            if payment_id is not None:
                payment_id['_text'] = variable_symbol
