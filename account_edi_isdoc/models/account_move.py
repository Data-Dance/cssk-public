from lxml import etree

from odoo import fields, models

ISDOC_NS = "http://isdoc.cz/namespace/2013"
# ISDOC namespaces across versions: ".../invoice" (1.x-5.x) and ".../2013" (6.x). Imports are
# accepted from any of them — the element structure is stable — while exports stay 6.0.2.
ISDOC_NS_PREFIX = "http://isdoc.cz/namespace"


class AccountMove(models.Model):
    _inherit = 'account.move'

    # ISDOC mandates a document <UUID>. We persist the one we generate on export and
    # the one we read on import so the value round-trips and stays stable across re-exports.
    isdoc_uuid = fields.Char(string="ISDOC UUID", copy=False)

    def _get_edi_decoder(self, file_data, new=False):
        """ Route ISDOC files to our builder.

        18.0 port: 19.0 dispatched on ``file_data['import_file_type']`` and returned a
        ``{'priority', 'decoder'}`` dict. On 18.0 the file-data pipeline lives on
        ``ir.attachment`` (``_unwrap_edi_attachments`` / ``_get_edi_supported_formats``),
        the file-data schema exposes ``type``/``xml_tree`` (no ``import_file_type``), and
        ``_get_edi_decoder`` returns the decoder *callable* directly. We therefore detect
        ISDOC by inspecting the parsed XML root (flat ``<Invoice>`` in any ISDOC namespace).
        The bare-``.isdoc`` and ``.isdocx`` recognition/unwrapping is handled by our
        ``ir.attachment`` override.
        """
        # EXTENDS account
        if file_data.get('type') == 'xml' and file_data.get('xml_tree') is not None:
            qname = etree.QName(file_data['xml_tree'])
            if qname.localname == 'Invoice' and (qname.namespace or '').startswith(ISDOC_NS_PREFIX):
                return self.env['account.edi.xml.isdoc']._import_invoice_ubl_cii
        return super()._get_edi_decoder(file_data, new=new)
