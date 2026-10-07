import io
import zipfile

from lxml import etree

from odoo import fields, models
from odoo.tools.mimetypes import guess_mimetype

ISDOC_NS = "http://isdoc.cz/namespace/2013"
# ISDOC namespaces across versions: ".../invoice" (1.x-5.x) and ".../2013" (6.x). Imports are
# accepted from any of them — the element structure is stable — while exports stay 6.0.2.
ISDOC_NS_PREFIX = "http://isdoc.cz/namespace"


class AccountMove(models.Model):
    _inherit = 'account.move'

    # ISDOC mandates a document <UUID>. We persist the one we generate on export and
    # the one we read on import so the value round-trips and stays stable across re-exports.
    isdoc_uuid = fields.Char(string="ISDOC UUID", copy=False)

    def _get_import_file_type(self, file_data):
        """ Identify ISDOC invoice files (flat <Invoice> root in any ISDOC namespace). """
        # EXTENDS account_edi_ubl_cii
        if (tree := file_data['xml_tree']) is not None:
            qname = etree.QName(tree)
            if qname.localname == 'Invoice' and (qname.namespace or '').startswith(ISDOC_NS_PREFIX):
                return 'account.edi.xml.isdoc'
        return super()._get_import_file_type(file_data)

    def _get_edi_decoder(self, file_data, new=False):
        """ Route ISDOC files to our builder.

        The base implementation only dispatches models that inherit
        ``account.edi.xml.ubl_20`` or ``account.edi.xml.cii``. Our builder inherits
        ``account.edi.common`` directly, so it must be wired here explicitly.
        """
        # EXTENDS account_edi_ubl_cii
        if file_data['import_file_type'] == 'account.edi.xml.isdoc':
            return {
                'priority': 20,
                'decoder': self.env['account.edi.xml.isdoc']._import_invoice_ubl_cii,
            }
        return super()._get_edi_decoder(file_data, new)

    def _get_xml_tree(self, file_data):
        """ Also parse bare ``.isdoc`` files: their mimetype is often not ``*/xml`` (e.g.
        ``application/octet-stream`` when uploaded/emailed), so the base parser skips them. """
        tree = super()._get_xml_tree(file_data)
        if tree is not None:
            return tree
        raw = file_data.get('raw') or b''
        name = (file_data.get('name') or '').lower()
        looks_isdoc = name.endswith('.isdoc') or (
            raw[:200].lstrip().startswith(b'<?xml') and b'isdoc.cz/namespace' in raw[:2000]
        )
        if raw and looks_isdoc:
            try:
                return etree.fromstring(raw, parser=etree.XMLParser(remove_comments=True, resolve_entities=False))
            except etree.XMLSyntaxError:
                return None
        return tree

    def _unwrap_attachment(self, file_data, recurse=True):
        """ Unwrap an ``.isdocx`` archive (ZIP holding the ISDOC XML + manifest + PDF). """
        # EXTENDS account_edi_ubl_cii
        embedded = self._unwrap_isdocx(file_data)
        if embedded:
            if recurse:
                embedded.extend(self._unwrap_attachments(embedded))
            return embedded
        return super()._unwrap_attachment(file_data, recurse)

    def _unwrap_isdocx(self, file_data):
        raw = file_data.get('raw') or b''
        if raw[:2] != b'PK':  # not a ZIP
            return []
        try:
            archive = zipfile.ZipFile(io.BytesIO(raw))
            names = archive.namelist()
        except zipfile.BadZipFile:
            return []
        members = [n for n in names if n.lower().endswith('.isdoc')]
        if not members:  # not an ISDOC archive
            return []
        members += [n for n in names if n.lower().endswith('.pdf')]
        embedded = []
        for member in members:
            content = archive.read(member)
            embedded_file_data = {
                'name': member.split('/')[-1],
                'raw': content,
                'mimetype': guess_mimetype(content),
                'attachment': None,
                'origin_attachment': file_data.get('origin_attachment'),
                'origin_import_file_type': file_data.get('origin_import_file_type'),
            }
            embedded_file_data['xml_tree'] = self._get_xml_tree(embedded_file_data)
            embedded_file_data['import_file_type'] = self._get_import_file_type(embedded_file_data)
            embedded.append(embedded_file_data)
        return embedded
