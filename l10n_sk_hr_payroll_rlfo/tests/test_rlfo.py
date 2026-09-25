# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runtime test — proves RLFO (RLZEC) generation + XSD validation. RLFO is
lifecycle-driven (no payslip), so it runs on a single engine: it only needs an
``hr.employee`` and a couple of registration events. The produced XML is
validated against the shipped ``RLZEC-v2026.xsd``."""
import base64
from datetime import date

from lxml import etree

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

    def test_no_events_raises(self):
        from odoo.exceptions import UserError
        rlfo = self.env["l10n.sk.rlfo"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026", "month": "3"})
        with self.assertRaises(UserError):
            rlfo.action_generate()

    # ------------------------------------------------------------------
    # typZec — the relationship code the Sociálna poisťovňa registers
    # ------------------------------------------------------------------
    def _employee_on(self, name, agreement_type, income_regular):
        """An employee whose version carries an agreement type and regularity.

        Skips rather than fails where the SK payroll engine is not installed:
        those fields live on hr.version in the payroll modules, and the RLFO
        is installable without them.
        """
        employee = self.env["hr.employee"].with_company(self.company).create({
            "name": name,
            "company_id": self.company.id,
            "identification_id": "9002022345",
            "birthday": date(1990, 2, 2),
        })
        version = employee.version_id
        if "l10n_sk_agreement_type" not in version._fields:
            self.skipTest("no SK payroll engine installed")
        vals = {"l10n_sk_agreement_type": agreement_type}
        if "l10n_sk_income_regular" in version._fields:
            vals["l10n_sk_income_regular"] = income_regular
        version.write(vals)
        return employee

    def test_typ_zec_follows_the_agreement_type(self):
        for agreement, expected in (
            ("none", "ZEC"), ("dovp", "ZECD1"), ("dopc", "ZECD2"),
        ):
            with self.subTest(agreement=agreement):
                emp = self._employee_on("Pravidelny", agreement, True)
                rlfo = self.env["l10n.sk.rlfo"].with_company(self.company).create(
                    {"company_id": self.company.id, "year": "2026", "month": "3"})
                ev = self.env["l10n.sk.rlfo.event"].create({
                    "rlfo_id": rlfo.id, "employee_id": emp.id,
                    "typ_rl": "PA", "date_start": date(2026, 3, 1)})
                self.assertEqual(ev.typ_zec, expected)

    def test_irregular_income_registers_the_N_variant(self):
        """A dohoda with IRREGULAR income is a different relationship to the
        Sociálna poisťovňa: old-age and disability only, no sickness, no
        unemployment, no short-time contribution.

        Until 2026-08-07 typ_zec keyed on the agreement type alone, so an
        irregular-income dohodár was registered as ZECD1/ZECD2 — the regular
        codes. ZECD1N and ZECD2N were declared in the selection and reachable
        by hand, but nothing ever produced them. That tells SP the wrong
        insurance scope from the day of registration, not merely on a payslip.
        """
        for agreement, expected in (("dovp", "ZECD1N"), ("dopc", "ZECD2N")):
            with self.subTest(agreement=agreement):
                emp = self._employee_on("Nepravidelny", agreement, False)
                if not emp.version_id.l10n_sk_income_regular is False:
                    self.skipTest("income regularity not modelled here")
                rlfo = self.env["l10n.sk.rlfo"].with_company(self.company).create(
                    {"company_id": self.company.id, "year": "2026", "month": "3"})
                ev = self.env["l10n.sk.rlfo.event"].create({
                    "rlfo_id": rlfo.id, "employee_id": emp.id,
                    "typ_rl": "PA", "date_start": date(2026, 3, 1)})
                self.assertEqual(ev.typ_zec, expected)
