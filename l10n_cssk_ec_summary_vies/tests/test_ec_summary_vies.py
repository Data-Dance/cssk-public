import base64
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestEcSummaryVies(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # A VALID SK DIČ: ten digits divisible by 11, which is what
        # base_vat.check_vat_sk enforces. SK2022334455 leaves remainder 9, so
        # this assignment raised in setUpClass and took the WHOLE class with
        # it — the suite reported "0 tests" rather than a failure, so nothing
        # here had run since the check was added.
        cls.env.company.vat = "SK2022334446"
        cls.env.company.vies_use_direct = True
        template = cls.env["ir.ui.view"].create({
            "name": "test sv template", "type": "qweb",
            "key": "l10n_cssk_ec_summary_vies.test_sv_template",
            "arch": '<t t-name="l10n_cssk_ec_summary_vies.test_sv_template">'
                    "<SDV/></t>",
        })
        # A schema is not optional on this path any more: export refuses a
        # version it cannot validate against, because a KV DPH once exported
        # unvalidated and looked like it had passed. This suite is about how
        # many times VIES is consulted, not about the SV structure, so it
        # brings the smallest schema that accepts its own toy document rather
        # than the real svdph20.xsd — which the <SDV/> template would fail.
        schema = (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">'
            b'<xsd:element name="SDV"/>'
            b"</xsd:schema>"
        )
        version = cls.env["cssk.ec.summary.statement.version"].create({
            "name": "T", "country_id": cls.env.ref("base.sk").id,
            "valid_from": "2025-01-01",
            "xml_template_ref_id": template.id,
            "xml_root_element": "SDV",
            "xml_schema_filename": "test_sdv.xsd",
            "xml_schema_data": base64.b64encode(schema),
        })
        st_type = cls.env["cssk.ec.summary.statement.type"].create({
            "version_id": version.id, "code": "R", "name": "Riadny",
            "fa_xml_value": "R",
        })
        cls.statement = cls.env["cssk.ec.summary.statement"].create({
            "company_id": cls.env.company.id, "version_id": version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month", "statement_type_id": st_type.id,
        })
        cls.line = cls.env["cssk.ec.summary.statement.line"].create({
            "statement_id": cls.statement.id, "partner_country_code": "SK",
            "partner_vat": "SK2023456787", "transaction_code": "0",
        })

    def _patch_vies(self, result):
        # NB: patch with ``new=`` (a plain function), NEVER a MagicMock — the
        # registry's lazy ``_ondelete_methods`` scan collects every class
        # attribute that *has* an ``_ondelete`` attribute, and a MagicMock
        # auto-creates one on ``getattr``, so it would be cached as an unlink
        # hook (here on res.partner!) and poison unrelated tests.
        def fake_query(model, vat, requester_vat=None, trader_name=None):
            fake_query.call_count += 1
            return result
        fake_query.call_count = 0
        return patch.object(
            type(self.env["res.partner"]), "_vies_query_direct",
            new=fake_query,
        )

    def test_valid_snapshots_consultation_number(self):
        with self._patch_vies({"valid": True, "requestIdentifier": "ABC123"}):
            self.statement._check_vies()
        self.assertTrue(self.line.vies_valid)
        self.assertEqual(self.line.vies_consultation_number, "ABC123")
        self.assertTrue(self.line.vies_check_date)

    def test_invalid_blocks_export(self):
        with self._patch_vies({"valid": False}):
            with self.assertRaises(UserError):
                self.statement._check_vies()
        # Snapshot still records the negative result.
        self.assertFalse(self.line.vies_valid)

    def test_service_fault_does_not_block(self):
        with self._patch_vies(None):
            # No raise — a transient VIES outage must not block filing.
            self.statement._check_vies()
        self.assertTrue(self.line.vies_check_date)
        self.assertFalse(self.line.vies_consultation_number)

    # ------------------------------------------------------------------
    # Export flow: proofs must persist even when the export is blocked
    # ------------------------------------------------------------------

    def test_export_blocked_without_losing_proofs(self):
        """An invalid line hard-blocks the export, but WITHOUT an exception
        that would roll back the consultation numbers (legal proof) already
        obtained for the valid lines."""
        bad_line = self.env["cssk.ec.summary.statement.line"].create({
            "statement_id": self.statement.id, "partner_country_code": "CZ",
            "partner_vat": "CZ25663585", "transaction_code": "0",
        })
        self.statement.state = "preview"

        def fake_query(model, vat, requester_vat=None, trader_name=None):
            if vat == "SK2023456787":
                return {"valid": True, "requestIdentifier": "PROOF1"}
            return {"valid": False}

        with patch.object(
            type(self.env["res.partner"]), "_vies_query_direct",
            new=fake_query,
        ):
            action = self.statement.action_export_xml()

        # Blocked via a notification, not a raise.
        self.assertEqual(action.get("tag"), "display_notification")
        self.assertEqual(action["params"]["type"], "danger")
        self.assertNotEqual(self.statement.state, "exported")
        self.assertTrue(self.statement.vies_blocked)
        # The valid line's proof was obtained and kept.
        self.assertEqual(self.line.vies_consultation_number, "PROOF1")
        self.assertEqual(self.line.vies_status, "valid")
        self.assertTrue(self.line.vies_valid)
        # The invalid line is clearly marked.
        self.assertEqual(bad_line.vies_status, "invalid")
        self.assertFalse(bad_line.vies_valid)

    def test_export_queries_vies_once_per_line(self):
        """The export must not re-query VIES a second time after the
        proof-fetch step (the base export gate reuses the stored results)."""
        self.statement.state = "preview"
        with self._patch_vies(
            {"valid": True, "requestIdentifier": "ONCE"}
        ) as mock_query:
            self.statement.action_export_xml()
        self.assertEqual(mock_query.call_count, len(self.statement.line_ids))
        self.assertEqual(self.line.vies_consultation_number, "ONCE")
        # All valid → the export itself completed normally.
        self.assertEqual(self.statement.state, "exported")
        self.assertFalse(self.statement.vies_blocked)

    def test_disabled_skips_direct_check(self):
        self.env.company.vies_use_direct = False

        # If direct VIES is off, _vies_query_direct must never be called.
        def never_called(model, *args, **kwargs):
            raise AssertionError("should not be called")

        with patch.object(
            type(self.env["res.partner"]), "_vies_query_direct",
            new=never_called,
        ):
            self.statement._check_vies()
