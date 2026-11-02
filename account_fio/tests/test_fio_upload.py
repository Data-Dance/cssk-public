# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""The transport half of sending a payment file, independent of who built it."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import FioCommon

PAIN001 = (
    b'<?xml version="1.0"?>'
    b'<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">'
    b"<CstmrCdtTrfInitn/></Document>"
)
PAIN008 = (
    b'<?xml version="1.0"?>'
    b'<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.008.001.02">'
    b"<CstmrDrctDbtInitn/></Document>"
)
FIO_XML = b'<?xml version="1.0"?><Import><Orders/></Import>'
ABO = b"UHL1010426FIRMA               2111111111\n"


@tagged("post_install", "-at_install")
class TestFioUploadSniffer(FioCommon):
    """One button, several exporters.

    Fio accepts its own XML, pain.001, pain.008 and ABO, so the upload works
    out what it is holding instead of each exporter having to say — which is
    what makes ``account_abo`` and the SEPA exporters sendable to Fio without a
    line of new format code.
    """

    def setUp(self):
        super().setUp()
        self.mixin = self.env["fio.upload.mixin"]

    def test_fio_xml(self):
        self.assertEqual(self.mixin._fio_sniff_type(FIO_XML), "xml")

    def test_pain001(self):
        self.assertEqual(self.mixin._fio_sniff_type(PAIN001), "pain001_xml")

    def test_pain008(self):
        self.assertEqual(self.mixin._fio_sniff_type(PAIN008), "pain008_xml")

    def test_abo(self):
        self.assertEqual(self.mixin._fio_sniff_type(ABO), "abo")

    def test_unknown_xml_is_refused_rather_than_guessed(self):
        with self.assertRaises(UserError) as caught:
            self.mixin._fio_sniff_type(b"<CustomExport><x/></CustomExport>")
        self.assertIn("CustomExport", str(caught.exception))

    def test_garbage_is_refused(self):
        with self.assertRaises(UserError):
            self.mixin._fio_sniff_type(b"not a payment file at all")

    def test_broken_xml_is_refused(self):
        with self.assertRaises(UserError):
            self.mixin._fio_sniff_type(b"<Import><Orders>")


@tagged("post_install", "-at_install")
class TestFioUploadPlumbing(FioCommon):
    """Everything around the request that is not the request itself."""

    def setUp(self):
        super().setUp()
        self.mixin = self.env["fio.upload.mixin"]

    def test_a_journal_without_a_submit_token_names_the_right_to_ask_for(self):
        """There is no connection record left to be missing — only a journal
        with no submit token, and the message has to say which Fio right to
        request rather than just refusing."""
        journal = self.env["account.journal"].sudo().create({
            "name": "Plain", "type": "bank", "code": "PLAIN",
            "company_id": self.company.id,
        })
        self.assertFalse(journal.fio_has_token_write)
        with self.assertRaises(UserError) as caught:
            journal._fio_token("write")
        self.assertIn("zadávání platebních", str(caught.exception))

    def test_the_bank_messages_are_rendered_per_order(self):
        from odoo.addons.account_fio_base.tests.fio_fixtures import import_response
        from odoo.addons.account_fio_base.utils.response import (
            parse_import_response,
        )

        result = parse_import_response(import_response(
            error_code=1, status="error",
            messages=[("error", 100, "Neplatné číslo účtu")],
        ))
        lines = self.mixin._fio_message_lines(result)
        self.assertEqual(len(lines), 1)
        self.assertIn("#1", lines[0])
        self.assertIn("error", lines[0])
        self.assertIn("Neplatné", lines[0])

    def test_the_accepted_summary_says_it_is_not_paid_yet(self):
        from odoo.addons.account_fio_base.tests.fio_fixtures import import_response
        from odoo.addons.account_fio_base.utils.response import (
            parse_import_response,
        )

        result = parse_import_response(import_response(id_instruction="4242"))
        body = self.mixin._fio_result_body(result)
        self.assertIn("4242", body)
        self.assertIn("authorised", body)
