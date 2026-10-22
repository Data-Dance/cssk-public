import io
import zipfile

from odoo import models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def _get_edi_supported_formats(self):
        """ Teach the 18.0 EDI attachment pipeline about ISDOC.

        18.0 port: on 19.0 the module overrode ``account.move._get_import_file_type`` /
        ``_get_xml_tree`` / ``_unwrap_attachment``. On 18.0 the attachment decode/unwrap
        pipeline is driven by ``ir.attachment._get_edi_supported_formats()`` (a list of
        ``{format, check, decoder}`` probed in order, first match wins). We prepend two
        handlers so they take precedence over the generic xml/binary catch-alls:

        * ``isdocx`` — a ZIP holding an ``.isdoc`` (+ manifest + PDF); we extract the
          inner ISDOC XML and any PDF members into their own file-data entries.
        * ``isdoc``  — a bare ``.isdoc`` XML whose mimetype is often *not* ``*/xml``
          (e.g. ``application/octet-stream`` when emailed/uploaded), which the core
          ``is_xml`` probe would otherwise skip.

        ISDOC embedded inside a PDF/A-3 needs no special handling: the core
        ``_decode_edi_pdf`` already extracts embedded XML attachments and parses them,
        so ``account.move._get_edi_decoder`` recognises them by namespace.
        """
        formats = super()._get_edi_supported_formats()
        isdoc_formats = [
            {
                'format': 'isdocx',
                'check': self._is_isdocx,
                'decoder': self._decode_isdocx,
            },
            {
                'format': 'isdoc',
                'check': self._is_isdoc_xml,
                'decoder': self._decode_edi_xml,  # reuse the core XML decoder
            },
        ]
        return isdoc_formats + formats

    def _is_isdocx(self, attachment):
        raw = attachment.raw or b''
        if raw[:2] != b'PK':  # not a ZIP
            return False
        try:
            names = zipfile.ZipFile(io.BytesIO(raw)).namelist()
        except zipfile.BadZipFile:
            return False
        return any(n.lower().endswith('.isdoc') for n in names)

    def _is_isdoc_xml(self, attachment):
        name = (attachment.name or '').lower()
        if name.endswith('.isdoc'):
            return True
        raw = attachment.raw or b''
        return raw[:200].lstrip().startswith(b'<?xml') and b'isdoc.cz/namespace' in raw[:2000]

    def _decode_isdocx(self, filename, content):
        """ Unwrap an ``.isdocx`` archive into file-data entries (inner ISDOC + PDFs). """
        try:
            archive = zipfile.ZipFile(io.BytesIO(content))
            names = archive.namelist()
        except zipfile.BadZipFile:
            return []
        to_process = []
        for name in names:
            low = name.lower()
            base = name.split('/')[-1]
            member = archive.read(name)
            if low.endswith('.isdoc'):
                to_process += self._decode_edi_xml(base, member)
            elif low.endswith('.pdf'):
                to_process += self._decode_edi_pdf(base, member)
        return to_process
