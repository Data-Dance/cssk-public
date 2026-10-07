import io
import zipfile

from lxml import etree

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
from odoo.tools import file_open

ISDOC_NS = "http://isdoc.cz/namespace/2013"
ISDOC_MANIFEST_NS = "http://isdoc.cz/namespace/2013/manifest"


@tagged('post_install', '-at_install')
class TestISDOCContainers(AccountTestInvoicingCommon):

    @classmethod
    def _create_company(cls, **create_values):
        create_values.setdefault('currency_id', cls.env.ref('base.CZK').id)
        company = super()._create_company(**create_values)
        company.country_id = cls.env.ref('base.cz')
        company.tax_calculation_rounding_method = 'round_globally'  # Czech VAT is rounded globally
        return company

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data['company']
        cls.purchase_journal = cls.company_data['default_journal_purchase']
        for rate in (12.0, 21.0):
            cls.env['account.tax'].create({
                'name': f"DPH {rate:.0f}% (nákup)", 'amount': rate, 'amount_type': 'percent',
                'type_tax_use': 'purchase', 'company_id': cls.company.id,
            })
        cls.cz_customer = cls.env['res.partner'].create({
            'name': "Zákazník s.r.o.", 'street': "Hlavní 1", 'zip': "11000", 'city': "Praha",
            'vat': 'CZ25663585', 'country_id': cls.env.ref('base.cz').id,
            'invoice_edi_format': 'isdoc',
        })
        cls.company.partner_id.write({
            'street': "Příhon 943", 'zip': "696 15", 'city': "Čejkovice",
            'vat': 'CZ46342958', 'company_registry': '46342958',
        })
        with file_open('account_edi_isdoc/tests/schema/isdoc-invoice-6.0.2.xsd', 'rb') as f:
            cls.invoice_schema = etree.XMLSchema(etree.parse(f))

    # ----- Export pipeline wiring -----

    def test_isdoc_registered_and_engages_pipeline(self):
        self.assertIn('isdoc', self.env['res.partner']._get_ubl_cii_formats())
        invoice = self.init_invoice(
            'out_invoice', partner=self.cz_customer, invoice_date='2024-07-10',
            amounts=[100.0], taxes=self.company_data['default_tax_sale'], post=True)
        self.assertTrue(invoice._need_ubl_cii_xml('isdoc'))

    def test_isdoc_skips_ubl_postprocessing(self):
        send = self.env['account.move.send']
        # ISDOC must NOT go through the UBL AdditionalDocumentReference postprocessing.
        self.assertFalse(send._needs_ubl_postprocessing(
            {'ubl_cii_xml_options': {'ubl_cii_format': 'isdoc'}}))
        # ... but a UBL format still does.
        self.assertTrue(send._needs_ubl_postprocessing(
            {'ubl_cii_xml_options': {'ubl_cii_format': 'ubl_bis3'}}))

    # ----- Container import -----

    def _new_bill(self):
        return self.env['account.move'].with_company(self.company).create({
            'move_type': 'in_invoice', 'journal_id': self.purchase_journal.id})

    def test_get_xml_tree_parses_bare_isdoc(self):
        # A .isdoc uploaded with a non-xml mimetype must still be recognised.
        with file_open('account_edi_isdoc/tests/test_files/import/doklad.isdoc', 'rb') as f:
            raw = f.read()
        attachment = self.env['ir.attachment'].create({
            'name': 'invoice.isdoc', 'raw': raw, 'mimetype': 'application/octet-stream'})
        file_data = self.env['account.move']._to_files_data(attachment)[0]
        self.assertIsNotNone(file_data['xml_tree'])
        self.assertEqual(file_data['import_file_type'], 'account.edi.xml.isdoc')

    def test_import_isdocx_archive(self):
        # Official .isdocx (doklad + attachments + nested old docs). Unwrap finds the ISDOC
        # and decodes it (the inner doklad is the ISDOC 5.1 ABRA demo).
        with file_open('account_edi_isdoc/tests/test_files/import/doklad_s_prilohami.isdocx', 'rb') as f:
            raw = f.read()
        attachment = self.env['ir.attachment'].create({
            'name': 'doklad_s_prilohami.isdocx', 'raw': raw, 'mimetype': 'application/zip'})
        bill = self._new_bill()
        files_data = bill._to_files_data(attachment)
        files_data += bill._unwrap_attachments(files_data)
        isdoc_fd = next(fd for fd in files_data if fd.get('import_file_type') == 'account.edi.xml.isdoc')
        self.assertIsNotNone(isdoc_fd['xml_tree'])

        bill._get_edi_decoder(isdoc_fd)['decoder'](bill, isdoc_fd)
        self.assertEqual(bill.partner_id.name, "ABRA Software a.s.")
        self.assertEqual(bill.ref, 'FV-111999/2008')
        self.assertGreater(len(bill.invoice_line_ids.filtered(lambda l: l.display_type == 'product')), 3)

    # ----- Export container forms -----

    def test_export_isdocx_archive(self):
        invoice = self.init_invoice(
            'out_invoice', partner=self.cz_customer, invoice_date='2024-07-10',
            amounts=[100.0, 200.0], taxes=self.company_data['default_tax_sale'], post=True)
        raw, errors = self.env['account.edi.xml.isdoc']._export_invoice_isdocx(invoice, pdf=b'%PDF-1.4 test')
        self.assertFalse(errors)

        archive = zipfile.ZipFile(io.BytesIO(raw))
        names = archive.namelist()
        self.assertIn('manifest.xml', names)
        isdoc_name = next(n for n in names if n.endswith('.isdoc'))
        self.assertTrue(any(n.endswith('.pdf') for n in names))
        # Inner ISDOC is schema-valid.
        self.invoice_schema.assertValid(etree.fromstring(archive.read(isdoc_name)))
        # Manifest points at the ISDOC.
        manifest = etree.fromstring(archive.read('manifest.xml'))
        main = manifest.find(f'{{{ISDOC_MANIFEST_NS}}}maindocument')
        self.assertEqual(main.get('filename'), isdoc_name)
        # The archive round-trips through our importer's unwrap.
        attachment = self.env['ir.attachment'].create({
            'name': 'invoice.isdocx', 'raw': raw, 'mimetype': 'application/zip'})
        files_data = self._new_bill()._unwrap_attachments(
            self.env['account.move']._to_files_data(attachment))
        self.assertTrue(any(fd.get('import_file_type') == 'account.edi.xml.isdoc' for fd in files_data))

    def test_embed_isdoc_in_pdf_roundtrips(self):
        # Take a real PDF + ISDOC from the official archive, embed, then re-detect on import.
        with file_open('account_edi_isdoc/tests/test_files/import/doklad_s_prilohami.isdocx', 'rb') as f:
            archive = zipfile.ZipFile(io.BytesIO(f.read()))
        pdf = archive.read(next(n for n in archive.namelist() if n.lower().endswith('.pdf')))
        isdoc_xml = archive.read(next(n for n in archive.namelist() if n.lower().endswith('.isdoc')))

        new_pdf = self.env['account.move.send']._isdoc_embed_in_pdf(pdf, isdoc_xml, 'invoice.isdoc')

        attachment = self.env['ir.attachment'].create({
            'name': 'invoice.pdf', 'raw': new_pdf, 'mimetype': 'application/pdf'})
        bill = self._new_bill()
        files_data = bill._to_files_data(attachment)
        files_data += bill._unwrap_attachments(files_data)
        isdoc_fd = next((fd for fd in files_data if fd.get('import_file_type') == 'account.edi.xml.isdoc'), None)
        self.assertIsNotNone(isdoc_fd, "Embedded ISDOC not found back in the PDF")
        self.assertTrue((etree.QName(isdoc_fd['xml_tree']).namespace or '').startswith('http://isdoc.cz/namespace'))
