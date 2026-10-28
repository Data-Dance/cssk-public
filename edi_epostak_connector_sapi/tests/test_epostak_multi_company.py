"""Several companies exchanging Peppol documents through ePošťák in one database.

The firm, the credentials and the inbound health used to be global, so one
account served one company per database: a second company's invoices went out
under the first company's credentials and firm, and its inbox was never
polled. HTTP is faked at the session; nothing leaves.
"""

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import requests

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

UBL = (
    '<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" '
    'xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" '
    'xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">'
    '<cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0</cbc:CustomizationID>'
    '<cbc:ProfileID>urn:fdc:peppol.eu:2017:poacc:billing:01:1.0</cbc:ProfileID>'
    '<cbc:ID>{doc_id}</cbc:ID><cbc:IssueDate>2026-10-20</cbc:IssueDate>'
    '<cac:AccountingSupplierParty><cac:Party><cbc:EndpointID schemeID="0245">{sender}</cbc:EndpointID></cac:Party></cac:AccountingSupplierParty>'
    '<cac:AccountingCustomerParty><cac:Party><cbc:EndpointID schemeID="0245">2021888888</cbc:EndpointID></cac:Party></cac:AccountingCustomerParty>'
    '</Invoice>'
)


def _response(status, body):
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(body).encode()
    response.encoding = "utf-8"
    return response


