# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import hashlib
from copy import deepcopy

from lxml import etree
from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged

MODEL = "l10n.sk.health.registration"


@tagged("post_install", "-at_install")
class TestHealthRegistration(TransactionCase):
    def test_forged_attachment_checksum_does_not_authorize_content_replacement(self):
        batch = self.batch()
        batch.action_generate()
        attachment = batch.xml_attachment_id
        original = attachment.raw
        tampered = b"synthetic changed filing"
        attachment.write({"checksum": hashlib.sha1(tampered).hexdigest()})
        # Stock ir.attachment.write discards this computed-field override.
        self.assertEqual(attachment.checksum, hashlib.sha1(original).hexdigest())
        with self.assertRaises(UserError):
            attachment.write({"raw": tampered})
        self.assertEqual(attachment.raw, original)

    def test_dated_exemption_blocks_start_but_allows_end_and_cancellation(self):
        if "l10n_sk_health_exempt" not in self.env["hr.version"]._fields:
            self.skipTest("Optional country payroll eligibility is not installed")
        version = self.employee.version_id
        version.write({"date_version": "2026-01-01", "l10n_sk_health_exempt": False})
        version.copy({"date_version": "2026-07-01", "l10n_sk_health_exempt": True})
        historical = self.batch()
        historical.with_user(self.manager).action_generate()
        current = self.batch(
            batch_sequence=2,
            month="7",
            event_ids=[Command.create(self.event_values(changed_on="2026-07-01"))],
        )
        with self.assertRaisesRegex(UserError, "health-exempt"):
            current.with_user(self.manager).action_generate()
        # A change of status can legally require termination on that date.
        current.event_ids.validity = "K"
        current.with_user(self.manager).action_generate()
        current.action_reset_to_draft()
        current.event_ids.validity = "X"
        current.with_user(self.manager).action_generate()

    def test_identity_prefill_reuses_the_common_name_adapter_without_attesting_notice_duty(
        self,
    ):
        self.employee.identification_id = "005101/123"
        event = self.env["l10n.sk.health.registration.event"].new(
            {
                "batch_id": self.batch(event_ids=[]).id,
                "employee_id": self.employee.id,
            }
        )
        event._onchange_employee_identity()
        self.assertEqual(
            (event.first_name, event.last_name, event.birth_number),
            ("Žofia", "Šťastná", "005101123"),
        )
        self.assertFalse(event.employer_notice_reviewed)
        self.assertFalse(event.insurer_identifier)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Syntetická601 spoločnosť",
                "country_id": cls.env.ref("base.sk").id,
                "company_registry": "36000001",
                "street": "Testovacia1",
                "city": "Bratislava",
                "zip": "85110",
            }
        )
        cls.bank = cls.env["res.partner.bank"].create(
            {
                "partner_id": cls.company.partner_id.id,
                "acc_number": "SK3112000000198742637541",
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Žofia Šťastná", "company_id": cls.company.id}
        )
        cls.manager = cls.env["res.users"].create(
            {
                "name": "Synthetic601 HR manager",
                "login": "synthetic601-manager",
                "company_id": cls.company.id,
                "company_ids": [Command.set(cls.company.ids)],
                "group_ids": [Command.set(cls.env.ref("hr.group_hr_manager").ids)],
            }
        )

    def event_values(self, **changes):
        values = {
            "employee_id": self.employee.id,
            "first_name": "Žofia",
            "last_name": "Šťastná",
            "birth_number": "005101123",
            "code": "2D",
            "validity": "Z",
            "changed_on": "2026-06-02",
            "source_reference": "Synthetic reviewed agreement and actual work day",
            "employer_notice_reviewed": True,
        }
        values.update(changes)
        return values

    def batch(self, **changes):
        values = {
            "company_id": self.company.id,
            "year": "2026",
            "month": "6",
            "sending_date": "2026-07-01",
            "insurer_code": "25",
            "receiver_ico": "12345678",
            "payer_number": "9900112233",
            "batch_sequence": 1,
            "payment_bank_id": self.bank.id,
            "phone": "+421900000000",
            "responsible_person": "Syntetická osoba",
            "event_ids": [
                Command.create(self.event_values()),
                Command.create(self.event_values(validity="K")),
            ],
        }
        values.update(changes)
        return self.env[MODEL].with_company(self.company).create(values)

    def test_hr_event_workflow_uses_registration_sources(self):
        batch = self.batch().with_user(self.manager)
        batch.action_generate()
        self.assertNotIn("payslips", batch.source_snapshot)
        self.assertEqual(batch.state, "generated")
        attachment = batch.xml_attachment_id
        self.assertEqual((attachment.res_model, attachment.res_id), (MODEL, batch.id))
        self.assertEqual(attachment.name, "36000001260701.xml")
        root = etree.fromstring(base64.b64decode(attachment.datas))
        self.assertEqual(root.xpath("PersonData/ValidationOfChange/text()"), ["Z", "K"])
        self.assertEqual(len(batch.source_snapshot["sources"]), 2)
        batch.action_submit()
        self.assertEqual(batch.submitted_attachment_id, attachment)
        self.assertEqual(batch.source_history[0]["attachment_id"], attachment.id)
        self.assertTrue(batch.submission_ids)
        self.assertTrue(all(row.state == "draft" for row in batch.submission_ids))

    def test_reset_and_correction_keep_exact_original_file_and_source_history(self):
        original = self.batch()
        original.action_generate()
        original.action_submit()
        attachment, history = (
            original.submitted_attachment_id,
            deepcopy(original.source_history),
        )
        content = attachment.datas
        original.action_reset_to_draft()
        original.event_ids[0].source_reference = "Later reviewed correction source"
        original.action_generate()
        original.action_submit()
        self.assertEqual(attachment.datas, content)
        self.assertEqual(original.source_history[:1], history)
        self.assertEqual(len(original.source_history), 2)
        correction = self.batch(correction_type="corrective", amends_id=original.id)
        correction.action_generate()
        root = etree.fromstring(base64.b64decode(correction.xml_attachment_id.datas))
        self.assertEqual(root.findtext("Identification/PatternOfBatch"), "O")
        self.assertEqual(attachment.datas, content)

    def test_missing_original_and_wrong_company_bank_are_rejected(self):
        correction = self.batch(correction_type="corrective")
        with self.assertRaises(UserError):
            correction.action_generate()
        other = self.env["res.partner"].create(
            {"name": "Other synthetic account owner"}
        )
        bank = self.bank.copy({"partner_id": other.id})
        original = self.batch(payment_bank_id=bank.id)
        with self.assertRaises(UserError):
            original.action_generate()

    def test_protected_workflow_fields_reject_api_values_and_defaults(self):
        for key, value in [
            ("state", "submitted"),
            ("source_snapshot", {}),
            ("source_history", []),
            ("submitted_date", "2026-07-01 00:00:00"),
            ("xml_attachment_id", False),
        ]:
            with self.assertRaises(UserError):
                self.batch(**{key: value})
            with self.assertRaises(UserError):
                self.env[MODEL].with_context(**{"default_" + key: value}).create({})
        batch = self.batch()
        with self.assertRaises(UserError):
            batch.write({"state": "generated"})

    def test_generated_inputs_nested_children_and_archived_file_are_protected(self):
        batch = self.batch()
        batch.action_generate()
        for operation in [
            lambda: batch.write({"phone": "+421900000001"}),
            lambda: batch.event_ids[0].write({"changed_on": "2026-06-03"}),
            lambda: batch.event_ids[0].unlink(),
            lambda: self.env["l10n.sk.health.registration.event"]
            .with_context(default_batch_id=batch.id)
            .create(self.event_values()),
            lambda: batch.xml_attachment_id.write(
                {"datas": base64.b64encode(b"changed")}
            ),
        ]:
            with self.assertRaises(UserError):
                operation()
        batch.action_submit()
        batch.action_reset_to_draft()
        with self.assertRaises(UserError):
            batch.submitted_attachment_id.unlink()
        with self.assertRaises(UserError):
            batch.unlink()

    def test_archive_allows_identical_content_storage_and_unrelated_chatter(self):
        batch = self.batch()
        batch.action_generate()
        attachment = batch.xml_attachment_id
        original = attachment.raw
        attachment.write({"raw": original})
        attachment.write({"datas": base64.b64encode(original)})
        attachment.write({"access_token": "synthetic-token"})
        with self.assertRaises(UserError):
            attachment.write({"store_fname": "incorrect-storage-location"})
        chatter = self.env["ir.attachment"].create(
            {
                "name": "Unrelated synthetic note.txt",
                "raw": b"note",
                "res_model": MODEL,
                "res_id": batch.id,
            }
        )
        chatter.write({"raw": b"updated note"})
        chatter.unlink()
        batch.action_submit()
        # The real migration method rewrites identical raw bytes.
        attachment._migrate()
        self.assertEqual(attachment.raw, original)

    def test_changed_payer_source_requires_regeneration_but_preserves_old_filing(self):
        batch = self.batch()
        batch.action_generate()
        previous = batch.xml_attachment_id
        content = previous.raw
        self.company.street = "Changed synthetic address2"
        with self.assertRaisesRegex(UserError, "source changed"):
            batch.action_submit()
        batch.action_reset_to_draft()
        batch.action_generate()
        batch.action_submit()
        filed, filed_content = (
            batch.submitted_attachment_id,
            batch.submitted_attachment_id.raw,
        )
        self.company.street = "Another later address3"
        self.assertEqual(previous.raw, content)
        self.assertEqual(filed.raw, filed_content)

    def test_original_retry_keeps_wire_identity_and_non_vat_payer_dic(self):
        self.company.l10n_sk_dic = "2020000000"
        batch = self.batch()
        batch.action_generate()
        self.assertEqual(batch.source_snapshot["payer"]["tax_id"], "2020000000")
        batch.action_submit()
        batch.action_reset_to_draft()
        batch.event_ids[0].changed_on = "2026-06-03"
        with self.assertRaisesRegex(UserError, "filed original"):
            batch.action_generate()
        correction = self.batch(correction_type="corrective", amends_id=batch.id)
        # The original's state is restored by a same-content retry, not by
        # forging generated state. Then a genuinely new O carries the change.
        batch.event_ids[0].changed_on = "2026-06-02"
        batch.action_generate()
        batch.action_submit()
        correction.event_ids[0].changed_on = "2026-06-03"
        correction.action_generate()

    def test_cross_company_children_and_bank_inputs_are_not_relabelled(self):
        other = self.env["res.company"].create(
            {
                "name": "Foreign synthetic601 company",
                "country_id": self.env.ref("base.sk").id,
            }
        )
        foreign = self.env["hr.employee"].create(
            {"name": "Foreign employee", "company_id": other.id}
        )
        with self.assertRaises(UserError), self.env.cr.savepoint():
            self.batch(
                event_ids=[Command.create(self.event_values(employee_id=foreign.id))]
            )
        batch = self.batch()
        with self.assertRaises(UserError), self.env.cr.savepoint():
            batch.company_id = other
        with self.assertRaises(AccessError):
            batch.with_user(self.manager).with_context(
                allowed_company_ids=[other.id]
            ).action_generate()

    def test_text601_is_latin2_and_2s_has_an_explicit_supported_workaround(self):
        batch = self.batch(event_ids=[Command.create(self.event_values(code="2S"))])
        with self.assertRaises(UserError):
            batch.action_generate()
        self.assertEqual(batch.state, "draft")
        self.assertFalse(batch.source_snapshot)
        self.assertFalse(batch.xml_attachment_id)
        batch.export_format = "text"
        batch.action_generate()
        self.assertEqual(batch.xml_attachment_id.name, "36000001260701.601")
        content = base64.b64decode(batch.xml_attachment_id.datas)
        self.assertIn("Žofia", content.decode("iso8859-2"))
        self.assertIn(b"|2S|Z|20260602|", content)

    def test_reviewed_calendar_scope_and_late_historical_notice_use_sending_vintage(
        self,
    ):
        calendar = self.env["l10n.sk.health.calendar"].create(
            {
                "company_id": self.company.id,
                "employee_id": self.employee.id,
                "month": "2025-06-01",
                "complete": True,
                "evidence": "Synthetic historical reviewed day source",
                "interval_ids": [
                    Command.create(
                        {
                            "kind": "2D",
                            "date_start": "2025-06-02",
                            "date_end": "2025-06-02",
                        }
                    )
                ],
            }
        )
        batch = self.batch(
            year="2025",
            event_ids=[
                Command.create(
                    self.event_values(
                        changed_on="2025-06-02",
                        source_calendar_id=calendar.id,
                    )
                )
            ],
        )
        with self.assertRaises(UserError):
            batch.action_generate()
        calendar.action_review()
        batch.action_generate()
        self.assertEqual(
            batch.version_id,
            self.env.ref(
                "l10n_sk_hr_payroll_health_registration.registration_version_2026"
            ),
        )
        root = etree.fromstring(base64.b64decode(batch.xml_attachment_id.datas))
        self.assertEqual(root.findtext("CorporateBody/YearOfChange"), "25")
        self.assertEqual(root.findtext("PersonData/DateOfChange"), "20250602")

    def test_notice_obligation_is_reviewed_separately_from_coverage(self):
        batch = self.batch(
            event_ids=[
                Command.create(self.event_values(employer_notice_reviewed=False))
            ]
        )
        with self.assertRaises(UserError):
            batch.action_generate()
        self.assertFalse(batch.xml_attachment_id)

    def test_calendar_endpoints_use_unioned_runs_not_internal_interval_edges(self):
        calendar = self.env["l10n.sk.health.calendar"].create(
            {
                "company_id": self.company.id,
                "employee_id": self.employee.id,
                "month": "2026-06-01",
                "complete": True,
                "evidence": "Synthetic reviewed work/rest run",
                "interval_ids": [
                    Command.create({"kind": "2D", "date_start": start, "date_end": end})
                    for start, end in [
                        ("2026-06-02", "2026-06-04"),
                        ("2026-06-04", "2026-06-06"),
                    ]
                ],
            }
        )
        calendar.action_review()
        batch = self.batch(
            event_ids=[
                Command.create(
                    self.event_values(
                        source_calendar_id=calendar.id,
                        changed_on="2026-06-04",
                    )
                )
            ]
        )
        with self.assertRaises(UserError):
            batch.action_generate()
        batch.event_ids.changed_on = "2026-06-02"
        batch.action_generate()

    def test_same_employer_employment_suppresses_concurrent_2d_notice(self):
        calendar = self.env["l10n.sk.health.calendar"].create(
            {
                "company_id": self.company.id,
                "employee_id": self.employee.id,
                "month": "2026-06-01",
                "complete": True,
                "evidence": "Synthetic employment and additional agreement",
                "interval_ids": [
                    Command.create({"kind": kind, "date_start": start, "date_end": end})
                    for kind, start, end in [
                        ("2", "2026-06-01", "2026-06-30"),
                        ("2D", "2026-06-02", "2026-06-02"),
                    ]
                ],
            }
        )
        calendar.action_review()
        batch = self.batch(
            event_ids=[
                Command.create(self.event_values(source_calendar_id=calendar.id))
            ]
        )
        with self.assertRaises(UserError):
            batch.action_generate()
