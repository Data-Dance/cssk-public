"""Peppol addressing metadata derived from the UBL payload.

Everything ePošťák routes on is read out of the document rather than out of
Odoo records, because the API rejects a submission whose metadata disagrees
with the payload (``SAPI-DOC-025``). These tests pin that derivation for the
three document shapes that cross a Peppol access point.
"""

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
BIS3_CUSTOMIZATION = (
    "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0"
)
BIS3_PROFILE = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"
IR_CUSTOMIZATION = "urn:fdc:peppol.eu:poacc:trns:invoice_response:3"


def _invoice_ubl(kind="Invoice", doc_id="FA-2026-001"):
    namespace = "urn:oasis:names:specification:ubl:schema:xsd:%s-2" % kind
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<%(kind)s xmlns="%(ns)s" xmlns:cac="%(cac)s" xmlns:cbc="%(cbc)s">'
        "<cbc:CustomizationID>%(cust)s</cbc:CustomizationID>"
        "<cbc:ProfileID>%(prof)s</cbc:ProfileID>"
        "<cbc:ID>%(id)s</cbc:ID>"
        "<cbc:IssueDate>2026-07-01</cbc:IssueDate>"
        "<cac:AccountingSupplierParty><cac:Party>"
        '<cbc:EndpointID schemeID="0245">2121576435</cbc:EndpointID>'
        "</cac:Party></cac:AccountingSupplierParty>"
        "<cac:AccountingCustomerParty><cac:Party>"
        '<cbc:EndpointID schemeID="0208">0987654321</cbc:EndpointID>'
        "</cac:Party></cac:AccountingCustomerParty>"
        "</%(kind)s>"
    ) % {
        "kind": kind,
        "ns": namespace,
        "cac": CAC,
        "cbc": CBC,
        "cust": BIS3_CUSTOMIZATION,
        "prof": BIS3_PROFILE,
        "id": doc_id,
    }


def _application_response():
    namespace = (
        "urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2"
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<ApplicationResponse xmlns="%(ns)s" xmlns:cac="%(cac)s" '
        'xmlns:cbc="%(cbc)s">'
        "<cbc:CustomizationID>%(cust)s</cbc:CustomizationID>"
        "<cbc:ProfileID>urn:fdc:peppol.eu:poacc:bis:invoice_response:3"
        "</cbc:ProfileID>"
        "<cbc:ID>0f4b1f0e-1111-2222-3333-444455556666</cbc:ID>"
        "<cac:SenderParty>"
        '<cbc:EndpointID schemeID="0245">2121576435</cbc:EndpointID>'
        "</cac:SenderParty>"
        "<cac:ReceiverParty>"
        '<cbc:EndpointID schemeID="0208">0987654321</cbc:EndpointID>'
        "</cac:ReceiverParty>"
        "</ApplicationResponse>"
    ) % {"ns": namespace, "cac": CAC, "cbc": CBC, "cust": IR_CUSTOMIZATION}


