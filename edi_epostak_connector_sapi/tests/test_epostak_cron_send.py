"""A cron run sends each queued document on its own (cssk-public#6).

The connector's failure bookkeeping was written for a job: it rolls the cursor
back and records the outcome on a second one. Under the cron that cursor is
the run's own, so one failure undid every document already sent and parked a
retryable failure in ``error``. HTTP is faked at the session; nothing leaves.

A test cursor cannot show the damage itself: its rollback and its "separate"
cursor both stay inside the test's own transaction. So the invariant is pinned
where it lives — under the cron the connector never takes the out-of-job path
that rolls back — and the outcome is checked as the cron records it.
"""

import json
from unittest.mock import patch

import requests

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

US = "2020999999"
CUSTOMER = "2021888888"

UBL = (
    '<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" '
    'xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" '
    'xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">'
    '<cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0</cbc:CustomizationID>'
    '<cbc:ProfileID>urn:fdc:peppol.eu:2017:poacc:billing:01:1.0</cbc:ProfileID>'
    '<cbc:ID>{doc_id}</cbc:ID><cbc:IssueDate>2026-10-20</cbc:IssueDate>'
    '<cac:AccountingSupplierParty><cac:Party><cbc:EndpointID schemeID="0245">' + US + '</cbc:EndpointID></cac:Party></cac:AccountingSupplierParty>'
    '<cac:AccountingCustomerParty><cac:Party><cbc:EndpointID schemeID="0245">' + CUSTOMER + '</cbc:EndpointID></cac:Party></cac:AccountingCustomerParty>'
    '</Invoice>'
)


def _response(status, body):
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(body).encode()
    response.encoding = "utf-8"
    return response


ACCEPTED = (202, {"providerDocumentId": "P"})
UNAVAILABLE = (503, {"error": {"code": "UNAVAILABLE", "message": "try later",
                               "retryable": True}})
REJECTED = (422, {"error": {"code": "SAPI-DOC-001", "message": "malformed",
                            "retryable": False}})


# post_install: ePošťák registers itself for cron dispatch in _register_hook,
# which runs after the at-install tests.
@tagged("post_install", "-at_install")
class TestEpostakCronSend(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        icp = cls.env["ir.config_parameter"].sudo()
        icp.set_param("epostak.mode", "sandbox")
        icp.set_param("epostak.sapi.sandbox.client_id", "c1")
        icp.set_param("epostak.sapi.sandbox.client_secret", "fake")
        cls.env.company.partner_id.write(
            {"peppol_eas": "0245", "peppol_endpoint": US})

    def _queued(self, count):
        messages = self.env["edi.message"]
        for n in range(1, count + 1):
            message = self.env["edi.message"].create({
                "name": "DOC%d.xml" % n, "direction": "out",
                "provider": "epostak", "doc_family": "peppol",
                "state": "queued", "company_id": self.env.company.id,
            })
            message._store_xml(UBL.format(doc_id="DOC%d" % n))
            messages |= message
        return messages

    def _send(self, answers, call):
        """Run ``call`` against faked HTTP ``answers``; return the messages
        whose failure was written outside the transaction (the job path)."""
        answers = list(answers)
        stamped = []

        def send(session, request, **kwargs):
            if request.url.split("?")[0].endswith("/auth/token"):
                return _response(200, {"access_token": "t", "expires_in": 900})
            return _response(*answers.pop(0))

        def write_outside_job(message, vals, rollback_first=True):
            stamped.append(message.name)
            return True

        with patch("requests.sessions.Session.send", send), \
                patch.object(type(self.env["edi.message"]), "_write_outside_job",
                             write_outside_job):
            call()
        self.assertFalse(answers, "every document was attempted")
        return stamped

    def _run_cron(self, *answers):
        stamped = self._send(answers, self.env["edi.message"]._cron_send_queued)
        self.assertFalse(
            stamped, "under the cron, the job-path stamp rolls back the run itself")

    def test_a_transient_failure_neither_undoes_nor_blocks_the_rest(self):
        first, second, third = self._queued(3)
        self._run_cron(ACCEPTED, UNAVAILABLE, ACCEPTED)
        self.assertEqual(first.state, "sent", "accepted, so it must not go out again")
        self.assertEqual(second.state, "queued", "a 503 is tried again next run")
        self.assertEqual(second.blocking_level, "warning")
        self.assertIn("503", second.error_message)
        self.assertEqual(third.state, "sent")

    def test_a_permanent_failure_is_parked_alone(self):
        first, second, third = self._queued(3)
        self._run_cron(ACCEPTED, REJECTED, ACCEPTED)
        self.assertEqual(
            (first.state, second.state, third.state), ("sent", "error", "sent"))
        self.assertIn("malformed", second.error_message)

    def test_a_job_still_records_its_failure_outside_the_transaction(self):
        """The job path is unchanged: its runner rolls the cursor back around
        the raise, so the failure must be written where that cannot reach."""
        from odoo.addons.edi_base.exceptions import RetryableJobError

        (message,) = self._queued(1)
        connector = self.env["epostak.connector"]

        def call():
            with self.assertRaises(RetryableJobError):
                connector._send_message(message)

        self.assertEqual(self._send([UNAVAILABLE], call), ["DOC1.xml"])

