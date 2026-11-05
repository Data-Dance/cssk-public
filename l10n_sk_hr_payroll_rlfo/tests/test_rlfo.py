# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runtime test — proves RLFO (RLZEC) generation + XSD validation. RLFO is
lifecycle-driven (no payslip), so it runs on a single engine: it only needs an
``hr.employee`` and a couple of registration events. The produced XML is
validated against the shipped ``RLZEC-v2026.xsd``."""
import base64
from datetime import date
from unittest.mock import patch

from lxml import etree
from odoo.exceptions import UserError

from odoo.tests import TransactionCase, tagged
from odoo.tools import file_path

NS = {"r": "http://socpoist.sk/xsd/rlzec2026"}


@tagged("post_install", "-at_install")
class TestRlfo(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({
            "name": "SK RLFO Co",
            "country_id": cls.env.ref("base.sk").id,
            "company_registry": "12345678",
            "l10n_sk_sp_vs": "1234567890",
        })
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(context=dict(
            cls.env.context, allowed_company_ids=cls.company.ids))
        cls.employee = cls.env["hr.employee"].with_company(cls.company).create({
            "name": "Jozko Mrkvicka",
            "company_id": cls.company.id,
            "identification_id": "8501011234",
            "birthday": date(1985, 1, 1),
        })

    def _make_batch(self):
        rlfo = self.env["l10n.sk.rlfo"].with_company(self.company).create({
            "company_id": self.company.id,
            "year": "2026",
            "month": "3",
        })
        self.env["l10n.sk.rlfo.event"].create({
            "rlfo_id": rlfo.id,
            "employee_id": self.employee.id,
            "typ_rl": "PA",
            "typ_zec": "ZEC",
            "date_start": date(2026, 3, 1),
            "owner50_status": "no",
            "ownership_evidence": "Synthetic ordinary employee, no statutory membership",
        })
        self.env["l10n.sk.rlfo.event"].create({
            "rlfo_id": rlfo.id,
            "sequence": 20,
            "employee_id": self.employee.id,
            "typ_rl": "OD",
            "typ_zec": "ZEC",
            "date_start": date(2026, 3, 1),
            "date_end": date(2026, 3, 31),
        })
        return rlfo

    def test_generate_and_validate(self):
        rlfo = self._make_batch()
        self.assertTrue(rlfo.version_id, "RLFO version should default")
        rlfo.action_generate()
        self.assertEqual(rlfo.state, "generated")

        xml_bytes = base64.b64decode(rlfo.xml_attachment_id.datas)
        schema = etree.XMLSchema(etree.parse(
            file_path("l10n_sk_hr_payroll_rlfo/data/RLZEC-v2026.xsd")))
        root = etree.fromstring(xml_bytes)
        schema.assertValid(root)

        regs = root.findall(".//r:regListZec", NS)
        self.assertEqual(len(regs), 2)
        self.assertEqual(regs[0].get("typRL"), "PA")
        self.assertEqual(regs[1].get("typRL"), "OD")
        # PA carries the birth number and the insurance-start date.
        self.assertEqual(regs[0].find(".//r:identFO/r:rc", NS).text,
                         "8501011234")
        self.assertEqual(
            regs[0].find(".//r:zecPrihl/r:datVznikPoist", NS).text,
            "01.03.2026")
        self.assertEqual(regs[0].find(".//r:zecPrihl", NS).get("typZec"),
                         "ZEC")
        # OD carries the zanik with both start and end dates (zecPPOdhl branch).
        zanik = regs[1].find(".//r:zecPPOdhl/r:zanik", NS)
        self.assertEqual(zanik.get("datVzniku"), "01.03.2026")
        self.assertEqual(zanik.get("datZaniku"), "31.03.2026")

    def test_owner_render_context_is_respected(self):
        """A reviewed statutory owner must not become false in the XML."""
        rlfo = self._make_batch()
        original = type(rlfo)._declaration_render_context

        def reviewed_context(record, data):
            context = original(record, data)
            context["events"][0]["zam_s_ucastou"] = "true"
            return context

        with patch.object(type(rlfo), "_declaration_render_context",
                          reviewed_context):
            rlfo.action_generate()
        root = etree.fromstring(base64.b64decode(rlfo.xml_attachment_id.datas))
        self.assertEqual(root.find(".//r:zamSUcastou", NS).text, "true")

    def test_statutory_owner_registration(self):
        rlfo = self._make_batch()
        event = rlfo.event_ids.filtered(lambda ev: ev.typ_rl == "PA")
        event.write({"owner50_status": "yes",
                     "ownership_evidence": "Synthetic dated sole-owner decision"})
        rlfo.action_generate()
        root = etree.fromstring(base64.b64decode(rlfo.xml_attachment_id.datas))
        self.assertEqual(root.find(".//r:zamSUcastou", NS).text, "true")

    def test_ordinary_worker_registration(self):
        rlfo = self._make_batch()
        rlfo.action_generate()
        root = etree.fromstring(base64.b64decode(rlfo.xml_attachment_id.datas))
        self.assertEqual(root.find(".//r:zamSUcastou", NS).text, "false")

    def test_unknown_ownership_cannot_become_false(self):
        rlfo = self._make_batch()
        rlfo.event_ids.filtered(lambda ev: ev.typ_rl == "PA").owner50_status = "unknown"
        with self.assertRaises(UserError):
            rlfo.action_generate()
        self.assertEqual(rlfo.state, "draft")
        self.assertFalse(rlfo.xml_attachment_id)

    def test_missing_ownership_evidence_is_rejected(self):
        rlfo = self._make_batch()
        rlfo.event_ids.filtered(lambda ev: ev.typ_rl == "PA").ownership_evidence = " "
        with self.assertRaises(UserError):
            rlfo.action_generate()

    def test_generated_ownership_cannot_be_edited(self):
        rlfo = self._make_batch()
        rlfo.action_generate()
        with self.assertRaises(UserError):
            rlfo.event_ids.filtered(lambda ev: ev.typ_rl == "PA").owner50_status = "yes"

    def test_ownership_is_a_registration_fact(self):
        rlfo = self._make_batch()
        event = rlfo.event_ids.filtered(lambda ev: ev.typ_rl == "PA")
        event.owner50_status = "yes"
        # 18.0 keeps the payroll fields on hr.contract, not hr.version.
        contract = self.employee.contract_id
        if contract and "l10n_sk_guarantee_exempt" in contract._fields:
            contract.l10n_sk_guarantee_exempt = False
        rlfo.action_generate()
        root = etree.fromstring(base64.b64decode(rlfo.xml_attachment_id.datas))
        self.assertEqual(root.find(".//r:zamSUcastou", NS).text, "true")

    def test_no_events_raises(self):
        from odoo.exceptions import UserError
        rlfo = self.env["l10n.sk.rlfo"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026", "month": "3"})
        with self.assertRaises(UserError):
            rlfo.action_generate()

    def test_2027_api_period_selects_new_schema(self):
        rlfo = self._make_batch()
        rlfo.write({"year": "2027", "month": "1"})
        # Deliberately leave the older API default / explicit old vintage.
        rlfo.version_id = self.env.ref("l10n_sk_hr_payroll_rlfo.rlfo_version_2026")
        rlfo.action_generate()
        self.assertEqual(rlfo.version_id, self.env.ref(
            "l10n_sk_hr_payroll_rlfo.rlfo_version_2027"))
        root = etree.fromstring(base64.b64decode(rlfo.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).namespace,
                         "http://socpoist.sk/xsd/rlzec2027")
        schema = etree.XMLSchema(etree.parse(file_path(
            "l10n_sk_hr_payroll_rlfo/data/RLZEC-v2027.xsd")))
        schema.assertValid(root)

    def test_2026_api_period_keeps_old_schema(self):
        rlfo = self._make_batch()
        rlfo.version_id = self.env.ref("l10n_sk_hr_payroll_rlfo.rlfo_version_2027")
        rlfo.action_generate()
        self.assertEqual(rlfo.version_id, self.env.ref(
            "l10n_sk_hr_payroll_rlfo.rlfo_version_2026"))
        root = etree.fromstring(base64.b64decode(rlfo.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).namespace,
                         "http://socpoist.sk/xsd/rlzec2026")

    # ------------------------------------------------------------------
    # typZec — the relationship code the Sociálna poisťovňa registers
    # ------------------------------------------------------------------
    def _employee_on(self, name, agreement_type, income_regular):
        employee = self.env["hr.employee"].with_company(self.company).create({
            "name": name,
            "company_id": self.company.id,
            "identification_id": "9002022345",
            "birthday": date(1990, 2, 2),
        })
        calendar = self.env["resource.calendar"].create(
            {"name": "SK 40h", "company_id": self.company.id})
        contract = self.env["hr.contract"].create({
            "name": "C " + name,
            "employee_id": employee.id,
            "resource_calendar_id": calendar.id,
            "wage": 1000.0,
            "date_start": date(2026, 1, 1),
            "state": "open",
        })
        if "l10n_sk_agreement_type" not in contract._fields:
            self.skipTest("no SK payroll engine installed")
        vals = {"l10n_sk_agreement_type": agreement_type}
        if "l10n_sk_income_regular" in contract._fields:
            vals["l10n_sk_income_regular"] = income_regular
        contract.write(vals)
        return employee

    def _event_for(self, employee):
        rlfo = self.env["l10n.sk.rlfo"].with_company(self.company).create(
            {"company_id": self.company.id, "year": "2026", "month": "3"})
        return self.env["l10n.sk.rlfo.event"].create({
            "rlfo_id": rlfo.id, "employee_id": employee.id,
            "typ_rl": "PA", "date_start": date(2026, 3, 1)})

    def test_typ_zec_follows_the_agreement_type(self):
        for agreement, expected in (
            ("none", "ZEC"), ("dovp", "ZECD1"), ("dopc", "ZECD2"),
        ):
            with self.subTest(agreement=agreement):
                emp = self._employee_on("Pravidelny", agreement, True)
                self.assertEqual(self._event_for(emp).typ_zec, expected)

    def test_irregular_income_registers_the_N_variant(self):
        """A dohoda with IRREGULAR income is a different relationship to the
        Sociálna poisťovňa: old-age and disability only. typ_zec used to key
        on the agreement type alone, so ZECD1N and ZECD2N were declared in the
        selection and reachable only by typing them in."""
        for agreement, expected in (("dovp", "ZECD1N"), ("dopc", "ZECD2N")):
            with self.subTest(agreement=agreement):
                emp = self._employee_on("Nepravidelny", agreement, False)
                self.assertEqual(self._event_for(emp).typ_zec, expected)
