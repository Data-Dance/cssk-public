"""An inbound Peppol document is a duplicate only of the same sender's same
document: a cbc:ID is an invoice number, unique per sender (cssk-public#8)."""

from unittest.mock import patch

from odoo.tests.common import TransactionCase

UBL = """<?xml version="1.0" encoding="UTF-8"?>
<{root} xmlns="urn:oasis:names:specification:ubl:schema:xsd:{root}-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0</cbc:CustomizationID>
  <cbc:ID>{doc_id}</cbc:ID>
  <cbc:IssueDate>2026-10-20</cbc:IssueDate>
  <cac:AccountingSupplierParty><cac:Party>
    <cbc:EndpointID schemeID="0245">{sender}</cbc:EndpointID>
  </cac:Party></cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty><cac:Party>
    <cbc:EndpointID schemeID="0245">{receiver}</cbc:EndpointID>
  </cac:Party></cac:AccountingCustomerParty>
</{root}>"""

SUPPLIER_A = "2020999999"
SUPPLIER_B = "2021888888"
US = "2022777777"
OTHER_COMPANY = "2023666666"


class TestPeppolInboundDedup(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Message = cls.env["edi.message"]
        # A made-up provider, registered the way a connector module does it:
        # this is about the poll, not about any one transport.
        cls.Message.PROVIDER_CONNECTOR_MAP["t_poll"] = "edi.connector.mixin"
        cls.addClassCleanup(
            cls.Message.PROVIDER_CONNECTOR_MAP.pop, "t_poll", None)

    @staticmethod
    def _doc(sender, doc_id, root="Invoice", receiver=US):
        return UBL.format(root=root, doc_id=doc_id, sender=sender, receiver=receiver)

    def _poll(self, *documents):
        """Poll ``documents`` (UBL strings) in one run; return the raw_ids
        acknowledged."""
        packages = [
            {"name": "doc-%d.xml" % n, "raw_id": "R%d" % n, "xml_content": xml}
            for n, xml in enumerate(documents, start=1)
        ]
        acked = []
        connector = type(self.env["edi.connector.mixin"])
        with patch.object(connector, "_poll_inbound",
                          lambda self_: {"messages": packages, "has_more": False},
                          create=True), \
                patch.object(type(self.Message), "_dispatch_ack",
                             lambda self_, conn, raw_id: acked.append(raw_id)), \
                patch.object(type(self.Message), "_inbound_dispatch_may_commit",
                             lambda self_: False), \
                patch.object(type(self.Message), "_lookup_related_records"):
            self.Message._poll_provider("t_poll")
        return acked

    def _stored(self, doc_id):
        return self.Message.search([
            ("provider", "=", "t_poll"), ("message_id", "=", doc_id)])

    def test_two_suppliers_invoices_with_one_number_are_both_kept(self):
        acked = self._poll(self._doc(SUPPLIER_A, "2026001"),
                           self._doc(SUPPLIER_B, "2026001"))
        self.assertEqual(
            sorted(self._stored("2026001").mapped("sender_gln")),
            sorted([SUPPLIER_A, SUPPLIER_B]),
            "an acknowledged package that was not stored is a deleted invoice")
        self.assertEqual(acked, ["R1", "R2"])

    def test_the_same_suppliers_invoice_twice_is_one_document(self):
        self._poll(self._doc(SUPPLIER_A, "2026001"))
        acked = self._poll(self._doc(SUPPLIER_A, "2026001"))
        self.assertEqual(len(self._stored("2026001")), 1)
        self.assertEqual(acked, ["R1"], "a duplicate is still acknowledged")

    def test_an_invoice_and_a_credit_note_may_share_a_number(self):
        self._poll(self._doc(SUPPLIER_A, "2026001", "Invoice"),
                   self._doc(SUPPLIER_A, "2026001", "CreditNote"))
        self.assertEqual(
            sorted(self._stored("2026001").mapped("message_type")),
            ["CreditNote", "Invoice"])

    def test_one_supplier_invoicing_two_of_our_companies(self):
        self._poll(self._doc(SUPPLIER_A, "2026001", receiver=US),
                   self._doc(SUPPLIER_A, "2026001", receiver=OTHER_COMPANY))
        self.assertEqual(len(self._stored("2026001")), 2)

    def test_a_document_without_a_sender_endpoint_is_kept(self):
        """Nothing to tell two senders apart by: store it rather than risk
        acknowledging a different supplier's document away."""
        no_sender = UBL.format(root="Invoice", doc_id="2026009", sender="",
                               receiver=US)
        self._poll(no_sender)
        acked = self._poll(no_sender)
        self.assertEqual(len(self._stored("2026009")), 2)
        self.assertEqual(acked, ["R1"])
