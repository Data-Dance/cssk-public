import io
import logging

from odoo import api, models, tools
from odoo.tools.pdf import OdooPdfFileReader, OdooPdfFileWriter

_logger = logging.getLogger(__name__)


class AccountMoveSend(models.AbstractModel):
    _inherit = 'account.move.send'

    @api.model
    def _needs_ubl_postprocessing(self, invoice_data):
        # EXTENDS account_edi_ubl_cii
        # ISDOC is not UBL: it has no <AdditionalDocumentReference> element and uses a single
        # default namespace, so the UBL PDF-embedding postprocessing would corrupt it.
        if invoice_data.get('ubl_cii_xml_options', {}).get('ubl_cii_format') == 'isdoc':
            return False
        return super()._needs_ubl_postprocessing(invoice_data)

    def _hook_invoice_document_after_pdf_report_render(self, invoice, invoice_data):
        # EXTENDS account_edi_ubl_cii
        # For ISDOC, embed the ISDOC XML into the invoice PDF (the "ISDOC.PDF" / PDF-A3
        # representation) instead of running the UBL postprocessing + Factur-X embedding.
        if invoice_data.get('ubl_cii_xml_options', {}).get('ubl_cii_format') == 'isdoc':
            attachment_values = invoice_data.get('ubl_cii_xml_attachment_values')
            if tools.config['test_enable'] or not attachment_values:
                return
            pdf_values = (
                invoice.invoice_pdf_report_id
                or invoice_data.get('pdf_attachment_values')
                or invoice_data.get('proforma_pdf_attachment_values')
            )
            if pdf_values:
                pdf_values['raw'] = self._isdoc_embed_in_pdf(
                    pdf_values['raw'], attachment_values['raw'], attachment_values['name'])
            return
        super()._hook_invoice_document_after_pdf_report_render(invoice, invoice_data)

    def _isdoc_embed_in_pdf(self, pdf_bytes, isdoc_xml, filename):
        """ Embed the ISDOC XML into the PDF as an attachment and convert to PDF/A-3. """
        reader = OdooPdfFileReader(io.BytesIO(pdf_bytes), strict=False)
        writer = OdooPdfFileWriter()
        writer.cloneReaderDocumentRoot(reader)
        writer.addAttachment(filename, isdoc_xml, subtype='text/xml')
        try:
            if not writer.is_pdfa:
                writer.convert_to_pdfa()
        except Exception:  # noqa: BLE001 — embedding already succeeded; PDF/A is best-effort
            _logger.exception("ISDOC: PDF/A-3 conversion failed; the XML is still embedded")
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()
