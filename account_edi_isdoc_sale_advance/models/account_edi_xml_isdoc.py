import re

from odoo import models
from odoo.addons.account_edi_isdoc.models.account_edi_xml_isdoc import ISDOC_DOCUMENT_TYPE


class AccountEdiXmlISDOC(models.AbstractModel):
    _inherit = 'account.edi.xml.isdoc'

    def _get_document_type_code(self, invoice):
        # daňový doklad k přijaté platbě = tax document for a received advance (with VAT).
        if invoice.is_advance_invoice_tax_document:
            is_refund = invoice.move_type in ('out_refund', 'in_refund')
            return ISDOC_DOCUMENT_TYPE['advance_credit'] if is_refund else ISDOC_DOCUMENT_TYPE['advance']
        return super()._get_document_type_code(invoice)

    def _isdoc_deduction_lines(self, product_lines):
        # EXTENDS core: a Czech settlement invoice deducts advances through tracking lines
        # (is_advance_tracking) rather than generic is_downpayment lines.
        lines = super()._isdoc_deduction_lines(product_lines)
        lines |= product_lines.filtered(lambda l: l.sale_line_ids.filtered('is_advance_tracking'))
        return lines

    def _isdoc_deposit_source(self, line):
        # Resolve the advance's identity from its tax document (daňový doklad k přijaté platbě),
        # falling back to the advance order (zálohová faktura) if no tax document is posted yet.
        tracking = line.sale_line_ids.filtered('is_advance_tracking')
        advance = tracking.advance_source_order_id[:1]
        if not advance:
            return super()._isdoc_deposit_source(line)
        tax_docs = advance.invoice_ids.filtered(
            lambda m: m.move_type in ('out_invoice', 'out_refund') and m.state == 'posted')
        source = tax_docs[:1] or advance
        doc_id = source.name
        var_symbol = source.variable_symbol if 'variable_symbol' in source._fields else ''
        return doc_id, (var_symbol or re.sub(r'\D', '', doc_id or '') or '0')