@tagged("post_install", "-at_install")
class TestEpostakMultiCompany(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param("epostak.mode", "sandbox")
        cls.connector = cls.env["epostak.connector"]
        cls.Message = cls.env["edi.message"]
        cls.alfa = cls._company("Alfa SK s.r.o.", "2020000001", "alfa-id", "")
        cls.beta = cls._company("Beta SK s.r.o.", "2020000002", "int-id", "beta-firm")
        # no credentials at all
        cls.gama = cls._company("Gama SK s.r.o.", "2020000003", "", "")

    @classmethod
    def _company(cls, name, dic, client_id, firm_id):
        company = cls.env["res.company"].create({"name": name})
        company.partner_id.write({"peppol_eas": "0245", "peppol_endpoint": dic})
        company.sudo().write({
            "epostak_sandbox_client_id": client_id or False,
            "epostak_sandbox_client_secret": ("sk_live_" + client_id) if client_id else False,
            "epostak_firm_id": firm_id or False,
        })
        return company

    # -- configuration ----------------------------------------------------

    def test_each_company_reads_its_own_credentials_and_firm(self):
        alfa = self.connector.with_company(self.alfa)._get_sapi_config()
        beta = self.connector.with_company(self.beta)._get_sapi_config()
        self.assertEqual((alfa["client_id"], alfa["firm_id"]), ("alfa-id", ""))
        self.assertEqual((beta["client_id"], beta["firm_id"]), ("int-id", "beta-firm"))
        self.assertEqual(beta["client_secret"], "sk_live_int-id")

    def test_a_company_without_credentials_holds_no_account(self):
        self.assertIsNone(self.connector.with_company(self.gama)._epostak_account_key())

    # -- polling ----------------------------------------------------------

    def _poll(self):
        polled = []

        def poll_inbound(connector):
            cfg = connector._get_sapi_config()
            polled.append((connector.env.company, cfg["client_id"], cfg["firm_id"],
                           connector._epostak_own_participant_id()))
            return {"messages": [], "has_more": False}

        with patch.object(type(self.connector), "_poll_inbound", poll_inbound):
            self.Message._poll_provider("epostak")
        return polled

    def test_each_mailbox_is_polled_as_its_company(self):
        polled = self._poll()
        self.assertIn((self.alfa, "alfa-id", "", "0245:2020000001"), polled)
        self.assertIn((self.beta, "int-id", "beta-firm", "0245:2020000002"), polled)
        self.assertNotIn(self.gama, [row[0] for row in polled])
        self.assertEqual(len(polled), len(set(polled)), "each mailbox once")

    def test_one_integrator_key_for_two_companies_is_two_mailboxes(self):
        """ePošťák scopes the inbox to the participant header: two companies
        under one key and firm still have two inboxes to collect."""
        self.alfa.sudo().write({
            "epostak_sandbox_client_id": "int-id",
            "epostak_sandbox_client_secret": "sk_live_int-id",
            "epostak_firm_id": "beta-firm",
        })
        participants = [row[3] for row in self._poll()]
        self.assertIn("0245:2020000001", participants)
        self.assertIn("0245:2020000002", participants)

    def test_inbound_health_is_kept_per_company(self):
        """One company's successful poll must not reset another's failure
        streak, nor close its activity."""
        alfa = self.connector.with_company(self.alfa)
        beta = self.connector.with_company(self.beta)
        ICP = self.env["ir.config_parameter"].sudo()
        alfa._record_poll(error="bad key")
        alfa._record_poll(error="bad key")
        beta._record_poll(count=2)
        self.assertEqual(ICP.get_param(alfa._poll_key(alfa.PARAM_POLL_STREAK)), "2")
        self.assertEqual(ICP.get_param(alfa._poll_key(alfa.PARAM_POLL_ERROR)), "bad key")
        self.assertEqual(ICP.get_param(beta._poll_key(beta.PARAM_POLL_STREAK)), "0")
        label = self.env["res.config.settings"].with_company(self.beta).create(
            {}).epostak_inbound_health
        self.assertIn("OK at", label)

    def test_the_poll_button_polls_the_selected_company_only(self):
        polled = []

        def poll_inbound(connector):
            polled.append(connector.env.company)
            return {"messages": [], "has_more": False}

        settings = self.env["res.config.settings"].with_company(self.beta).create({})
        self.assertEqual(settings.company_id, self.beta)
        with patch.object(type(self.connector), "_poll_inbound", poll_inbound):
            settings.action_epostak_poll_inbound()
        self.assertEqual(polled, [self.beta])

    # -- sending ----------------------------------------------------------

    def test_each_message_is_sent_with_its_company_credentials(self):
        messages = self.Message
        for company, dic in ((self.alfa, "2020000001"), (self.beta, "2020000002")):
            message = self.Message.create({
                "name": "%s.xml" % dic, "direction": "out", "provider": "epostak",
                "doc_family": "peppol", "state": "queued", "company_id": company.id,
            })
            message._store_xml(UBL.format(doc_id="INV-" + dic, sender=dic))
            messages |= message
        tokens, sends = [], []

        def send(session, request, **kwargs):
            if request.url.endswith("/auth/token"):
                client_id = json.loads(request.body)["client_id"]
                tokens.append(client_id)
                return _response(200, {"access_token": "tok-" + client_id,
                                       "expires_in": 900})
            sends.append((request.headers.get("Authorization"),
                          request.headers.get("X-Firm-Id"),
                          request.headers.get("X-Peppol-Participant-Id")))
            return _response(202, {"providerDocumentId": "P"})

        self.connector._clear_token_cache()
        with patch("requests.sessions.Session.send", send):
            self.connector._send_messages(messages)
        self.assertEqual(sorted(tokens), ["alfa-id", "int-id"])
        self.assertIn(("Bearer tok-alfa-id", None, "0245:2020000001"), sends)
        self.assertIn(("Bearer tok-int-id", "beta-firm", "0245:2020000002"), sends)
        self.assertEqual(set(messages.mapped("state")), {"sent"})

    # -- settings ---------------------------------------------------------

    def test_the_settings_page_edits_the_selected_company(self):
        settings = self.env["res.config.settings"].with_company(self.gama).create({
            "epostak_sapi_sandbox_client_id": "gama-id",
            "epostak_sapi_sandbox_client_secret": "sk_live_gama",
            "epostak_firm_id": "gama-firm",
        })
        settings.execute()
        self.assertEqual(self.gama.sudo().epostak_sandbox_client_id, "gama-id")
        self.assertEqual(self.gama.sudo().epostak_firm_id, "gama-firm")
        self.assertEqual(self.alfa.sudo().epostak_sandbox_client_id, "alfa-id")

    # -- migration --------------------------------------------------------

    def _migrate(self, module, version):
        path = (Path(__file__).parents[2] / module / "migrations" / version
                / "post-migrate.py")
        spec = importlib.util.spec_from_file_location(module + "_migration", path)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        migration.migrate(self.env.cr, "19.0.1.0.0")

    def test_the_migration_gives_the_collecting_company_the_global_account(self):
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("epostak.sapi.sandbox.client_id", "legacy-id")
        ICP.set_param("epostak.sapi.sandbox.client_secret", "sk_live_legacy")
        ICP.set_param("epostak.firm_id", "legacy-firm")
        ICP.set_param("epostak.inbound.last_ok", "2026-10-01 10:00:00")
        cron = self.env.ref("edi_epostak_base.cron_epostak_get_messages")
        collecting = cron.user_id.company_id
        collecting.sudo().write({
            "epostak_sandbox_client_id": False, "epostak_prod_client_id": False,
            "epostak_firm_id": False,
        })
        self._migrate("edi_epostak_base", "19.0.1.1.0")
        self._migrate("edi_epostak_connector_sapi", "19.0.1.2.0")
        collecting.invalidate_recordset()
        self.alfa.invalidate_recordset()
        self.assertEqual(collecting.sudo().epostak_sandbox_client_id, "legacy-id")
        self.assertEqual(collecting.sudo().epostak_sandbox_client_secret, "sk_live_legacy")
        self.assertEqual(collecting.sudo().epostak_firm_id, "legacy-firm")
        self.assertEqual(
            ICP.get_param("epostak.inbound.last_ok.%s" % collecting.id),
            "2026-10-01 10:00:00")
        self.assertEqual(self.alfa.sudo().epostak_sandbox_client_id, "alfa-id",
                         "another company is not given the old account")