class TestEpostakMetadata(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.connector = cls.env["epostak.connector"]

    # ------------------------------------------------------------------
    # Participant identifiers
    # ------------------------------------------------------------------

    def test_participant_join_and_normalise(self):
        self.assertEqual(
            self.connector._epostak_participant("0245", "2121576435"),
            "0245:2121576435",
        )
        # A half-configured partner must yield '' (= "not addressable")
        # rather than a malformed identifier the API would 403 on.
        self.assertEqual(self.connector._epostak_participant("0245", ""), "")
        self.assertEqual(self.connector._epostak_participant("", "2121576435"), "")
        # Inbound metadata echoes the ICD prefix; send wants it stripped.
        self.assertEqual(
            self.connector._epostak_normalize_participant(
                "iso6523-actorid-upis::0245:2121576435"
            ),
            "0245:2121576435",
        )

    def test_sk_participant_must_be_a_dic_not_an_ico(self):
        """0245 addresses the 10-digit DIČ; the 8-digit IČO is not routable.

        ePošťák answers an unknown participant with 400 SAPI-VAL-004 "Invalid
        participant ID" — indistinguishable from a malformed one — so the
        mix-up has to be named locally or it costs an afternoon.
        """
        complaint = self.connector._epostak_participant_complaint
        self.assertEqual(complaint("0245:4536197514"), "")
        # An IČO in the DIČ slot is the mistake worth naming explicitly.
        ico = complaint("0245:36197514")
        self.assertTrue(ico)
        self.assertIn("IČO", ico)
        # Padding it to ten digits does not make it a DIČ, but the shape check
        # can no longer tell — only the API can, and that is fine.
        self.assertEqual(complaint("0245:0036197514"), "")
        self.assertTrue(complaint("0245:453619751X"))
        self.assertTrue(complaint("0245:"))
        # Other schemes carry their own rules; we judge only what we know.
        self.assertEqual(complaint("0088:1234567890128"), "")
        self.assertEqual(complaint(""), "")

    def test_validate_config_rejects_an_ico_participant(self):
        """The refusal must name the address, not blame the credentials.

        Asserted on the message because a concrete connector adds its own
        credential checks on top; only the wording tells the two apart, and
        an install without keys must still fail for the right reason.
        """
        self.env.company.partner_id.write(
            {"peppol_eas": "0245", "peppol_endpoint": "36197514"}
        )
        with self.assertRaises(UserError) as caught:
            self.connector._validate_config()
        self.assertIn("0245", str(caught.exception))
        self.assertIn("IČO", str(caught.exception))

    # ------------------------------------------------------------------
    # Document type identifiers
    # ------------------------------------------------------------------

    def test_invoice_metadata(self):
        parsed = self.connector._epostak_parse_ubl(_invoice_ubl())
        self.assertEqual(parsed["doc_kind"], "Invoice")
        self.assertEqual(parsed["document_id"], "FA-2026-001")
        self.assertEqual(parsed["sender"], "0245:2121576435")
        self.assertEqual(parsed["receiver"], "0208:0987654321")
        self.assertEqual(parsed["process_id"], BIS3_PROFILE)
        self.assertEqual(
            parsed["document_type_id"],
            "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2::Invoice"
            "##" + BIS3_CUSTOMIZATION + "::2.1",
        )

    def test_credit_note_metadata(self):
        parsed = self.connector._epostak_parse_ubl(_invoice_ubl(kind="CreditNote"))
        self.assertEqual(
            parsed["document_type_id"],
            "urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2"
            "::CreditNote##" + BIS3_CUSTOMIZATION + "::2.1",
        )

    def test_application_response_uses_sender_receiver_party(self):
        """An Invoice Response addresses via SenderParty/ReceiverParty.

        We are the buyer here, so "sender" must be our company and not the
        supplier — reading only the AccountingSupplierParty path would leave
        the response unaddressed.
        """
        parsed = self.connector._epostak_parse_ubl(_application_response())
        self.assertEqual(parsed["doc_kind"], "ApplicationResponse")
        self.assertEqual(parsed["sender"], "0245:2121576435")
        self.assertEqual(parsed["receiver"], "0208:0987654321")
        self.assertEqual(
            parsed["document_type_id"],
            "urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2"
            "::ApplicationResponse##" + IR_CUSTOMIZATION + "::2.1",
        )

    def test_explicit_ubl_version_is_honoured(self):
        xml = _invoice_ubl().replace(
            "<cbc:CustomizationID>",
            "<cbc:UBLVersionID>2.2</cbc:UBLVersionID><cbc:CustomizationID>",
        )
        parsed = self.connector._epostak_parse_ubl(xml)
        self.assertTrue(parsed["document_type_id"].endswith("::2.2"))

    # ------------------------------------------------------------------
    # Rejections
    # ------------------------------------------------------------------

    def test_non_ubl_payloads_are_rejected(self):
        for payload in ("", "not xml at all", "<biztalk_1><header/></biztalk_1>"):
            self.assertFalse(
                self.connector._epostak_parse_ubl(payload),
                "payload %r must not yield Peppol metadata" % payload,
            )

    def test_missing_customization_id_is_rejected(self):
        """Without a CustomizationID there is no Peppol document type, so the
        network has nothing to route on — better caught here than as a 422."""
        xml = _invoice_ubl().replace(
            "<cbc:CustomizationID>%s</cbc:CustomizationID>" % BIS3_CUSTOMIZATION,
            "",
        )
        self.assertFalse(self.connector._epostak_parse_ubl(xml))

    def test_dtd_payload_is_refused(self):
        """Inbound XML is untrusted; a DTD is the entity-expansion vector."""
        xml = _invoice_ubl().replace(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
            '<?xml version="1.0"?><!DOCTYPE Invoice [<!ENTITY a "b">]>',
        )
        self.assertFalse(self.connector._epostak_parse_ubl(xml))

    def test_document_metadata_names_what_is_missing(self):
        """A misaddressed document is a configuration error on a partner
        record; the HTTP 422 would not say which half is wrong."""
        msg = self.env["edi.message"].create(
            {
                "name": "test.xml",
                "direction": "out",
                "provider": "epostak",
                "state": "ready",
            }
        )
        xml = _invoice_ubl().replace(
            '<cbc:EndpointID schemeID="0208">0987654321</cbc:EndpointID>', ""
        )
        with self.assertRaises(UserError) as ctx:
            self.connector._epostak_document_metadata(msg, xml)
        self.assertIn("receiver", str(ctx.exception))

        with self.assertRaises(UserError):
            self.connector._epostak_document_metadata(msg, "<nonsense/>")

    # ------------------------------------------------------------------
    # Provider registration
    # ------------------------------------------------------------------

    def test_provider_registered_and_mode_stamped(self):
        EdiMessage = self.env["edi.message"]
        # fields_get resolves the selection= method name into real values;
        # _fields[...].selection is just the method NAME here, not a callable.
        selection = dict(EdiMessage.fields_get(["provider"])["provider"]["selection"])
        self.assertIn("epostak", selection)
        # _register_hook runs at STEP 9 of load_modules — AFTER at-install
        # tests — so the maps are still empty at this point in the run.
        # Invoke it directly (it is idempotent) to test what it registers
        # rather than when the loader gets round to calling it.
        EdiMessage._register_hook()
        self.assertEqual(
            EdiMessage.PROVIDER_CONNECTOR_MAP.get("epostak"), "epostak.connector"
        )
        # The cron xmlid must resolve, or has_more would never re-trigger.
        self.assertTrue(
            self.env.ref(EdiMessage.PROVIDER_CRON_MAP["epostak"])
        )
        msg = EdiMessage.create(
            {
                "name": "mode.xml",
                "direction": "out",
                "provider": "epostak",
                "state": "ready",
            }
        )
        self.assertEqual(msg.provider_mode, self.connector._get_mode())
        self.assertEqual(msg.is_test_mode, msg.provider_mode == "sandbox")

    def test_send_does_not_need_a_job_runner(self):
        """A standalone cssk-public customer has no queue_job: edi_base does not
        depend on it, and the bridge edi_base_queue_job is proprietary and so is
        not in the public repo at all.

        ePošťák must therefore dispatch by cron. If this ever defaulted back to
        'queue', every invoice on such a database would sit in 'queued' for ever
        with nothing to pick it up, and nothing would raise.
        """
        EdiMessage = self.env["edi.message"]
        EdiMessage._register_hook()
        self.assertEqual(
            EdiMessage.PROVIDER_DISPATCH_MAP.get("epostak"),
            "cron",
            "epostak must not rely on the proprietary job bridge",
        )
        # And the cron that drains 'queued' has to exist, in edi_base, which IS
        # public. Registering the mode without it would be the same outage.
        self.assertTrue(
            self.env.ref("edi_base.cron_edi_send_queued", raise_if_not_found=False),
            "edi_base must ship the cron that sends queued messages",
        )
